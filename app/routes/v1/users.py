from flask import Flask, jsonify, render_template, url_for, request, redirect, json, make_response
from datetime import datetime, timedelta


import pymysql, os, math, requests, uuid, traceback


# File imports
from routes.v1 import app
from routes.v1 import db
from routes.v1 import bcrypt
from routes.v1 import cache, clearCache, require_api_token

from models import User, Usertype, Token, FeatureRole

def close(self):
    self.session.close()


@app.route('/user/single')
# @cache.cached(timeout=86400)
# @require_api_token
def getUsers():
    # get the auth token
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            auth_token = auth_header.split(" ")[1]
        except IndexError:
            responseObject = {
                'status': 'fail',
                'message': 'Bearer token malformed.'
            }
            return make_response(jsonify(responseObject)), 401
    else:
        auth_token = ''
    if auth_token:
        resp = User.decode_auth_token(auth_token)
        # if not isinstance(resp, str):
        user = db.session.query(User).filter_by(public_id=resp, status=5).first()
        if not user:
            return jsonify({'message' : 'No such user can be found'}), 422

        user_type = db.session.query(Usertype.name).filter_by(public_id=user.user_type).first()
        first_name, =  db.session.query(User.first_name).filter_by(public_id=user.session_id).first()
        last_name, =  db.session.query(User.last_name).filter_by(public_id=user.session_id).first()
        registered_by = first_name + " " + last_name

        output = []
        response = {}
        response['public_id'] = user.public_id
        response['full_name'] = user.first_name.strip().title() + " " + user.last_name.strip().title()
        response['phone_number'] = user.phone_number
        response['email'] = user.email
        response['user_type_public_id'] = user.user_type
        response['user_type'] = user_type[0]
        response['registered_by'] = registered_by 
        response['registered_on'] = user.created_at
        response['active_status'] = 'Suspended' if int(user.status) == 15 else 'Active'

        output.append(response)

        ## fetch menu data

        responseObject = {
            'status': 'success',
            'data' : output
        }
        return make_response(jsonify(responseObject)), 200
    else:
        responseObject = {
            'status': 'fail',
            'message': 'Provide a valid auth token.'
        }
        return make_response(jsonify(responseObject)), 401

@app.route('/user/<public_id>')
@cache.cached(timeout=86400)
# @require_api_token
def getUserbyID(public_id):
    user = db.session.query(User).filter_by(public_id=public_id).first()

    if not user:
        responseObject = {
            'message' : 'No such User Found'
        }
        return make_response(jsonify(responseObject)), 412
    else:
        user_type, = db.session.query(Usertype.name).filter_by(public_id=user.user_type).first()
        registered_by = db.session.query(User).filter_by(public_id=user.session_id).first()
        responseObject = {
            'first_name' : user.first_name,
            'last_name' : user.last_name,
            'phone_number' : user.phone_number,
            'email' : user.email,
            'registered_by' : registered_by.first_name + " " + registered_by.first_name if registered_by else "",
            'user_type_public_id' : user.user_type,
            'user_type' : user_type,
			'registered_on' : user.created_at,
            'active_status' : 'Suspended' if int(user.status) == 15 else 'Active'
        }
        return make_response(jsonify(responseObject)), 200

@app.route('/users/array', methods=['POST'])
# @require_api_token
def arraryofUsers():
    user_id = request.json['users_ids']

    if 'users_ids' not in request.json:
        responseObject = {
            'message' : '["users_ids"] is not sent'
        }
        return make_response(jsonify(responseObject)), 412

    num_users = db.session.query(User)\
							  .filter(User.public_id.in_(user_id))\
							  .filter_by(status=5)\
							  .all()

    if num_users:
        data =[]
        for user in num_users:
            response = {}
            user_type, = db.session.query(Usertype.public_id).filter_by(public_id=user.user_type).first()
            registered_by = db.session.query(User).filter_by(public_id=user.session_id).first()

            response['public_id'] = user.public_id
            response['full_name'] = user.first_name.strip().title() + " " + user.last_name.strip().title()
            response['phone_number'] = user.phone_number
            response['email'] = user.email
            response['user_type_public_id'] = user.user_type
            response['user_type'] = user_type
            response['registered_by'] = registered_by.first_name + " " + registered_by.first_name if registered_by else ""
            response['registered_on'] = user.created_at
            data.append(response)
        
        responseObject = {
            'data' : data
        }
        return make_response(jsonify(responseObject)), 200
    else:
        responseObject = {
            'message' : 'No users found'
        }
        return make_response(jsonify(responseObject)), 412
            

