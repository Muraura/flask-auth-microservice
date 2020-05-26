from flask import Flask, jsonify, request, make_response, render_template

from routes.v1 import app
from routes.v1 import db
from routes.v1 import bcrypt
from datetime import datetime, timedelta

from models import User, PasswordReset

import uuid, traceback

import sendgrid
from sendgrid.helpers.mail import * 

def close(self):
    self.session.close()

def send_email(subject, sender, recipients, payload, html_file):
    sg = sendgrid.SendGridAPIClient(apikey=app.config['SENDGRID_API_KEY'])
    from_email = Email(sender)
    to_email = Email(recipients)
    subject = subject
    content = Content("text/html", render_template(html_file, data=payload))
    mail = Mail(from_email, subject, to_email, content)
    response = sg.client.mail.send.post(request_body=mail.get())

def Authenticator(self, auth_header):
    if auth_header:
        try:
            auth_token = auth_header.split(" ")[1]
        except IndexError as identifier:
            pass
    raise NotImplementedError

@app.route('/password/reset', methods=['POST'])
def passwordReset():
    email_address = request.json['email']

    user = db.session.query(User).filter_by(email=email_address).filter(User.deletion_marker == None).first()
    if not user:
        responseObject = {
            'message' : 'Enter a vaild email address'
        }
        return make_response(jsonify(responseObject)), 422
    else:    
        #generate a reset token
        token = user.encode_auth_token(user.public_id)
        reset_public_id = str(uuid.uuid4())
        reset_token = PasswordReset(
            public_id = reset_public_id,
            email = email_address,
            token = token.decode(),
            status = 5,
            created_at = datetime.now()
        )
        db.session.add(reset_token)

        try:
            db.session.commit()
            #send an email 
            payload = {
                ## <M69k65y>
                "datenow" : datetime.now().strftime("%d %B %Y"),
                ## </M69k65y>
                'reset_url' : '{}/password/reset/{}'.format(app.config['SERVER_ADDRESS'],reset_public_id), # testing purposes, remove while in production
                'copyright_year' : datetime.now().strftime("%Y")
            }
            sg = sendgrid.SendGridAPIClient(app.config['SENDGRID_API_KEY'])
            from_email = Email(app.config['MAIL_ADDRESS'])
            to_email = Email(email_address)
            subject = 'Password Reset'
            content = Content("text/html", render_template('password_reset.html', data=payload))
            mail = Mail(from_email, subject, to_email, content)
            response = sg.client.mail.send.post(request_body=mail.get())
            # send_email('Password Reset', app.config['MAIL_ADDRESS'], user.email, payload, 'password_reset.html')
            close(db)
            responseObject = {
                'message' : 'Sent an email to {0}. Check the email for instructions.'.format(email_address)
            }
            return make_response(jsonify(responseObject)), 200
        except Exception as identifier:
            db.session.rollback()
            close(db)
            responseObject = {
                'message' : 'An error has occured {0}'.format(str(identifier)),
                'trace_back' : traceback.format_exc()
            }
            return make_response(jsonify(responseObject)), 500

@app.route('/password/reset/<public_id>', methods=['POST'])
def resetPassword(public_id):
    reset_header = request.headers.get('Authorization')

    if reset_header:
        new_password = request.json['new_password']

        ## <Added by M69k65y>
        password = request.json['password']

        if password != new_password:
            responseObject = {
                    "message" : "Please ensure that your new password and the confirmation match. "
                }

            return make_response(jsonify(responseObject)), 422
        
        ## </Added by M69k65y>

        # check validity 
        # query the reset table to check token authenticity

        ## <Removed by M69k65y>
        # There is no Bearer sent by the UI. See Situma.
        # check_token = db.session.query(PasswordReset).filter_by(token=reset_header, public_id=public_id).first()
        ## </Removed by M69k65y>

        ## <Added by M69k65y>
        check_token = db.session.query(PasswordReset).filter_by(public_id=public_id).first()
        ## </Added by M69k65y>

        if check_token:
            email_address, = db.session.query(PasswordReset.email).filter_by(token=check_token.token, public_id=public_id).first()
            user = db.session.query(User).filter_by(email=email_address).first()

            check_token.status = 10 # denotes an expired token
            user.password = bcrypt.generate_password_hash(new_password, app.config['BCRYPT_LOG_ROUNDS']).decode('utf-8')

            try:
                db.session.commit()
                # send and email 
                payload = {
                    'company' : app.config['COMPANY_NAME'],
                    'logo_url' : '',
                    'message' : 'Password has successfully been reset',
                    ## <M69k65y>
                    "datenow" : datetime.now().strftime("%d %B %Y"),
                    'copyright_year' : datetime.now().strftime("%Y")
                    ## </M69k65y>
                }
                send_email('Password Reset', app.config['MAIL_ADDRESS'], user.email, payload, 'success.html')
                close(db)
                responseObject = {
                    'message' : 'Password has successfully been reset'
                }
                return make_response(jsonify(responseObject)), 200
            except Exception as identifier:
                db.session.rollback()
                close(db)
                responseObject = {
                    'message' : 'An error has occured',
                    'error' : str(identifier)
                }
                return make_response(jsonify(responseObject)), 500

        else:
            responseObject = {
                    'message' : 'Password reset token has expired'
                }

            return make_response(jsonify(responseObject)), 422

@app.route('/password/resets')
def fetchPasswordResets():
    resets = PasswordReset.query.order_by(PasswordReset.created_at.desc()).all()
    if not resets:
        return jsonify({'message' : 'No Password resets found'}), 200
    
    output = []
    for reset in resets:
        response = {}
        response['public_id'] = reset.public_id
        response['email'] = reset.email
        response['status'] = reset.status
        response['created_at'] = reset.created_at
        output.append(response)
    return jsonify({'data' : output}), 200


