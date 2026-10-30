"""Expose the production application."""
from app import create_app

app = create_app("production")
