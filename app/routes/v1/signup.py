from flask import Flask, jsonify, render_template, url_for, request, redirect, json, make_response
from datetime import datetime, timedelta


import pymysql, os, math, requests, uuid, jwt


# File imports
from routes.v1 import app
from routes.v1 import db
from routes.v1 import bcrypt, clearCache

import sendgrid
from sendgrid.helpers.mail import * 

from models import Usertype, User, Token

def close(self):
    self.session.close()

@app.route('/signup', methods=['POST'])
def userSignup():
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
        resp = User.decode_auth_token(auth_token)
        if resp == "Signature expired. Please log in again":
            return jsonify({"message": "Signature expired. Please log in again"}), 422
        
        user = db.session.query(User).filter_by(public_id=resp, status=5).filter(User.instituition_id == None).first()

        first_name = request.json['first_name']
        last_name = request.json['last_name']
        email = request.json['email']
        phone_number = request.json['phone_number']
        user_type = request.json['user_type']
        password = str(uuid.uuid4())[:10]


        # check if user exists
        user = db.session.query(User).filter_by(email=email, phone_number=phone_number).first()

        if db.session.query(User).filter_by(email=email).filter(User.deletion_marker == None).first():
            responseObject = {
                'status': 'fail',
                'message': 'User already exists. Please Log in.',
            }
            return make_response(jsonify(responseObject)), 422
        else:
            try:
                #continue with registration
                u_ublic_id = str(uuid.uuid4())[:15]
                user = User(
                    public_id = u_ublic_id,
                    first_name = first_name,
                    last_name = last_name,
                    email = email,
                    phone_number = phone_number,
                    user_type = user_type,
                    session_id = resp,
                    password = bcrypt.generate_password_hash(password, app.config['BCRYPT_LOG_ROUNDS']).decode('utf-8'),
                    created_at = datetime.now()
                )

                db.session.add(user)
                # generate and auth token
                payload = {
                    'exp' : datetime.utcnow() + timedelta(days=1, seconds=5),
                    'iat': datetime.utcnow(),
                    'sub': u_ublic_id
                }
                auth_token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
                # auth_token = user.encode_auth_token(u_ublic_id)
                token = Token(
                    public_id = str(uuid.uuid4())[:8],
                    token = auth_token.decode('utf-8'),
                    user_public_id = u_ublic_id,
                    client_id = 1,
                    scopes = '[]',
                    created_at = datetime.now()
                )
                db.session.add(token)
                try:
                    #commit to the database
                    db.session.commit()
                    close(db)
                    clearCache()
                    datenow = (datetime.now()).strftime("%B %Y")
                    #send email to partner user
                    recipients = email
                    sender = app.config['MAIL_ADDRESS']
                    sg = sendgrid.SendGridAPIClient(apikey=app.config['SENDGRID_API_KEY'])
                    from_email = Email(sender)
                    to_email = Email(recipients)
                    subject = "User Registration"
                    full_name = first_name.strip().title() + " " + last_name.strip().title()
                    pass_data = {
                        'confirm_account_url' : app.config['REGISTRATION_URL'],
                        'username' : email,
                        'full_name' : full_name,
                        'datenow' : datenow,
                        'password' : password,
                        'copyright_year' : datetime.now().strftime("%Y")
                    }
                    content = Content("text/html", render_template('account.html', data=pass_data))
                    mail = Mail(from_email, subject, to_email, content)
                    response = sg.client.mail.send.post(request_body=mail.get())

                    responseObject = {
                        'message' : 'Successfully Registered {0}'.format(full_name)
                        # 'access_token' : auth_token.decode()
                    }
                    return make_response(jsonify(responseObject)), 200
                except Exception as identifier:
                    db.session.rollback()
                    close(db)
                    clearCache()
                    responseObject = {
                        'message' : str(identifier),
                        'error' : 'From commit try & catch'
                    }
                    return make_response(jsonify(responseObject)), 202
            except Exception as identifier:
                db.session.rollback()
                close(db)
                clearCache()
                responseObject = {
                    'error' : str(identifier),
                    'message': 'Some error occurred. Please try again. under if not'                
                }
                return make_response(jsonify(responseObject)), 401


