# _*_ coding: utf-8 _*_
import os

from flask import Flask
from flask_bootstrap import Bootstrap


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_mapping(
        SECRET_KEY=b"c7fe8e8ec431bc70be4ebf2497fb62a64c846468218206f99714674495d8fdf2"
    )
    Bootstrap(app)

    if test_config is None:
        app.config.from_pyfile('config.py')
        print(app.config)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import eg
    app.register_blueprint(eg.bp)

    return app
