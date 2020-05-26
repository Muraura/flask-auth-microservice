from flask import Flask, jsonify, render_template, url_for, request, redirect, json, make_response
from datetime import datetime, timedelta


import pymysql, os, math, requests, uuid
import logging
from logging.handlers import RotatingFileHandler

# File imports
from routes.v1 import app
from routes.v1 import db
from routes.v1 import bcrypt

from models import User, Usertype, Token, AccessTimes, FeatureRole, Feature, Menu


def close(self):
    self.session.close()


@app.route('/login', methods=['POST'])
def login():

    email = request.json['email']
    password = request.json['password']

    try:
        #check if user is suspended
        user = db.session.query(User).filter_by(email=email).filter(User.deletion_marker == None).first()
        if int(user.status) == 15:
            return jsonify({'message' : 'Account has been suspended'}), 422
            
        #check if email exists
        user = db.session.query(User).filter_by(email=email, status=5).filter(User.deletion_marker == None).first()

        if user and bcrypt.check_password_hash(user.password, password):
            auth_token = user.encode_auth_token(user.public_id)
            if auth_token:
                # log the session
                # send_url = 'http://freegeoip.net/json'
                # r = requests.get(send_url)
                # j = json.loads(r.text)
                # lat = j['latitude']
                # lon = j['longitude']
                # public_ip = j['ip']
                # timezone = j['time_zone']
                # country_name = j['country_name']
                tracker_id = str(uuid.uuid4())
                new_log = AccessTimes(
                    user_public_id = user.public_id,
                    public_id=tracker_id,
                    loggin_status_code = 10, # denotes still logged in
                    ip_address = request.headers.get('X-Real-IP', request.remote_addr),
                    public_ip = request.headers.get('X-Real-IP', request.remote_addr),
                    browser = request.headers.get("User-Agent"),
                    logged_in_at = datetime.now(),
                    created_at = datetime.now()
                )
                
                db.session.add(new_log)
                db.session.commit()

                #get the users menu
                featureRoles = db.session.query(FeatureRole).filter_by(role_public_id=user.user_type, status=5).filter(FeatureRole.deletion_marker == None).all()
                features_array = []
                output = []

                menus = db.session.query(Menu).filter_by(status=5).filter(Menu.deletion_marker == None).all()
                for menu in menus:
                    response = {}
                    response['name'] = menu.name
                    response['description'] = menu.description
                    response['public_id'] = menu.public_id
                    response['rating'] = menu.rating

                    features = []
                    items =  db.session.query(Feature).filter_by(menu_public_id=menu.public_id, status=5).filter(Feature.deletion_marker == None).all()
                    for item in items:
                        return_object = {}
                        # Check the user type -> If user type is of Partner -> check if its the first partner -> if it is -> append Create User feature -> else don't
                        if user.user_type == '35fcfdaf':
                            admin_first_partner = db.session.query(User).filter_by(email=email, instituition_id=user.instituition_id, partner_admin_status=100).filter(User.deletion_marker == None).first()
                            if admin_first_partner:
                                return_object['name'] = item.name
                                return_object['public_id'] = item.public_id
                                return_object['url'] = item.url
                                return_object['type'] = item.feature_type
                                if db.session.query(FeatureRole).filter_by(role_public_id=user.user_type, feature_public_id=item.public_id).filter(FeatureRole.deletion_marker == None).first():
                                    return_object['active'] = True
                                    features.append(return_object)
                            else:
                                # Not the first partner 
                                # Check the feature ID
                                if item.public_id == '773a288e':
                                    # Create new users feature
                                    # add it 
                                    pass
                                else:
                                    return_object['name'] = item.name
                                    return_object['public_id'] = item.public_id
                                    return_object['url'] = item.url
                                    if db.session.query(FeatureRole).filter_by(role_public_id=user.user_type, feature_public_id=item.public_id).filter(FeatureRole.deletion_marker == None).first():
                                        return_object['active'] = True
                                        features.append(return_object)
                                    
                        else:
                            return_object['name'] = item.name
                            return_object['public_id'] = item.public_id
                            return_object['url'] = item.url
                            return_object['type'] = item.feature_type
                            if db.session.query(FeatureRole).filter_by(role_public_id=user.user_type, feature_public_id=item.public_id).filter(FeatureRole.deletion_marker == None).first():
                                return_object['active'] = True
                                features.append(return_object)
                    if features: 
                        response['features'] = features
                        output.append(response)

                #get the user type 
                user_type, = db.session.query(Usertype.name).filter_by(public_id=user.user_type).filter(Usertype.deletion_marker == None).first()
                

                if not user.instituition_id:
                    instituition_id = 'N/A'
                    close(db)
                    responseObject = {
                        'status': 'success',
                        'message': 'Successfully logged in.',
                        'auth_token': auth_token.decode(),
                        'user_type' : user_type,
                        'user_type_id' : user.user_type,
                        'created_at' : user.created_at,
                        'instiution_id' : instituition_id,
                        'tracker_id' : tracker_id,
                        'menu' : sorted(output, key=lambda x: x['rating'], reverse=False)
                    }
                    app.logger.info('{0} successfull loggin at {1}'.format(user.public_id, datetime.now()))
                    return make_response(jsonify(responseObject)), 200
                else:
                    instituition_id = user.instituition_id
                    partner_name = requests.get('https://{}:5003/v1/partner/{}'.format(app.config['SERVER'],user.instituition_id))
                    close(db)
                    responseObject = {
                        'status': 'success',
                        'message': 'Successfully logged in.',
                        'auth_token': auth_token.decode(),
                        'user_type_id' : user.user_type,
                        'user_type' : user_type,
                        'instiution_id' : instituition_id,
                        'tracker_id' : tracker_id,
                        'created_at' : user.created_at,
                        'instiution_name' : partner_name.json()["name"] if partner_name.status_code == 200 else "N/A",
                        'menu' : sorted(output, key=lambda x: x['rating'], reverse=False)
                    }
                    app.logger.info('{0} successfull loggin at {1}'.format(user.public_id, datetime.now()))
                    return make_response(jsonify(responseObject)), 200
            else:
                responseObject = {
                    'status': 'fail',
                    'message': 'User does not exist.'
                }
                return make_response(jsonify(responseObject)), 404
        else:
            # send_url = 'http://freegeoip.net/json'
            # r = requests.get(send_url)
            # j = json.loads(r.text)
            # lat = j['latitude']
            # lon = j['longitude']
            # public_ip = j['ip']
            # timezone = j['time_zone']
            # country_name = j['country_name']
            # # log the incorrect user loggin
            # error_log = AccessTimes(
            #     loggin_status_code = 77,# denotes an incorrect login
            #     ip_address = request.headers.get('X-Real-IP', request.remote_addr),
            #     public_ip = public_ip,
            #     browser = request.headers.get("User-Agent"),
            #     latitude = lat,
            #     longitude = lon,
            #     timezone = timezone,
            #     country_name = country_name,
            #     created_at = datetime.now(),
            #     logged_in_at = datetime.now()
            # )
            app.logger.warning('{0} tried to loggin at {1}'.format(email, datetime.now()))
            # db.session.add(error_log)

            # db.session.commit()
            close(db)
            responseObject = {
                'message' : 'Incorrect email or password'
            }
            return make_response(jsonify(responseObject)), 422
    except (Exception, NameError, TypeError, RuntimeError, ValueError) as identifier:
        responseObject = {
                'status': str(identifier),
                'message': 'Try again @login',
                'partner': 'partner_name.json()'
            }
        return jsonify(responseObject), 500
    except (NameError) as name_identifier:
        responseObject = {
                'status': str(name_identifier),
                'message': 'Try again @login',
                'error': 'Name',
            }
    except (TypeError) as type_identifier:
        responseObject = {
                'status': str(type_identifier),
                'message': 'Try again @login',
                'error': 'Type',
            }
    except (RuntimeError) as run_identifier:
        responseObject = {
                'status': str(run_identifier),
                'message': 'Try again @login',
                'error': 'Runtime',
            }
    except (ValueError) as val_identifier:
        responseObject = {
                'status': str(val_identifier),
                'message': 'Try again @login',
                'error': 'Value',
            }
    except (Exception) as exc_identifier:
        responseObject = {
                'status': str(exc_identifier),
                'message': 'Try again @login',
                'error': 'Exception',
                'url': 'http://{}:5003/v1/partner/{}'.format(app.config['SERVER'],user.instituition_id)
            }
        return make_response(jsonify(responseObject)), 500

