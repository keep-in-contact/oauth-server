from flask import Blueprint

api = Blueprint('api', __name__)
oauth = Blueprint('oauth', __name__)


@api.route('/v1.0/ping')
def ping():
    return jsonify({'ok': True})


from .oauth import *
