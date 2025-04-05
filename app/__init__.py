from flask import Flask

def start_app():
    app = Flask(__name__, template_folder='views')
    app.config.from_object('config.Config')
    
    from app.controllers import main_controller
    app.register_blueprint(main_controller.app)
    
    return app