@app.route('/logout/<tracker_id>')
def logout(tracker_id):
    # get auth token
    auth_header = request.headers.get('Authorization')
    if auth_header:
        auth_token = auth_header.split(" ")[1]
    else:
        auth_token = ''
    if auth_token:
        resp = User.decode_auth_token(auth_token)
        tracker = AccessTimes.query.filter_by(public_id=tracker_id).first()
        if tracker:
            tracker.logged_out_at = datetime.now()
            tracker.loggin_status_code = 100
            db.session.commit()

        if not isinstance(resp, str):
            # mark the token as blacklisted
            blacklist_token = Token(token=0) #denotes a blacklisted token
            try:
                # insert the token
                db.session.add(blacklist_token)
                db.session.commit()
                responseObject = {
                    'status': 'success',
                    'message': 'Successfully logged out.'
                }
                return make_response(jsonify(responseObject)), 200
            except Exception as e:
                responseObject = {
                    'status': 'fail',
                    'message': str(e)
                }
                return make_response(jsonify(responseObject)), 200
        else:
            responseObject = {
                'status': 'fail',
                'message': resp
            }
            return make_response(jsonify(responseObject)), 401
    else:
        responseObject = {
            'status': 'fail',
            'message': 'Provide a valid auth token.'
        }
        return make_response(jsonify(responseObject)), 403