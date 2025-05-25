from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from app.config import Config

db = SQLAlchemy()
migrate = Migrate()

def start_app(config_class=Config):
   app = Flask(__name__, template_folder='views')
   app.config.from_object(config_class)
   
   # Inicializa extensões
   db.init_app(app)
   migrate.init_app(app, db)
   
   # Registra blueprints
   from app.controllers.main_controller import main_bp
   from app.controllers.auth_controller import auth_bp
   from app.controllers.view_controller import view_bp

   app.register_blueprint(main_bp)
   app.register_blueprint(auth_bp)
   app.register_blueprint(view_bp)
   
#   from app.middlewares.auth_middleware import setup_auth_middleware
#   setup_auth_middleware(app)
   
   return app