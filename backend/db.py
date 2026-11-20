from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        # Check connection and create tables if using SQLite or if tables not created yet
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"Note on db.create_all(): {e}")
