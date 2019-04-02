from flask import Blueprint, jsonify

from ..__meta__ import __api_name__, __version__

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return jsonify({
        'name': __api_name__,
        'version': __version__,
    })