@app.route('/partner/user', methods=['POST'])
def partnerSignup():

    first_name = request.json['first_name']
    last_name = request.json['last_name']
    email = request.json['email']
    phone_number = request.json['phone_number']
    user_type = request.json['user_type']
    session_id = request.json['session_id']
    partner_public_id = request.json['partner_public_id']

    empty_set = []

    if not partner_public_id or not user_type:
        empty_set.append("Not all fields are provided")
    
    if empty_set:
        responseObject = {
            'messages' : empty_set
        }
        return make_response(jsonify(responseObject)), 422

    # check if user exists
    user = db.session.query(User).filter_by(email=email, phone_number=phone_number).filter(User.deletion_marker==None).first()

    if user:
        responseObject = {
            'status': 'fail',
            'message': 'User already exists. Please Log in.',
        }
        return make_response(jsonify(responseObject)), 202
    else:
        try:
            #continue with registration
            u_ublic_id = str(uuid.uuid4())[:15]
            generate_password = str(uuid.uuid4())[:8]
            # generate_password = '123456'
            # check if an Admin exists
            admin_exits = db.session.query(User).filter_by(instituition_id=partner_public_id, partner_admin_status=100).filter(User.deletion_marker == None).first()
            if admin_exits:
                user = User(
                    public_id = u_ublic_id,
                    first_name = first_name,
                    last_name = last_name,
                    email = email,
                    phone_number = phone_number,
                    user_type = user_type,
                    session_id = session_id,
                    password = bcrypt.generate_password_hash(generate_password, app.config['BCRYPT_LOG_ROUNDS']).decode('utf-8'),
                    instituition_id = partner_public_id,
                    created_at = datetime.now()
                )
            else:
                user = User(
                    public_id = u_ublic_id,
                    first_name = first_name,
                    last_name = last_name,
                    email = email,
                    phone_number = phone_number,
                    user_type = user_type,
                    session_id = session_id,
                    password = bcrypt.generate_password_hash(generate_password, app.config['BCRYPT_LOG_ROUNDS']).decode('utf-8'),
                    instituition_id = partner_public_id,
                    created_at = datetime.now(),
                    partner_admin_status = 100
                )

            db.session.add(user)
            # generate and auth token
            payload = {
                'exp' : datetime.utcnow() + timedelta(days=1, seconds=5),
                'iat': datetime.utcnow(),
                'sub': u_ublic_id
            }
            auth_token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
            # auth_token = user.encode_auth_token(u_ublic_id)
            token = Token(
                public_id = str(uuid.uuid4())[:8],
                token = auth_token.decode('utf-8'),
                user_public_id = u_ublic_id,
                client_id = 1,
                scopes = '[]',
                created_at = datetime.now()
            )
            db.session.add(token)
            try:
                #commit to the database
                db.session.commit()
                close(db)
                clearCache()
                datenow = (datetime.now()).strftime("%B %Y")
                #send email to partner user
                recipients = email
                sender = app.config['MAIL_ADDRESS']
                sg = sendgrid.SendGridAPIClient(apikey=app.config['SENDGRID_API_KEY'])
                from_email = Email(sender)
                to_email = Email(recipients)
                subject = "Partner User Registration"
                pass_data = {
                    'confirm_account_url' : app.config['REGISTRATION_URL'],
                    'username' : email,
                    'full_name' : first_name.strip().title() + " " + last_name.strip().title(),
                    'datenow' : datenow,
                    'password' : generate_password,
                    'copyright_year' : datetime.now().strftime("%Y")
                }
                content = Content("text/html", render_template('user_registration.html', data=pass_data))
                mail = Mail(from_email, subject, to_email, content)
                response = sg.client.mail.send.post(request_body=mail.get())

                full_name = first_name.strip().title() + " " + last_name.strip().title()
                responseObject = {
                    'message' : 'Successfully Registered {0}'.format(full_name)
                }
                return jsonify(responseObject), 200
            except Exception as identifier:
                db.session.rollback()
                close(db)
                clearCache()
                print(str(identifier))
                responseObject = {
                    'error_message' : str(identifier),
                    'error' : 'From commit try & catch'
                }
                return make_response(jsonify(responseObject)), 202
        except Exception as identifier:
            db.session.rollback()
            close(db)
            responseObject = {
                'error' : str(identifier),
                'message': 'Some error occurred. Please try again. under if not'                
            }
            return make_response(jsonify(responseObject)), 401



