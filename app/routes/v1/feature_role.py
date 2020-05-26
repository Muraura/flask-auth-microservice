from flask import Flask, jsonify, render_template, url_for, request, redirect, json, make_response
from datetime import datetime, timedelta


import pymysql, os, math, requests, uuid


# File imports
from routes.v1 import app
from routes.v1 import db
from routes.v1 import cache, clearCache, require_api_token

from models import *

def close(self):
	self.session.close()

@app.route('/role/feature')
@cache.cached(timeout=86400)
@require_api_token
def getARolesFeatures():
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
        user = db.session.query(User).filter_by(public_id=resp, status=5).first()

        featureRoles = db.session.query(FeatureRole).filter_by(role_public_id=user.user_type, status=5).filter(FeatureRole.deletion_marker == None).all()
        features_array = []
        output = []

        menus = db.session.query(Menu).filter_by(status=5).all()
        for menu in menus:
            response = {}
            response['name'] = menu.name
            response['description'] = menu.description
            response['public_id'] = menu.public_id

            features = []
            items =  db.session.query(Feature).filter_by(menu_public_id=menu.public_id, status=5).filter(FeatureRole.deletion_marker == None).all()
            for item in items:
                return_object = {}
                return_object['name'] = item.name
                return_object['public_id'] = item.public_id
                return_object['url'] = item.url
                if db.session.query(FeatureRole).filter_by(role_public_id=user.user_type, feature_public_id=item.public_id).filter(FeatureRole.deletion_marker == None).first():
                    return_object['active'] = True
                    features.append(return_object)
            if features: 
                response['features'] = features
                output.append(response)
                
        responseObject = {
            'data' : output
        }
        return make_response(jsonify(responseObject)), 200
    else:
        responseObject = {
            'message' : 'No token available'
        }
        return make_response(jsonify(responseObject)), 412

@app.route('/role/feature/<public_id>')
@cache.cached(timeout=86400)
@require_api_token
def getARolesFeaturesbyID(public_id):
    featureRoles = db.session.query(FeatureRole).filter_by(role_public_id=public_id, status=5).filter(FeatureRole.deletion_marker == None).all()
    features_array = []
    output = []

    menus = db.session.query(Menu).filter_by(status=5).all()
    for menu in menus:
        response = {}
        response['name'] = menu.name
        response['description'] = menu.description
        response['public_id'] = menu.public_id

        features = []
        items =  db.session.query(Feature).filter_by(menu_public_id=menu.public_id, status=5).all()
        for item in items:
            return_object = {}
            return_object['menu_name'] = menu.name
            return_object['name'] = item.name
            return_object['public_id'] = item.public_id
            return_object['url'] = item.url
            if db.session.query(FeatureRole).filter_by(role_public_id=public_id, feature_public_id=item.public_id).first():
                return_object['active'] = True
                features.append(return_object)
        if features: 
            response['features'] = features
            output.append(response)
            
    responseObject = {
        'data' : output
    }
    return make_response(jsonify(responseObject)), 200


@app.route('/features/role/<public_id>')
@cache.cached(timeout=86400)
# @require_api_token
def getARolesFeaturesbyRoleID(public_id):
    featureRoles = db.session.query(FeatureRole).filter_by(role_public_id=public_id, status=5).filter(FeatureRole.deletion_marker == None).all()
    
    output = []
    for feature in featureRoles:
        response = {}
        menu_name, = db.session.query(Menu.name).filter_by(public_id=feature.menu_public_id).filter(FeatureRole.deletion_marker == None).first()
        feature_name, = db.session.query(Feature.name).filter_by(public_id=feature.feature_public_id).filter(FeatureRole.deletion_marker == None).first()
        url, = db.session.query(Feature.url).filter_by(public_id=feature.feature_public_id).filter(FeatureRole.deletion_marker == None).first()

        response['menu_name'] = menu_name
        response['name'] = feature_name
        response['public_id'] = feature.feature_public_id
        response['url'] = url
        output.append(response)

    responseObject = {
        'data' : sorted(output, key=lambda x: x['menu_name'], reverse=False)
    }
    return make_response(jsonify(responseObject)), 200

@app.route('/role/feature/add', methods=['POST'])
# @require_api_token
def addRelationshipRoleToFeature():
    role_public_id = request.json['role_public_id']
    feature_public_id = request.json['feature_public_id']
    session_id = request.json['session_id']

    #check if that feature is already associated with the role
    status = db.session.query(FeatureRole).filter_by(feature_public_id=feature_public_id, role_public_id=role_public_id).filter(FeatureRole.deletion_marker == None).first()

    if not status:
        # continue to add the relationship
        # query for the menu public id
        menu_id, = db.session.query(Feature.menu_public_id).filter_by(public_id=feature_public_id).filter(FeatureRole.deletion_marker == None).first()

        new_assoc = FeatureRole(
            public_id = str(uuid.uuid4())[:8],
            menu_public_id = menu_id,
            feature_public_id = feature_public_id,
            role_public_id = role_public_id,
            created_at = datetime.now()
        )
        db.session.add(new_assoc)
        feature_name, = db.session.query(Feature.name).filter_by(public_id=feature_public_id).filter(FeatureRole.deletion_marker == None).first()
        role_name, = db.session.query(Usertype.name).filter_by(public_id=role_public_id).filter(FeatureRole.deletion_marker == None).first()
        try:
            db.session.commit()
            trackFeatureAssignment(True, feature_public_id, session_id, role_public_id)
            close(db)
            clearCache()
            responseObject = {
                'message' : 'Successfully associated {0} with {1}'.format(feature_name, role_name)
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as identifier:
            db.session.rollback()
            close(db)
            responseObject = {
                'status': str(identifier),
                'message': 'Could not add the member'
            }
            return make_response(jsonify(responseObject)), 500
    else:
        responseObject = {
            'message' : 'The Role Already has that feature'
        }
        return make_response(jsonify(responseObject)), 200


@app.route('/role/feature/detach', methods=['POST'])
# @require_api_token
def detachAttachement():
    role_public_id = request.json['role_public_id']
    feature_public_id = request.json['feature_public_id']
    session_id = request.json['session_id']

    #check if that feature is already associated with the role
    status = db.session.query(FeatureRole).filter_by(feature_public_id=feature_public_id, role_public_id=role_public_id).filter(FeatureRole.deletion_marker == None).first()

    if not status:
       responseObject = {
           'message' : 'That relation doesnt not exist'
       }
       return make_response(jsonify(responseObject)), 412
    else:
        status.status = 10
        status.deletion_marker = 1
        status.updated_at = datetime.now()

        try:
            db.session.commit()
            trackFeatureAssignment(False, feature_public_id, session_id, role_public_id)
            close(db)
            clearCache()
            responseObject = {
                'message' : 'Successfully detached the feature'
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as identifier:
            db.session.rollback()
            close(db)
            clearCache()
            responseObject = {
                'error' : str(identifier),
                'message' : 'Error occured while trying to detach'
            }
            return make_response(jsonify(responseObject)), 500

def trackFeatureAssignment(action, feature_public_id, session_id, role_public_id):
    # action === true => means attaching
    # action === false => means dettaching
    new_track = FeatureAssignmentTracker(
        public_id = str(uuid.uuid4())[:10],
        feature_public_id = feature_public_id,
        role_public_id = role_public_id,
        action = 1 if action else 0,
        action_by = session_id,
        created_at = datetime.now()
    )
    new_track.save_to_db()
    return ''