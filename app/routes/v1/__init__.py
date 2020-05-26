from flask import Flask, jsonify, render_template, url_for, request, redirect, json, make_response
from flask_sqlalchemy import SQLAlchemy, functools
from flask_cors import CORS, cross_origin
from datetime import datetime, timedelta

import pymysql, os, math, requests, uuid

from flask_bcrypt import Bcrypt
from functools import wraps

pymysql.install_as_MySQLdb()

import logging
from logging.handlers import *

from flask_cache import Cache


app = Flask(__name__)
cache = Cache(app,config={'CACHE_TYPE': 'simple'})
CORS(app)


def clearCache():
    #clear the cache data
    with app.app_context():
        cache.clear()

# used in route version
def prefix_route(route_function, prefix='', mask='{0}{1}'):
  '''
    Defines a new route function with a prefix.
    The mask argument is a `format string` formatted with, in that order:
      prefix, route
  '''
  def newroute(route, *args, **kwargs):
    '''New function to prefix the route'''
    return route_function(mask.format(prefix, route), *args, **kwargs)
  return newroute

bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

def require_api_token(func):
    @wraps(func)
    def check_token(*args, **kwargs):
        # Check to see if it's in their session
        if 'Authorization' not in request.headers:
            return jsonify({'message':'Access denied, API Token is required'})
        else:
          auth_header = request.headers.get('Authorization')
          url = request.url
          method = request.method
          content = request.json

          if auth_header:
            try:
                auth_token = auth_header.split(" ")[1]
                payload = {
                  'token' : auth_header,
                  'url' : url,
                  'method' : method,
                  'content' : content
                }
                token_auhenticate = requests.post('https://{}:9000/v1/token/oauth'.format(app.config['SERVER']), json=payload)
                
                if 'message' in token_auhenticate.json():
                  if token_auhenticate.json()['message'] == "1":
                    return func(*args, **kwargs)
                  else:
                    responseObject = {
                      'message' : 'Bad Token used'
                    }
                    return make_response(jsonify(responseObject)), 401
                else:
                  return jsonify({'message' : 'bad token'})
            except IndexError as identifier:
                responseObject = {
                    'status' : 'failed',
                    'message' : 'Beared token malformed'
                }
                return make_response(jsonify(responseObject)), 401
          else:
              auth_token = ''
              responseObject = {
                  'message' : 'Token is missing'
              }
              return make_response(jsonify(responseObject)), 404

        # Otherwise just send them where they wanted to go
        return func(*args, **kwargs)

    return check_token

from routes.v1 import base_urls, login, signup, users, passwordresets, roles, menu, feature_role, features, token_handler