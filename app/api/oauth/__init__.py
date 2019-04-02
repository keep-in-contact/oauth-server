import json

from authlib.flask.oauth2 import current_token
from flask import jsonify, g, current_app, request

from .. import oauth
from ...oauth2 import authorization, require_oauth


@oauth.route('/token', methods=['POST'])
def issue_token():
    """
    access_token 발급
    OAuth2.0 스펙의 access_token 발급
    ---
    consumes:
      - application/x-www-form-urlencoded
    parameters:
      - in: formData
        name: username
        schema:
          type: string
      - in: formData
        name: password
        schema:
          type: string
      - in: formData
        name: client_id
        schema:
          type: string
      - in: formData
        name: client_secret
        schema:
          type: string
      - in: formData
        name: scope
        schema:
          type: string
    tags:
      - Auth
    responses:
      200:
        description: OK
        schema:
          type: object
          properties:
            access_token:
              type: string
            refresh_token:
              type: string
    """
    current_app.logger.info(request.form)
    resp = authorization.create_token_response()

    data = json.loads(resp.data)
    if 'access_token' not in data:
        return resp

    user = g.current_user

    profile = {
        'id': user.id,
        'email': user.username,
        'name': user.name,
    }

    data = dict(**data, profile=profile)
    resp.data = json.dumps(data)

    return resp


@oauth.route('/revoke', methods=['POST'])
def revoke_token():
    return authorization.create_endpoint_response('revocation')


