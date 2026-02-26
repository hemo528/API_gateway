from flask import Flask, redirect, url_for
from flask_login import LoginManager
from app.config import Config
from app.models import db, User
from app.routes.auth import auth_bp, init_auth
from app.routes.api import api_bp
from app.routes import main_bp

login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'info'
    
    init_auth(app)
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/v1')
    app.register_blueprint(main_bp)
    
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    with app.app_context():
        db.create_all()
    
    return app
