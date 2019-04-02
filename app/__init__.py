import logging

import graypy
import sentry_sdk
from flask import Flask
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from tabulate import tabulate

from app.__meta__ import __api_name__, __version__
from app.config import config
from app.database import db
from app.extensions import cors, migrate
from app.oauth2 import config_oauth


def init_extensions(app):
    db.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}, })
    config_oauth(app)
    migrate.init_app(app, db)


def init_graylog(app):
    GRAYLOG_HOST = app.config.get('GRAYLOG_HOST')
    GRAYLOG_PORT = app.config.get('GRAYLOG_PORT')

    if GRAYLOG_HOST and GRAYLOG_PORT:
        app_name = app.config.get('APPLICATION_NAME') or 'flask.app'
        handler = graypy.GELFHandler(GRAYLOG_HOST, GRAYLOG_PORT, facility=app_name)
        app.logger.addHandler(handler)


def init_sentry(app):
    SENTRY_DSN = app.config.get('SENTRY_DSN')
    if SENTRY_DSN:
        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR,
        )

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[FlaskIntegration(), sentry_logging]
        )


def init_blueprint(app):
    @app.teardown_request
    def teardown_request(exception):
        if exception:
            db.session.rollback()
        db.session.remove()

    from .main import main as main_bp
    app.register_blueprint(main_bp, url_prefix='/')

    from .api import api as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from .api import oauth as oauth_bp
    app.register_blueprint(oauth_bp, url_prefix='/oauth')

    from .swagger import swagger_bp
    app.register_blueprint(swagger_bp, url_prefix='/swagger')


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    cfg = []
    for k in sorted(app.config.keys()):
        cfg.append([k, app.config.get(k)])

    app.logger.info(tabulate(cfg))

    init_extensions(app)
    init_blueprint(app)
    init_sentry(app)
    init_graylog(app)

    return app
