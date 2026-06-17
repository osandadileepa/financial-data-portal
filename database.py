import os
from flask_sqlalchemy import SQLAlchemy

# SQLAlchemy instance shared across the app
db = SQLAlchemy()


def get_database_path():
    """
    Return the SQLite database URI.

    Railway provides a persistent disk at /data, so we use RAILWAY_DATABASE_PATH
    when it is set.  For local development we fall back to a local app.db file.
    """
    railway_path = os.environ.get("RAILWAY_DATABASE_PATH")
    if railway_path:
        return f"sqlite:///{railway_path}"
    return "sqlite:///app.db"