@app.route('/users')
# @cache.cached(timeout=86400)
# @require_api_token
def getAllUser():
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            auth_token = auth_header.split(" ")[1]
        except IndexError as identifier:
            responseObject = {
                'status' : 'failed',
                'message' : 'Beared token malformed'
            }
            return make_response(jsonify(make_response)), 401
    else:
        auth_token = ''
        responseObject = {
            'message' : 'Token is missing'
        }
        return make_response(jsonify(responseObject)), 404

    if auth_token:
        try:
            resp = User.decode_auth_token(auth_token)
            print('resp : ' + resp)
        except Exception as identifier:
            error = traceback.format_exc()
            print(error)
            return jsonify({error}), 500
        user = db.session.query(User).filter_by(public_id=resp, status=5).filter(User.instituition_id == None).first()
        if not user:
            return jsonify({'message' : resp, 'resp' : resp}), 422
            
        user_type, = db.session.query(Usertype.public_id).filter_by(public_id=user.user_type).first()
        first_name, =  db.session.query(User.first_name).filter_by(public_id=user.session_id).first()
        last_name, =  db.session.query(User.last_name).filter_by(public_id=user.session_id).first()
        registered_by = first_name + " " + last_name

        #check if the usertype is assigned that feature
        allowed = db.session.query(FeatureRole).filter_by(role_public_id=user.user_type, feature_public_id='7fc6f0e7').filter(FeatureRole.deletion_marker == None).first()

        if allowed:
            users = db.session.query(User).filter(User.deletion_marker == None).order_by(User.created_at.desc()).all()
            users_array = []

            for user in users:
                response = {}
                user_role, = db.session.query(Usertype.name).filter_by(public_id=user.user_type).first()

                response['public_id'] = user.public_id
                response['full_name'] = user.first_name.strip().title() + " " + user.last_name.strip().title()
                response['phone_number'] = user.phone_number
                response['email'] = user.email
                response['user_type'] = user_role
                response['registered_by'] = registered_by
                response['user_type_id'] = user.user_type
                response['user_role'] = user_role
                response['registered_on'] = user.created_at
                response['active_status'] = 'Suspended' if int(user.status) == 15 else 'Active'
                users_array.append(response)
            
            responseObject = {
                'data' : users_array
            }
            return make_response(jsonify(responseObject)), 200
        else:
            responseObject = {
                'message' : 'invalid permissions to view this page {0}'.format(user_type)
            }
            return make_response(jsonify(responseObject)), 403
    else:
        responseObject = {
            'status': 'fail',
            'message': resp
        }
        return make_response(jsonify(responseObject)), 401


