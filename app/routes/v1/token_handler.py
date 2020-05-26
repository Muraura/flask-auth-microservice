from flask import Flask, jsonify, make_response, request
from routes.v1 import app
import pymysql, os, math, requests, uuid
from datetime import datetime, timedelta
from routes.v1 import db, cache, clearCache
from models import Usertype, Gender, Country, User, RequestTracker

@app.route('/token/oauth', methods=['POST'])
# @cache.cached(timeout=86400)
def tokenAuthenticator():
    token = request.json['token']

    auth_header = token if 'token' in request.json else ''
    if auth_header:
        try:
            auth_token = auth_header.split(" ")[1]
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

    if auth_token:
        resp = User.decode_auth_token(auth_token)
        user = db.session.query(User).filter_by(public_id=resp, status=5).filter(User.instituition_id == None).first()

        if user:
            new_entry = RequestTracker(
                public_id = str(uuid.uuid4())[:12],
                url = request.json['url'],
                method = request.json['method'],
                token = auth_header,
                user = user.public_id,
                success = 1,
                content = str(request.json['content']),
                server = request.environ['REMOTE_ADDR'] if request.environ['REMOTE_ADDR'] else '0.0.0.0',
                created_at = datetime.now(),
                status = 5
            )
            new_entry.save_to_db()

            return jsonify({'message' : "1"})
        else:
            new_entry = RequestTracker(
                public_id = str(uuid.uuid4())[:12],
                url = request.json['url'],
                method = request.json['method'],
                token = auth_header,
                user = user.public_id,
                content = str(request.json['content']),
                success = 0,
                server = request.environ['REMOTE_ADDR'] if request.environ['REMOTE_ADDR'] else '0.0.0.0',
                created_at = datetime.now(),
                status = 10
            )
            new_entry.save_to_db()

            return jsonify({'message' : "0"})


