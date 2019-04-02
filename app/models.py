import time
from datetime import datetime

from authlib.flask.oauth2.sqla import (
    OAuth2ClientMixin,
    OAuth2AuthorizationCodeMixin,
    OAuth2TokenMixin,
)
from flask import current_app

from .database import db


def encode_password(password, salt):
    import hmac
    import hashlib
    import base64

    if isinstance(salt, str):
        salt = salt.encode('utf-8')

    if isinstance(password, str):
        password = password.encode('utf-8')

    dig = hmac.new(salt, msg=password, digestmod=hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column('id', db.Integer, primary_key=True)
    email = db.Column('email', db.String(255), unique=True)
    name = db.Column('name', db.String(255), )
    password = db.Column('password', db.String(255), )
    created_at = db.Column('created_at', db.DateTime, default=datetime.utcnow)

    def __str__(self):
        return self.email

    def get_user_id(self):
        return self.id

    def get_roles(self):
        return [role.name for role in self.roles]

    def check_password(self, password):
        encoded_pw = encode_password(password, current_app.config.get('PASSWORD_SALT'))
        return self.password == encoded_pw


class OAuth2Client(db.Model, OAuth2ClientMixin):
    __tablename__ = 'oauth2_client'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ))
    user = db.relationship('User')


class OAuth2AuthorizationCode(db.Model, OAuth2AuthorizationCodeMixin):
    __tablename__ = 'oauth2_code'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ))
    user = db.relationship('User')


class OAuth2Token(db.Model, OAuth2TokenMixin):
    __tablename__ = 'oauth2_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ))
    user = db.relationship('User')

    def is_refresh_token_expired(self):
        expires_at = self.issued_at + self.expires_in * 2
        return expires_at < time.time()
