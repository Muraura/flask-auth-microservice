import math
import os
import uuid
from datetime import datetime, timedelta

import requests
from flask import Flask, jsonify, make_response, request

import pymysql
from models import (Country, CountryCode, Feature, FeatureRole, Gender, Menu,
                    Usertype, FeatureAssignmentTracker, AccessTimes)
from routes.v1 import app, cache, clearCache, db


def close(self):
	self.session.close()

@app.route("/")
def index():
    return jsonify({'message':'Hello world. Welcome to the flask amura service'})


@app.route("/clear/cache")
def clear_cache_url():
    clearCache()
    return jsonify({
        "message": "Cache cleared"
    })


@app.errorhandler(404)
def page_not_found(e):
    responseObject ={
        'message' : 'This is not the page you are looking for. Move along.'
    }
    return make_response(jsonify(responseObject))

@app.route('/countries')
def getCountries():
    countries = db.session.query(Country)\
                          .join(CountryCode, Country.public_id == CountryCode.country)\
                          .add_columns(Country.public_id, Country.code, Country.name,\
                                       CountryCode.calling_code)\
                          .all()
    
    output = []

    if countries:
        for country in countries:
            response = {}
            response['public_id'] = country.public_id
            response['code'] = country.code
            response['name'] = country.name
            response['calling_code'] = country.calling_code
            output.append(response)
        
        responseObject = {
            'data' : output
        }
        return make_response(jsonify(responseObject)), 200
    else:
        responseObject = {
            'message' : 'No countries found'
        }
        return make_response(jsonify(responseObject)), 412


@app.route("/seed/country-codes", methods = ["POST"])
def seedCountryCode():
    countries = db.session.query(Country).all()
    list_countries = countries

    get_all_countries = requests.get("https://restcountries.eu/rest/v2/all")

    db.session.close()

    if list_countries:
        for country in list_countries:
            for single in get_all_countries.json():
                if country.name == single["name"] or country.name in single["name"]:
                    for call in single["callingCodes"]:
                        country_code = CountryCode(
                            public_id = str(uuid.uuid4())[:6],
                            status = 5,
                            calling_code = call,
                            country = country.public_id,
                            created_at = datetime.now()
                        )

                        db.session.add(country_code)

                        try:
                            db.session.commit()
                            db.session.close()

                        except Exception:
                            db.session.rollback()
                            db.session.close()

                else:
                    pass

    return "Ok"


@app.route('/country/<public_id>')
def singleCountry(public_id):
    country = db.session.query(Country).filter_by(public_id=public_id).first()

    if not country:
        responseObject = {
            'message' : 'No countries found'
        }
        return make_response(jsonify(responseObject)), 422
    
    responseObject = {
        'name' : country.name,
        'code' : country.code,
        'public_id': country.public_id
    }
    return make_response(jsonify(responseObject)), 200


@app.route('/genders')
def getGenders():
    genders = db.session.query(Gender).filter(Gender.deletion_marker == None).filter(Gender.name != "Mixed").all()
    output = []

    for gender in genders:
        response = {}
        response['public_id'] = gender.public_id
        response['name'] = gender.name
        output.append(response)
    
    responseObject = {
        'data' : output
    }
    return make_response(jsonify(responseObject)), 200


@app.route('/genders/schools')
def getSchoolGenders():
    genders = db.session.query(Gender).filter(Gender.deletion_marker == None).all()
    output = []

    for gender in genders:
        response = {}
        response['public_id'] = gender.public_id
        response['name'] = gender.name
        output.append(response)
    
    responseObject = {
        'data' : output
    }
    return make_response(jsonify(responseObject)), 200


@app.route('/gender/<public_id>')
def singleGender(public_id):
    gender = db.session.query(Gender).filter_by(public_id=public_id).first()

    if not gender:
        responseObject = {
            'message' : 'No Genders found'
        }
        return make_response(jsonify(responseObject)), 422
    
    responseObject = {
        'name' : gender.name,
        'public_id': gender.public_id
    }
    return make_response(jsonify(responseObject)), 200
        


@app.route('/usertypes')
@cache.cached(timeout=86400)
def getUserTypes():
    types = db.session.query(Usertype).filter_by(status=5).all()

    if not types:
        responseObject ={
            'message' : 'No Types Found'
        }
        return make_response(jsonify(responseObject)), 404
    else:
        output = []
        for data in types:
            response = {}
            response['name'] = data.name
            response['public_id'] = data.public_id
            response['description'] = data.description
            output.append(response)
        
        responseObject = {
            'data' : output
        }
        return make_response(jsonify(responseObject)), 200

@app.route('/single/usertype/<public_id>')
@cache.cached(timeout=86400)
def getSingleUserType(public_id):
    is_type = Usertype.query.filter_by(public_id=public_id).first()
    if not is_type:
        return jsonify({'message' : 'No such usertype can be found'})
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
        'name' : is_type.name,
        'public_id' : public_id,
        'description' : is_type.description,
        'features' : output
    }
    return jsonify(responseObject), 200

@app.route('/add/usertype', methods=['POST'])
def addUserType():
    name = request.json['name']
    desc = request.json['description']

    if name == " " or desc == " ":
        responseObject = {
            'message' : 'not all fields have been provided'
        }
        return make_response(jsonify(responseObject)), 201
    else:
        new_type = Usertype(
            public_id = str(uuid.uuid4())[:8],
            name = name,
            description = desc,
            status = 5,
            created_at = datetime.now()
        )
        db.session.add(new_type)
        try:
            db.session.commit()
            close(db)
            clearCache()
            responseObject = {
                'message' : 'Successfully added'
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as identifier:
            responseObject = {
                'error' : str(identifier)
            }
            return make_response(jsonify(responseObject)), 500

@app.route('/update/usertype/<public_id>', methods=['POST'])
def updateUserType(public_id):
    name = request.json['name']
    desc = request.json['description']

    if name == " " or desc == " ":
        responseObject = {
            'message' : 'not all fields have been provided'
        }
        return make_response(jsonify(responseObject)), 201
    else:
        usertype = db.session.query(Usertype).filter_by(public_id=public_id).first()
        if not usertype:
            responseObject = {
                'message' : 'Could not find the user type'
            }
            return make_response(jsonify(responseObject)), 404
        else:
            usertype.name = name
            usertype.description = desc
            updated_at = datetime.now()

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

@app.route('/delete/usertype/<public_id>', methods=['DELETE'])
def deleteUserType(public_id):
    usertype = db.session.query(Usertype).filter_by(public_id=public_id).first()
    if not usertype:
        responseObject = {
            'message' : 'Could not find the user type'
        }
        return make_response(jsonify(responseObject)), 404
    else:
        usertype.status = 10
        usertype.deletion_marker = 1

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

@app.route('/fetch/logs')
def loginLogs():
    accessTimes = AccessTimes.query.order_by(AccessTimes.created_at.desc()).all()

    if not accessTimes:
        return jsonify({'message' : 'No current logs'}), 412

    return jsonify({'data' : [log.to_json() for log in accessTimes]}), 200

@app.route('/fetch/feature/logs')
def featureAssignmentLogs():
    accessTimes = FeatureAssignmentTracker.query.order_by(FeatureAssignmentTracker.created_at.desc()).all()

    if not accessTimes:
        return jsonify({'message' : 'No current logs'}), 412

    return jsonify({'data' : [log.to_json() for log in accessTimes]}), 200