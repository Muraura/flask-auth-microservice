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

@app.route('/roles')
@require_api_token
@cache.cached(timeout=86400)
def getRoles():
    roles = db.session.query(Usertype).all()

    if not roles:
        responseObject = {
            'message' : 'No Roles Available'
        }
        return make_response(jsonify(responseObject)), app.config['ERROR_CODE']
    else:
        output = []

        for role in roles:
            response = {}
            response['name'] = role.name
            response['description'] = role.description
            response['public_id'] = role.public_id
            output.append(response)
        
        responseObject = {
            'data' : output
        }
        return make_response(jsonify(responseObject)), 200


@app.route('/role/add', methods=['POST'])
@require_api_token
def addRole():
    name = request.json['name']
    description = request.json['description']

    if name == "":
        responseObject = {
                'message' : 'Not all fields are provided'
            }
        return make_response(jsonify(responseObject)), 200
    else:
        new_role = Usertype(
            public_id = str(uuid.uuid4())[:8],
            name = name,
            description = description,
            created_at = datetime.now()
        )
        db.session.add(new_role)
        try:
            db.session.commit()
            close(db)
            clearCache()
            responseObject = {
                'message' : 'Successfully added the {0} Role'.format(name)
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

@app.route('/role/update/<public_id>', methods=['POST'])
@require_api_token
def updateRole(public_id):
    name = request.json['name']
    descsription = request.json['description']
    role = db.session.query(Usertype).filter_by(public_id=public_id).first()
    if not role:
        responseObject = {
                'message' : 'No such Role is Available'
            }
        return make_response(jsonify(responseObject)), app.config['ERROR_CODE']
    else:
        try:
            role.name = name
            role.description = descsription
            role.updated_at = datetime.now()
            db.session.commit()
            close(db)
            clearCache()
            responseObject = {
                'message' : 'Successfully added the {0} Role'.format(name)
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as identifier:
            db.session.rollback()
            close(db)
            responseObject = {
                'status': str(identifier),
                'message': 'Could not add the role'
            }
            return make_response(jsonify(responseObject)), 500

@app.route('/role/delete/<public_id>')
@require_api_token
def deleteRole(public_id):
    role = db.session.query(Usertype).filter_by(public_id=public_id).first()

    if not role:
        responseObject = {
            'message' : 'Could not find the role'
        }
        return make_response(jsonify(responseObject)), 200
    else:
        role.status = 10
        role.updated_at = datetime.now()

        db.session.commit()
        close(db)
        clearCache()
        responseObject = {
            'message': 'Successfully deleted '
        }
        return make_response(jsonify(responseObject)), 200

        