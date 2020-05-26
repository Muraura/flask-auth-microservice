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

@app.route('/features')
@cache.cached(timeout=86400)
# @require_api_token
def getFeatures():
    features = db.session.query(Feature).filter_by(status=5).all()

    if not features:
        responseObject = {
            'message' : 'No Features Available'
        }
        return make_response(jsonify(responseObject)), app.config['ERROR_CODE']
    else:
        output = []

        for feature in features:
            response = {}
            response['name'] = feature.name
            response['description'] = feature.description
            response['public_id'] = feature.public_id
            response['url'] = feature.url
            menu_name, = db.session.query(Menu.name).filter_by(public_id=feature.menu_public_id).first()
            response['menu'] = menu_name
            output.append(response)
        
        responseObject = {
            'data' : output
        }
        return make_response(jsonify(responseObject)), 200


@app.route('/feature/add', methods=['POST'])
# @require_api_token
def addFeature():
    name = request.json['name']
    url = request.json['url']
    description = request.json['description']
    menu_public_id = request.json['menu_public_id']
    feature_type = request.json['feature_type']

    if name == "" or menu_public_id == "":
        responseObject = {
                'message' : 'Not all fields are provided'
            }
        return make_response(jsonify(responseObject)), 200
    else:
        new_feature = Feature(
            public_id = str(uuid.uuid4())[:8],
            name = name,
            url = url,
            description = description,
            menu_public_id = menu_public_id,
            feature_type = feature_type if feature_type else 1, 
            created_at = datetime.now()
        )
        db.session.add(new_feature)
        try:
            db.session.commit()
            close(db)
            clearCache()
            responseObject = {
                'message' : 'Successfully added the {0} Feature'.format(name)
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as identifier:
            db.session.rollback()
            close(db)
            responseObject = {
                'status': str(identifier),
                'message': 'Could not add the menu'
            }
            return make_response(jsonify(responseObject)), 500


@app.route('/feature/update/<public_id>', methods=['POST'])
# @require_api_token
def updateFeature(public_id):
    name = request.json['name']
    descsription = request.json['description']
    menu_public_id = request.json['menu_public_id']

    feature = db.session.query(Feature).filter_by(public_id=public_id, status=5).first()
    if not feature:
        responseObject = {
                'message' : 'No such Feature is Available'
            }
        return make_response(jsonify(responseObject)), 200
    else:
        try:
            feature.name = name
            feature.description = descsription
            feature.menu_public_id = menu_public_id
            feature.updated_at = datetime.now()

            db.session.commit()
            close(db)
            clearCache()
            responseObject = {
                'message' : 'Successfully added the {0} Feature'.format(name)
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as identifier:
            db.session.rollback()
            close(db)
            responseObject = {
                'status': str(identifier),
                'message': 'Could not add the feature'
            }
            return make_response(jsonify(responseObject)), 500

# Get feature that the role isn't selected in
# params public_id (role_id)
@app.route('/feature/notassigned/<public_id>')
# @cache.cached(timeout=86400)
# @require_api_token
def getNoneAssignedFeatures(public_id):
    #get all features that are currently assigned
    assigned_features = db.session.query(FeatureRole).filter_by(role_public_id=public_id).filter(FeatureRole.deletion_marker == None).all()
    not_in_features = []

    for not_in in assigned_features:
        not_in_features.append(not_in.feature_public_id)

    # perform a where not in query on the Features table
    not_assigned_features = db.session.query(Feature).filter(~Feature.public_id.in_(not_in_features)).filter_by(status=5).filter(Feature.deletion_marker == None).all()
    not_assigned_features_count = db.session.query(Feature).filter(~Feature.public_id.in_(not_in_features)).filter_by(status=5).filter(Feature.deletion_marker == None).count()
    output = []

    for feature in not_assigned_features:
        response = {}
        response['name'] = feature.name
        response['description'] = feature.description
        response['public_id'] = feature.public_id
        response['url'] = feature.url
        menu_name, = db.session.query(Menu.name).filter_by(public_id=feature.menu_public_id).first()
        response['menu'] = menu_name
        output.append(response)
        
    responseObject = {
        'data' : sorted(output, key=lambda x: x['menu'], reverse=False),
        'not_assigned': not_assigned_features_count
    }
    return make_response(jsonify(responseObject)), 200
    