@app.route('/user/update/<public_id>', methods=['POST'])
# @require_api_token
def updateUser(public_id):
    user = db.session.query(User).filter_by(public_id=public_id).first()

    if not user:
        return jsonify({'message' : 'User Not Found'}), 412
    else:
        first_name = request.json['first_name']
        last_name = request.json['last_name']
        email = request.json['email']
        phone_number = request.json['phone_number']
        user_type = request.json['user_type']

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone_number = phone_number
        user.user_type = user_type

        try:
            db.session.commit()
            close(db)
            clearCache()
            responseObject = {
                'message' : 'Successfully updated'
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as identifier:
            responseObject = {
                'error' : str(identifier)
            }
            return make_response(jsonify(responseObject)), 500


@app.route('/user/delete/<public_id>', methods=['DELETE'])
# @require_api_token
def deleteUser(public_id):
    user = db.session.query(User).filter_by(public_id=public_id).first()

    if not user:
        return jsonify('User Not Found')
    else:
        user.status = 10
        user.deletion_marker = 1
        user.updated_at = datetime.now()
        try:
            db.session.commit()
            close(db)
            clearCache()
            responseObject = {
                'message' : 'Successfully deleted'
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as identifier:
            responseObject = {
                'error' : str(identifier)
            }
            return make_response(jsonify(responseObject)), 500

@app.route('/user/suspend/<public_id>')
# @require_api_token
def suspendUser(public_id):
    user = db.session.query(User).filter_by(public_id=public_id, status=5).first()

    if not user:
        return jsonify('User Not Found')
    else:
        user.status = 15 # suspended user
        user.updated_at = datetime.now()
        try:
            db.session.commit()
            close(db)
            clearCache()
            responseObject = {
                'message' : 'Successfully suspended'
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as identifier:
            responseObject = {
                'error' : str(identifier)
            }
            return make_response(jsonify(responseObject)), 500

@app.route('/user/unsuspend/<public_id>')
# @require_api_token
def unsuspendUser(public_id):
    user = db.session.query(User).filter_by(public_id=public_id, status=15).first()

    if not user:
        return jsonify('User Not Found')
    else:
        user.status = 5
        user.updated_at = datetime.now()
        try:
            db.session.commit()
            close(db)
            clearCache()
            responseObject = {
                'message' : 'Successfully unsuspended'
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as identifier:
            responseObject = {
                'error' : str(identifier)
            }
            return make_response(jsonify(responseObject)), 500

'''Get all the users belonging to a particular institution'''

@app.route('/users/institution/<public_id>')
@cache.cached(timeout=86400)
# @require_api_token
def getInstitutionUsers(public_id):
    users = db.session.query(User).filter_by(instituition_id=public_id).filter(User.deletion_marker==None).all()

    if not users:
        responseObject = {
            'message' : 'no users found'
        }
        return make_response(jsonify(responseObject)), 412
    else:
        output = []
        for user in users:
            user_type, = db.session.query(Usertype.name).filter_by(public_id=user.user_type).first()
            response = {}
            response['public_id'] = user.public_id
            response['full_name'] = user.first_name.strip().title() + " " + user.last_name.strip().title()
            response['phone_number'] = user.phone_number
            response['email'] = user.email
            response['user_role'] = user_type
            response['user_type_id'] = user.user_type
            response['user_type'] = user_type
            response['registered_on'] = user.created_at
            output.append(response)

        responseObject = {
            'data' : output
        }
        return make_response(jsonify(responseObject)), 200


@app.route('/partner/deactivate', methods=['POST'])
def deactivateUsers():
    instituition_id = request.json['instituition_id']
    session_id = request.json['session_id']

    users = db.session.query(User).filter_by(instituition_id=instituition_id).filter(User.deletion_marker == None).all()

    if not users:
        responseObject = {
            'message' : 'No users found'
        }
        return make_response(jsonify(responseObject)), 200
    else:
        output = []
        for user in users:
            user.status = 15
            user.suspended_by = session_id
            user.suspended_at = datetime.now()
            
            db.session.add(user)
        
        db.session.commit()
        close(db)
        responseObject = {
            'message' : 'Successfully deleted'
        }
        return make_response(jsonify(responseObject)), 200


@app.route('/partner/activate', methods=['POST'])
def activateUsers():
    instituition_id = request.json['instituition_id']
    session_id = request.json['session_id']

    users = db.session.query(User).filter_by(instituition_id=instituition_id).filter(User.status == 15).all()

    if not users:
        responseObject = {
            'message' : 'No users found'
        }
        return make_response(jsonify(responseObject)), 412
    else:
        output = []
        for user in users:
            # user.deletion_marker = ""
            user.status = 5 
            user.unsuspended_by = session_id
            user.unsuspended_at = datetime.now()
            
            db.session.add(user)
        
        db.session.commit()
        close(db)
        responseObject = {
            'message' : 'Successfully deleted'
        }
        return make_response(jsonify(responseObject)), 200