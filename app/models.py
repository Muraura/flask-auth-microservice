from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

import jwt

from routes.v1 import db, app

class TimestampMixin(object):
    status = db.Column(db.Integer, nullable=False, default="5")
    deletion_marker = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime)
    session_id = db.Column(db.String(200), nullable=True, index=True)

    def serialize(self):
        return {
            'deletion_marker': self.deletion_marker,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status': self.status,
            'session_id' : self.session_id
        }

class Usertype(db.Model, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    public_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=True)
    users = db.relationship('User', backref='usertype', lazy=True)
    tracker = db.relationship('FeatureAssignmentTracker', backref='usertype', lazy=True)

    def serialize(self):
        return {
            'name' : self.name,
            'public_id' : self.public_id,
            'description' : self.public_id
        }

class Gender(db.Model, TimestampMixin):
    __table_name = 'gender'
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(100), nullable=False, index=True, unique=True)
    status = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(255), nullable=False)


class Country(db.Model, TimestampMixin):
    __table_name = 'country'
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(100), nullable=False, index=True, unique=True)
    status = db.Column(db.Integer, nullable=False)
    code = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(255), nullable=False)


class CountryCode(db.Model, TimestampMixin):
    __table_name = 'country_calling_codes'
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(100), nullable=False, index=True, unique=True)
    status = db.Column(db.Integer, nullable=False)
    calling_code = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False, index=True)


