from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    api_key = db.Column(db.String(256), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    api_keys = db.relationship('APIKey', backref='user', lazy=True, cascade='all, delete-orphan')
    usage_records = db.relationship('UsageRecord', backref='user', lazy=True, cascade='all, delete-orphan')

class APIKey(db.Model):
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    api_key = db.Column(db.String(256), nullable=False)
    api_secret = db.Column(db.String(256), nullable=True)
    base_url = db.Column(db.String(256), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_free = db.Column(db.Boolean, default=False)
    priority = db.Column(db.Integer, default=0)
    max_tokens_per_day = db.Column(db.Integer, nullable=True)
    used_tokens_today = db.Column(db.Integer, default=0)
    last_used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    usage_records = db.relationship('UsageRecord', backref='api_key', lazy=True, cascade='all, delete-orphan')

class UsageRecord(db.Model):
    __tablename__ = 'usage_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'), nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(100), nullable=True)
    prompt_tokens = db.Column(db.Integer, default=0)
    completion_tokens = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    request_time = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='success')
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class APIProvider:
    PROVIDERS = {
        'openai': {
            'name': 'OpenAI',
            'default_model': 'gpt-3.5-turbo',
            'default_url': 'https://api.openai.com/v1'
        },
        'anthropic': {
            'name': 'Anthropic',
            'default_model': 'claude-3-haiku-20240307',
            'default_url': 'https://api.anthropic.com/v1'
        },
        'google': {
            'name': 'Google Gemini',
            'default_model': 'gemini-pro',
            'default_url': 'https://generativelanguage.googleapis.com/v1'
        },
        'azure': {
            'name': 'Azure OpenAI',
            'default_model': 'gpt-35-turbo',
            'default_url': ''
        },
        'local': {
            'name': 'Local/Other',
            'default_model': '',
            'default_url': 'http://localhost:8000/v1'
        },
        'moonshot': {
            'name': 'Moonshot AI',
            'default_model': 'moonshot-v1-8k',
            'default_url': 'https://api.moonshot.cn/v1'
        },
        'zhipu': {
            'name': '智谱AI',
            'default_model': 'glm-4',
            'default_url': 'https://open.bigmodel.cn/api/paas/v4'
        },
        'deepseek': {
            'name': 'DeepSeek',
            'default_model': 'deepseek-chat',
            'default_url': 'https://api.deepseek.com/v1'
        },
        'qwen': {
            'name': '阿里Qwen',
            'default_model': 'qwen-turbo',
            'default_url': 'https://dashscope.aliyuncs.com/api/v1'
        },
        'minimax': {
            'name': 'MiniMax',
            'default_model': 'abab6.5s-chat',
            'default_url': 'https://api.minimax.chat/v1'
        }
    }
