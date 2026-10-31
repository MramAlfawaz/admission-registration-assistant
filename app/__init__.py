"""Create the Flask application."""
import logging

from flask import Flask

from config.config import config_by_name


def create_app(config_name="default"):
    """Build and configure the application."""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    app.config["JSON_AS_ASCII"] = False
    app.json.ensure_ascii = False
    app.extensions["config_class"] = config_by_name[config_name]
    logging.basicConfig(
        level=app.config["LOG_LEVEL"],
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler("app.log")],
    )
    from app.models.seed import set_seed

    set_seed(app.config["SEED"])
    from app.routes import bp
    app.register_blueprint(bp)
    return app
