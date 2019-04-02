import requests
from authlib.flask.oauth2 import AuthorizationServer, ResourceProtector
from authlib.flask.oauth2.sqla import (
    create_query_client_func,
    create_save_token_func,
    create_revocation_endpoint,
)
from authlib.specs.rfc6749 import grants
from facebook import GraphAPI
from flask import current_app, g
from werkzeug.security import gen_salt

from .database import db
from .models import (
    User,
    OAuth2Client,
    OAuth2AuthorizationCode,
    OAuth2Token,
    encode_password)


class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):
    def create_authorization_code(self, client, user, request):
        code = gen_salt(48)
        item = OAuth2AuthorizationCode(
            code=code,
            client_id=client.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            user_id=user.id,
        )
        db.session.add(item)
        db.session.commit()
        return code

    def parse_authorization_code(self, code, client):
        item = db.session.query(OAuth2AuthorizationCode).filter_by(
            code=code, client_id=client.client_id).first()
        if item and not item.is_expired():
            return item

    def delete_authorization_code(self, authorization_code):
        db.session.delete(authorization_code)
        db.session.commit()

    def authenticate_user(self, authorization_code):
        return db.session.query(User).get(authorization_code.user_id)


class PasswordGrant(grants.ResourceOwnerPasswordCredentialsGrant):
    def authenticate_user(self, username, password):
        if username.lower() == 'facebook':
            token = password
            graph = GraphAPI(token)
            try:
                social_id = graph.get_object('me')['id']
                current_app.logger.debug(f'facebook.social_id: {social_id}')
                user = db.session.query(User).filter_by(social_class='FB', social_id=social_id).first()
                g.current_user = user

                return user
            except:
                current_app.logger.exception(token)
                return None

        elif username.lower() == 'kakaotalk':
            token = password
            try:
                url = 'https://kapi.kakao.com/v2/user/me'
                resp = requests.get(url, headers={'Authorization': f'Bearer {token}'})
                social_id = resp.json()['id']
                current_app.logger.debug(f'kakaotalk.social_id: {social_id}')
                user = db.session.query(User).filter_by(social_class='KT', social_id=social_id).first()
                g.current_user = user

                return user
            except:
                current_app.logger.exception(token)
                return None

        current_app.logger.info(f'oauth2 username: {username}')
        pass_encode = encode_password(password, current_app.config.get('PASSWORD_SALT'))
        user = db.session.query(User).filter_by(username=username, password=pass_encode).first()
        if not user:
            return None
        else:
            g.current_user = user
            return user


class RefreshTokenGrant(grants.RefreshTokenGrant):
    def authenticate_refresh_token(self, refresh_token):
        token = db.session.query(OAuth2Token).filter_by(refresh_token=refresh_token).first()
        if token and not token.is_refresh_token_expired():
            return token

    def authenticate_user(self, credential):
        g.current_user = user = db.session.query(User).get(credential.user_id)
        return user


authorization = AuthorizationServer()
require_oauth = ResourceProtector()


def config_oauth(app):
    query_client = create_query_client_func(db.session, OAuth2Client)
    save_token = create_save_token_func(db.session, OAuth2Token)
    authorization.init_app(
        app, query_client=query_client, save_token=save_token)

    # support all grants
    authorization.register_grant(grants.ImplicitGrant)
    authorization.register_grant(grants.ClientCredentialsGrant)
    authorization.register_grant(AuthorizationCodeGrant)
    authorization.register_grant(PasswordGrant)
    authorization.register_grant(RefreshTokenGrant)

    # support revocation
    revocation_cls = create_revocation_endpoint(db.session, OAuth2Token)
    authorization.register_endpoint(revocation_cls)
