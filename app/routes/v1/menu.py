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

@app.route('/menus')
# @require_api_token
@cache.cached(timeout=86400)
def getMenus():
    menus = db.session.query(Menu).all()

    if not menus:
        responseObject = {
            'message' : 'No Menus Available'
        }
        return make_response(jsonify(responseObject)), app.config['ERROR_CODE']
    else:
        output = []

        public_id = None

        for menu in menus:
            response = {}
            response['name'] = menu.name
            response['rating'] = menu.rating
            response['description'] = menu.description
            response['public_id'] = menu.public_id

            features = []
            items =  db.session.query(Feature).filter_by(menu_public_id=menu.public_id, status=5).order_by(Feature.id.asc()).all()
            for item in items:
                return_object = {}
                return_object['name'] = item.name
                return_object['public_id'] = item.public_id
                return_object['url'] = item.url
                features.append(return_object)

            response['features'] = features
            output.append(response)
        
        responseObject = {
            'data' : sorted(output, key=lambda x: x['rating'], reverse=False)
        }
        return make_response(jsonify(responseObject)), 200


@app.route('/menu/add', methods=['POST'])
# @require_api_token
def addMenu():
    name = request.json['name']
    rating = request.json['rating']
    description = request.json['description']

    if name.strip() is None:
        responseObject = {
                'message' : 'Not all fields are provided'
            }
        return make_response(jsonify(responseObject)), 200
    else:
        new_menu = Menu(
            public_id = str(uuid.uuid4())[:8],
            name = name,
            rating = rating,
            description = description,
            created_at = datetime.now()
        )
        db.session.add(new_menu)
        try:
            db.session.commit()
            close(db)
            clearCache()
            responseObject = {
                'message' : 'Successfully added the {0} Menu'.format(name)
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

@app.route('/menu/update/<public_id>', methods=['POST'])
# @require_api_token
def updateMenu(public_id):
    name = request.json['name']
    rating = request.json['rating']
    descsription = request.json['description']

    menu = db.session.query(Menu).filter_by(public_id=public_id).first()
    if not menu:
        responseObject = {
                'message' : 'No such Menu is Available'
            }
        return make_response(jsonify(responseObject)), app.config['ERROR_CODE']
    else:
        try:
            menu.name = name
            menu.description = descsription
            menu.rating = rating
            menu.updated_at = datetime.now()
            db.session.commit()
            responseObject = {
                'message' : 'Successfully updated the {0} Menu'.format(name)
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as identifier:
            db.session.rollback()
            close(db)
            clearCache()
            responseObject = {
                'status': str(identifier),
                'message': 'Could not add the feature'
            }
            return make_response(jsonify(responseObject)), 500

@app.route('/menu/<public_id>')
@cache.cached(timeout=86400)
# @require_api_token
def getMenu(public_id):

    menu = db.session.query(Menu).filter_by(public_id=public_id).first()
    if not menu:
        responseObject = {
                'message' : 'No such Menu is Available'
            }
        return make_response(jsonify(responseObject)), app.config['ERROR_CODE']
    else:
        try:
            output = []
            features = []
            items =  db.session.query(Feature).filter_by(menu_public_id=menu.public_id, status=5).all()
            for item in items:
                return_object = {}
                return_object['name'] = item.name
                return_object['public_id'] = item.public_id
                return_object['url'] = item.url
                features.append(return_object)

            response = {}
            response['menu_name'] = menu.name
            response['rating'] = menu.rating
            response['description'] = menu.description
            response['features'] = features
            output.append(response)

            responseObject = {
                'data' : output
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