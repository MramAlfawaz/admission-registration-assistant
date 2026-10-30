"""Define HTTP routes."""
from flask import Blueprint, jsonify

bp = Blueprint("main", __name__)


@bp.get("/health")
def health():
    """Return service status."""
    return jsonify({"results": [{"status": "ok"}], "errors": []})
