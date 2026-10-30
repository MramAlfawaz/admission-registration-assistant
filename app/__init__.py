"""Create the Flask application."""
import logging
from flask import Flask
from config.config import config_by_name


def create_app(config_name="default"):
    """Build and configure the application."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    logging.basicConfig(
        level=app.config["LOG_LEVEL"],
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
    )
    from app.routes import bp
    app.register_blueprint(bp)
    return app