""" User Model for storing user related details """
class User(db.Model, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(100), nullable=True, unique=True, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(150), nullable=False)
    user_type = db.Column(db.String(100),db.ForeignKey('usertype.public_id'), nullable=False, index=True)
    remember_token = db.Column(db.String(255), nullable=True)
    access_times = db.relationship('AccessTimes', backref='user', lazy=True)
    user_tracker = db.relationship('FeatureAssignmentTracker', backref='user', lazy=True)
    instituition_id = db.Column(db.String(100), nullable=True)
    tokens = db.relationship('Token', backref='user', lazy=True)
    partner_admin_status = db.Column(db.Integer, nullable=True)
    suspended_by = db.Column(db.String(100), nullable=True)
    unsuspended_by = db.Column(db.String(100), nullable=True)
    suspended_at = db.Column(db.DateTime, nullable=True)
    unsuspended_at = db.Column(db.DateTime, nullable=True)

    def serialize(self):
        return {
        'first_name' : self.first_name,
        'last_name' : self.last_name,
        'phone_number' : self.phone_number,
        'email' : self.email,
        'user_type' : self.user_type,
        'password' : self.password,
        'remember_token' : self.remember_token
    }

    def encode_auth_token(self, user_id):
        """
        Generates the Auth Token
        :return: string
        """
        try:
            payload = {
                'exp': datetime.utcnow() + timedelta(days=1, seconds=5),
                'iat': datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(
                payload,
                app.config.get('SECRET_KEY'),
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(auth_token):
        """
        Validates the auth token
        :param auth_token:
        :return: integer|string
        """
        try:
            payload = jwt.decode(auth_token, app.config['SECRET_KEY'], 'utf-8')
            is_blacklisted_token = BlacklistToken.check_blacklist(auth_token)
            if is_blacklisted_token:
                return 'Token blacklisted. Please log in again.'
            else:
                return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired. Please log in again'
            # return 'Signature expired. Please log in again.'
        except jwt.InvalidTokenError:
            return ''
            # return 'Invalid token. Please log in again.'


class OAuthClient(db.Model, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_public_id = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    secret = db.Column(db.String(100))
    redirect = db.Column(db.Text, nullable=True)
    personal_access_client = db.Column(db.Integer)
    password_client = db.Column(db.Integer)
    revoked = db.Column(db.Integer)

    def serialize(self):
        return{
        'name' : self.name,
        'secret' : self.secret,
        'redirect' : self.redirect,
        'personal_access_client' : self.personal_access_client,
        'password_client' : self.password_client,
        'revoked' : self.revoked
    }

class AccessTimes(db.Model, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(100))
    user_public_id = db.Column(db.String(255), db.ForeignKey('user.public_id'), nullable=True, index=True)
    logged_in_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    logged_out_at = db.Column(db.DateTime, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    loggin_status_code = db.Column(db.Integer, nullable=False)
    ip_address = db.Column(db.String(255), nullable=True)
    browser = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.String(100), nullable=True)
    longitude = db.Column(db.String(100), nullable=True)
    timezone = db.Column(db.String(100), nullable=True)
    country_name = db.Column(db.String(100), nullable=True)
    public_ip = db.Column(db.String(100), nullable=True)

    def to_json(self):
        return {
        'user_public_id' : self.user_public_id,
        'user': '{} {}'.format(self.user.first_name, self.user.last_name),
        'logged_in_at' : self.logged_in_at,
        'logged_out_at' : self.logged_out_at,
        'location' : self.location,
        'loggin_status_code' : self.loggin_status_code,
        'ip_address' : self.ip_address,
        'browser' : self.browser,
        'latitude' : self.latitude,
        'longitude' : self.longitude,
        'timezone' : self.timezone,
        'country_name' : self.country_name,
        'public_id' : self.public_id
    }

class Token(db.Model, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(100), nullable=False)
    user_public_id = db.Column(db.String(100), db.ForeignKey('user.public_id'), index=True)
    token = db.Column(db.Text, nullable=False)
    client_id = db.Column(db.Integer, nullable=True)
    scopes = db.Column(db.Text, nullable=True)
    revoked = db.Column(db.Integer, nullable=True)

    def serialize(self):
        return {
        'user_public_id' : self.user_public_id,
        'client_id' : self.client_id,
        'scopes' : self.scopes,
        'revoked' : self.revoked
    }


class PasswordReset(db.Model, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    token = db.Column(db.Text, nullable=False, unique=True, index=True)
    public_id  = db.Column(db.String(100), nullable=False, index=True, unique=True)

    def serialize(self):
        return {
        'email' : self.email,
        'token' : self.token,
        'public_id' : self.public_id
    }

# class BlokedIP(db.Model, TimestampMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     ip_address = db.Column(db.String(100), nullable=False)
#     public_id  = db.Column(db.String(100), nullable=False, index=True, unique=True)

#     def serialize(self):
#         return {
#         'ip_address' : self.ip_address,
#         'public_id' : self.public_id
#     }


class BlacklistToken(db.Model):
    """
    Token Model for storing JWT tokens
    """
    __tablename__ = 'blacklist_tokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(500), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token
        self.blacklisted_on = datetime.now()

    def __repr__(self):
        return '<id: token: {}'.format(self.token)

    @staticmethod
    def check_blacklist(auth_token):
        # check whether auth token has been blacklisted
        res = BlacklistToken.query.filter_by(token=str(auth_token)).first()
        if res:
            return True
        else:
            return False

class Role(db.Model, TimestampMixin):
    __table_name = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    public_id = db.Column(db.String(255), nullable=False, unique=True, index=True)

    def serialize(self):
        return {
            'name' : self.name,
            'description' : self.description,
            'public_id' : self.public_id,
            'created_at' : self.created_at
        }

class Menu(db.Model, TimestampMixin):
    __table_name = 'menus'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    public_id = db.Column(db.String(255), nullable=False, unique=True, index=True)

    def serialize(self):
        return {
            'name' : self.name,
            'description' : self.description,
            'rating' : self.rating,
            'public_id' : self.public_id,
            'created_at' : self.created_at
        }

class Feature(db.Model, TimestampMixin):
    __table_name = 'features'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    public_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    menu_public_id = db.Column(db.String(255),db.ForeignKey('menu.public_id') ,nullable=False)
    tracker = db.relationship('FeatureAssignmentTracker', backref='feature', lazy=True)
    url = db.Column(db.String(255), nullable=True)
    feature_type = db.Column(db.Integer, nullable=False, default="1")
     
    def serialize(self):
        return {
            'name' : self.name,
            'description' : self.description,
            'public_id' : self.public_id,
            'created_at' : self.created_at,
            'menu_public_id' : self.menu_public_id,
            'url' : self.url
        }

class FeatureRole(db.Model, TimestampMixin):
    __table_name = 'feature_role'
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(255), nullable=False, unique=True, index=True)
    role_public_id = db.Column(db.String(255),db.ForeignKey('usertype.public_id') ,nullable=False)
    feature_public_id = db.Column(db.String(255), db.ForeignKey('feature.public_id'), nullable=False)
    menu_public_id = db.Column(db.String(255),db.ForeignKey('menu.public_id') ,nullable=False)
    
    def serialize(self):
        return {
            'name' : self.name,
            'description' : self.description,
            'public_id' : self.public_id,
            'created_at' : self.created_at,
            'menu_public_id' : self.menu_public_id
        }

class FeatureAssignmentTracker(db.Model, TimestampMixin):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(100), nullable=False)
    feature_public_id = db.Column(db.String(255), db.ForeignKey('feature.public_id'), nullable=False)
    role_public_id = db.Column(db.String(255), db.ForeignKey('usertype.public_id'), nullable=True)
    action = db.Column(db.Integer, nullable=False)
    action_by = db.Column(db.String(200), db.ForeignKey('user.public_id'), nullable=True, index=True)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
    
    def to_json(self):
        return {
            'public_id' : self.public_id,
            'feature_public_id' : self.feature_public_id,
            'feature_name' : self.feature.name,
            'role': self.usertype.name if self.role_public_id else None,
            'action' : self.action,
            'created_at' : self.created_at,
            'action_by' : '{} {}'.format(self.user.first_name, self.user.last_name)
        }

class RequestTracker(db.Model, TimestampMixin):
    __table_name = 'request_tracker'
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(100), nullable=False)
    url = db.Column(db.Text, nullable=False)
    method = db.Column(db.String(100), nullable=False)
    token = db.Column(db.Text, nullable=True)
    user = db.Column(db.String(100), nullable=True)
    success = db.Column(db.Integer, nullable=False)
    server = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=True)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()
    
