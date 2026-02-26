from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from app.models import db, User
from datetime import datetime
import secrets
import string

def generate_api_key():
    alphabet = string.ascii_letters + string.digits
    return 'sk-' + ''.join(secrets.choice(alphabet) for _ in range(32))

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

def init_auth(app):
    bcrypt.init_app(app)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('api.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('login.html')
        
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('api.dashboard'))
        else:
            flash('用户名或密码错误', 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('api.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not email or not password:
            flash('请填写所有必填字段', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('密码长度至少6位', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return render_template('register.html')
        
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        api_key = generate_api_key()
        new_user = User(username=username, email=email, password_hash=password_hash, api_key=api_key)
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-api-key', methods=['POST'])
@login_required
def reset_api_key():
    new_api_key = generate_api_key()
    current_user.api_key = new_api_key
    db.session.commit()
    flash(f'API Key已重置为: {new_api_key}', 'success')
    return redirect(url_for('api.dashboard'))