@app.route('/member/user', methods=['POST'])
def memberSignup():

    first_name = request.json['first_name']
    last_name = request.json['last_name']
    email = request.json['email']
    phone_number = request.json['phone_number']
    user_type = request.json['user_type']
    member = request.json['member_public_id']

    # check if user exists
    user = db.session.query(User).filter_by(email=email, phone_number=phone_number).first()

    if user:
        responseObject = {
            'status': 'fail',
            'message': 'User already exists. Please Log in.',
        }
        return make_response(jsonify(responseObject)), 202
    else:
        try:
            #continue with registration
            u_ublic_id = str(uuid.uuid4())[:15]
            generate_password = str(uuid.uuid4())[:8]

            user = User(
                public_id = u_ublic_id,
                first_name = first_name,
                last_name = last_name,
                email = email,
                phone_number = phone_number,
                user_type = user_type,
                password = bcrypt.generate_password_hash(generate_password, app.config['BCRYPT_LOG_ROUNDS']).decode('utf-8'),
                instituition_id = member,
                created_at = datetime.now()
            )

            db.session.add(user)
            # generate and auth token
            payload = {
                'exp' : datetime.utcnow() + timedelta(days=1, seconds=5),
                'iat': datetime.utcnow(),
                'sub': u_ublic_id
            }
            auth_token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
            # auth_token = user.encode_auth_token(u_ublic_id)
            token = Token(
                public_id = str(uuid.uuid4())[:8],
                token = auth_token,
                user_public_id = u_ublic_id,
                client_id = 1,
                scopes = '[]',
                created_at = datetime.now()
            )
            db.session.add(token)
            try:
                #commit to the database
                db.session.commit()
                close(db)
                datenow = (datetime.now()).strftime("%B %Y")
                #send email to partner user
                recipients = email
                sender = app.config['MAIL_ADDRESS']
                sg = sendgrid.SendGridAPIClient(apikey=app.config['SENDGRID_API_KEY'])
                from_email = Email(sender)
                to_email = Email(recipients)
                subject = "Member Access"
                pass_data = {
                    'confirm_account_url' : app.config['REGISTRATION_URL'],
                    'full_name' : first_name.strip().title() + " " + last_name.strip().title(),
                    'datenow' : datenow,
                    'password' : generate_password,
                    'copyright_year' : datetime.now().strftime("%Y")
                }
                content = Content("text/html", render_template('member_access.html', data=pass_data))
                mail = Mail(from_email, subject, to_email, content)
                response = sg.client.mail.send.post(request_body=mail.get())

                full_name = first_name.strip().title() + " " + last_name.strip().title()
                responseObject = {
                    'message' : 'Successfully Registered {0}'.format(full_name),
                    'password' : generate_password
                }
                return jsonify(responseObject), 200
            except Exception as identifier:
                db.session.rollback()
                close(db)

                responseObject = {
                    'message' : str(identifier),
                    'error' : 'From commit try & catch'
                }
                return make_response(jsonify(responseObject)), 202
        except Exception as identifier:
            db.session.rollback()
            close(db)
            responseObject = {
                'error' : str(identifier),
                'message': 'Some error occurred. Please try again. under if not'                
            }
            return make_response(jsonify(responseObject)), 401


