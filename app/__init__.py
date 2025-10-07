import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from datetime import datetime

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "main.login"

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

    from app.routes import main as main_bp
    app.register_blueprint(main_bp)

    return app

