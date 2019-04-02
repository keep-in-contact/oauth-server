import os


class Config:
    APPLICATION_NAME = 'oauth-server'
    CONFIG_NAME = 'base'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    JWT_SECRET_KEY = '<<JWT_SECRET_KEY>>'
    SECRET_KEY = '<<SECRET_KEY>>'
    PASSWORD_SALT = "<<PASSWORD_SALT>>"

    OAUTH2_REFRESH_TOKEN_GENERATOR = True
    OAUTH2_TOKEN_EXPIRES_IN = {
        'password': 8640000,
        'client_credentials': 8640000,
    }

    SENTRY_DSN = None
    GRAYLOG_HOST = None
    GRAYLOG_PORT = None

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    APPLICATION_NAME = 'oauth-server-dev'
    CONFIG_NAME = 'development'

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = \
        os.environ.get('DEV_DATABASE_URL') or \
        'mysql+mysqlconnector://user:secret@localhost:3306/oauth_server_dev'

    SENTRY_DSN = os.environ.get('DEV_SENTRY_DSN')
    GRAYLOG_HOST = os.environ.get('DEV_GRAYLOG_HOST') or None
    GRAYLOG_PORT = os.environ.get('DEV_GRAYLOG_PORT') or 12201


class TestingConfig(Config):
    CONFIG_NAME = 'testing'

    TESTING = True
    SQLALCHEMY_DATABASE_URI = \
        os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    APPLICATION_NAME = 'oauth-server-prod'
    CONFIG_NAME = 'production'

    SQLALCHEMY_DATABASE_URI = \
        os.environ.get('DATABASE_URL') or \
        'mysql+mysqlconnector://user:secret@localhost:3306/oauth_server'

    SENTRY_DSN = os.environ.get('SENTRY_DSN') or None
    GRAYLOG_HOST = os.environ.get('GRAYLOG_HOST') or None
    GRAYLOG_PORT = os.environ.get('GRAYLOG_PORT') or 12201

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)


class HerokuConfig(ProductionConfig):
    SSL_REDIRECT = True if os.environ.get('DYNO') else False

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # handle reverse proxy server headers
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


class DockerConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.INFO)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'docker': DockerConfig,
    'unix': UnixConfig,
    'default': DevelopmentConfig
}
