from flask import Blueprint, jsonify, current_app, url_for, request
from flask_swagger import swagger

from ..__meta__ import __version__

swagger_bp = Blueprint('swagger', __name__)


@swagger_bp.route('/spec')
def spec():
    swag = swagger(current_app)

    swag['info'] = {
        'version': __version__,
        'title': "OAuth2.0 Server",
        'description': '',
    }

    swag['host'] = request.host
    swag['basePath'] = url_for('main.index', ).rstrip('/')
    swag['securityDefinitions'] = {
        'oauth2': {
            'type': 'oauth2',
            'tokenUrl': url_for('oauth.issue_token', _external=True),
            'flow': 'password',
            'scopes': {
                'profile': 'default',
            }
        },
        'token_auth': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Bearer <<OAUTH_TOKEN>>',
        }

    }

    return jsonify(swag)
