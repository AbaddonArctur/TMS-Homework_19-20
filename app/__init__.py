import os
from flask import Flask
from config import Config
from datetime import datetime
from app.extensions import db, migrate, login_manager
from app.routes import main as main_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @app.context_processor
    def inject_current_year():
        return {'current_year': datetime.utcnow().year}

    app.register_blueprint(main_bp)

    return app