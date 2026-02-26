from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import db, User, APIKey, UsageRecord, APIProvider
from datetime import datetime, timedelta
import requests
import json
import time

api_bp = Blueprint('api', __name__)

@api_bp.route('/dashboard')
@login_required
def dashboard():
    api_keys = APIKey.query.filter_by(user_id=current_user.id).all()
    usage_today = UsageRecord.query.filter(
        UsageRecord.user_id == current_user.id,
        UsageRecord.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
    ).all()
    
    total_tokens_today = sum(r.total_tokens for r in usage_today)
    total_requests_today = len(usage_today)
    success_requests = len([r for r in usage_today if r.status == 'success'])
    failed_requests = total_requests_today - success_requests
    
    provider_stats = {}
    for record in usage_today:
        if record.provider not in provider_stats:
            provider_stats[record.provider] = {'tokens': 0, 'requests': 0}
        provider_stats[record.provider]['tokens'] += record.total_tokens
        provider_stats[record.provider]['requests'] += 1
    
    recent_records = UsageRecord.query.filter_by(user_id=current_user.id).order_by(
        UsageRecord.created_at.desc()
    ).limit(20).all()
    
    return render_template('dashboard.html', 
                         api_keys=api_keys,
                         total_tokens_today=total_tokens_today,
                         total_requests_today=total_requests_today,
                         success_requests=success_requests,
                         failed_requests=failed_requests,
                         provider_stats=provider_stats,
                         recent_records=recent_records,
                         providers=APIProvider.PROVIDERS,
                         user_api_key=current_user.api_key)

@api_bp.route('/api-keys', methods=['GET'])
@login_required
def api_keys():
    api_keys = APIKey.query.filter_by(user_id=current_user.id).order_by(APIKey.priority.desc()).all()
    return render_template('api_keys.html', api_keys=api_keys, providers=APIProvider.PROVIDERS)

@api_bp.route('/api-keys/add', methods=['POST'])
@login_required
def add_api_key():
    name = request.form.get('name', '').strip()
    provider = request.form.get('provider', '')
    api_key = request.form.get('api_key', '').strip()
    api_secret = request.form.get('api_secret', '').strip()
    base_url = request.form.get('base_url', '').strip()
    model = request.form.get('model', '').strip()
    is_free = request.form.get('is_free') == 'on'
    max_tokens_per_day = request.form.get('max_tokens_per_day', type=int)
    priority = request.form.get('priority', type=int, default=0)
    
    if not name or not provider or not api_key:
        flash('请填写API名称、提供商和API Key', 'error')
        return redirect(url_for('api.api_keys'))
    
    if provider in APIProvider.PROVIDERS:
        provider_info = APIProvider.PROVIDERS[provider]
        if not model:
            model = provider_info.get('default_model', '')
        if not base_url:
            base_url = provider_info.get('default_url', '')
    
    new_api_key = APIKey(
        user_id=current_user.id,
        name=name,
        provider=provider,
        api_key=api_key,
        api_secret=api_secret if api_secret else None,
        base_url=base_url if base_url else None,
        model=model if model else None,
        is_free=is_free,
        max_tokens_per_day=max_tokens_per_day,
        priority=priority
    )
    
    db.session.add(new_api_key)
    db.session.commit()
    
    flash('API Key添加成功', 'success')
    return redirect(url_for('api.api_keys'))

@api_bp.route('/api-keys/<int:key_id>/toggle', methods=['POST'])
@login_required
def toggle_api_key(key_id):
    api_key = APIKey.query.filter_by(id=key_id, user_id=current_user.id).first_or_404()
    api_key.is_active = not api_key.is_active
    db.session.commit()
    
    status = '启用' if api_key.is_active else '停用'
    flash(f'API {status}', 'success')
    return redirect(url_for('api.api_keys'))

@api_bp.route('/api-keys/<int:key_id>/delete', methods=['POST'])
@login_required
def delete_api_key(key_id):
    api_key = APIKey.query.filter_by(id=key_id, user_id=current_user.id).first_or_404()
    db.session.delete(api_key)
    db.session.commit()
    
    flash('API Key已删除', 'success')
    return redirect(url_for('api.api_keys'))

@api_bp.route('/api-keys/<int:key_id>/test', methods=['POST'])
@login_required
def test_api_key(key_id):
    api_key = APIKey.query.filter_by(id=key_id, user_id=current_user.id).first_or_404()
    
    result = test_provider_connection(api_key)
    
    if result['success']:
        flash(f'连接测试成功！响应: {result["message"]}', 'success')
    else:
        flash(f'连接测试失败: {result["message"]}', 'error')
    
    return redirect(url_for('api.api_keys'))

def test_provider_connection(api_key):
    try:
        if api_key.provider == 'openai':
            headers = {
                'Authorization': f'Bearer {api_key.api_key}',
                'Content-Type': 'application/json'
            }
            model = api_key.model or 'gpt-3.5-turbo'
            base_url = api_key.base_url or 'https://api.openai.com/v1'
            response = requests.post(
                f'{base_url}/chat/completions',
                headers=headers,
                json={'model': model, 'messages': [{'role': 'user', 'content': 'Hi'}], 'max_tokens': 5},
                timeout=10
            )
            if response.status_code == 200:
                return {'success': True, 'message': 'API连接正常'}
            else:
                return {'success': False, 'message': f'HTTP {response.status_code}: {response.text[:100]}'}
        
        elif api_key.provider == 'anthropic':
            headers = {
                'x-api-key': api_key.api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json'
            }
            model = api_key.model or 'claude-3-haiku-20240307'
            base_url = api_key.base_url or 'https://api.anthropic.com/v1'
            response = requests.post(
                f'{base_url}/messages',
                headers=headers,
                json={'model': model, 'max_tokens': 5, 'messages': [{'role': 'user', 'content': 'Hi'}]},
                timeout=10
            )
            if response.status_code == 200:
                return {'success': True, 'message': 'API连接正常'}
            else:
                return {'success': False, 'message': f'HTTP {response.status_code}: {response.text[:100]}'}
        
        elif api_key.provider in ['moonshot', 'zhipu', 'deepseek', 'qwen', 'minimax']:
            headers = {
                'Authorization': f'Bearer {api_key.api_key}',
                'Content-Type': 'application/json'
            }
            model = api_key.model or ''
            base_url = api_key.base_url or ''
            response = requests.post(
                f'{base_url}/chat/completions',
                headers=headers,
                json={'model': model, 'messages': [{'role': 'user', 'content': 'Hi'}], 'max_tokens': 5},
                timeout=10
            )
            if response.status_code == 200:
                return {'success': True, 'message': 'API连接正常'}
            else:
                return {'success': False, 'message': f'HTTP {response.status_code}: {response.text[:100]}'}
        
        elif api_key.provider == 'azure':
            headers = {
                'api-key': api_key.api_key,
                'Content-Type': 'application/json'
            }
            base_url = api_key.base_url
            deployment = api_key.model or 'gpt-35-turbo'
            response = requests.post(
                f'{base_url}/openai/deployments/{deployment}/chat/completions?api-version=2024-02-15-preview',
                headers=headers,
                json={'messages': [{'role': 'user', 'content': 'Hi'}], 'max_tokens': 5},
                timeout=10
            )
            if response.status_code == 200:
                return {'success': True, 'message': 'API连接正常'}
            else:
                return {'success': False, 'message': f'HTTP {response.status_code}: {response.text[:100]}'}
        
        else:
            return {'success': False, 'message': f'未支持的提供商: {api_key.provider}'}
    
    except Exception as e:
        return {'success': False, 'message': str(e)}

@api_bp.route('/usage')
@login_required
def usage():
    days = request.args.get('days', type=int, default=7)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    records = UsageRecord.query.filter(
        UsageRecord.user_id == current_user.id,
        UsageRecord.created_at >= start_date
    ).order_by(UsageRecord.created_at.desc()).all()
    
    daily_usage = {}
    for record in records:
        date_key = record.created_at.strftime('%Y-%m-%d')
        if date_key not in daily_usage:
            daily_usage[date_key] = {'tokens': 0, 'requests': 0, 'providers': {}}
        daily_usage[date_key]['tokens'] += record.total_tokens
        daily_usage[date_key]['requests'] += 1
        
        if record.provider not in daily_usage[date_key]['providers']:
            daily_usage[date_key]['providers'][record.provider] = {'tokens': 0, 'requests': 0}
        daily_usage[date_key]['providers'][record.provider]['tokens'] += record.total_tokens
        daily_usage[date_key]['providers'][record.provider]['requests'] += 1
    
    return render_template('usage.html', records=records, daily_usage=daily_usage, days=days)

@api_bp.route('/chat', methods=['POST'])
def chat():
    # 从请求头获取API key
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized: No API key provided'}), 401
    
    user_api_key = auth_header.split(' ')[1]
    
    # 验证API key
    user = User.query.filter_by(api_key=user_api_key).first()
    if not user:
        return jsonify({'error': 'Unauthorized: Invalid API key'}), 401
    
    data = request.get_json()
    messages = data.get('messages', [])
    model = data.get('model')
    temperature = data.get('temperature', 0.7)
    max_tokens = data.get('max_tokens')
    
    api_key = select_api_key(user.id, model)
    
    if not api_key:
        return jsonify({'error': '没有可用的API Key'}), 400
    
    result = call_api(api_key, messages, model, temperature, max_tokens)
    
    if result['success']:
        record_usage(user.id, api_key, result)
        return jsonify(result['response'])
    else:
        if api_key.is_free:
            next_key = get_next_free_api_key(user.id, api_key.id)
            if next_key:
                result = call_api(next_key, messages, model, temperature, max_tokens)
                if result['success']:
                    record_usage(user.id, next_key, result)
                    return jsonify(result['response'])
        
        return jsonify({'error': result['message']}), 500

def select_api_key(user_id, model=None):
    api_keys = APIKey.query.filter_by(user_id=user_id, is_active=True).order_by(APIKey.priority.desc()).all()
    
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    for key in api_keys:
        if key.is_free:
            return key
        
        if key.max_tokens_per_day:
            if key.used_tokens_today < key.max_tokens_per_day:
                return key
            else:
                continue
        
        return key
    
    return None

def get_next_free_api_key(user_id, current_key_id):
    return APIKey.query.filter(
        APIKey.user_id == user_id,
        APIKey.is_active == True,
        APIKey.is_free == True,
        APIKey.id != current_key_id
    ).first()

def call_api(api_key, messages, model=None, temperature=0.7, max_tokens=None):
    start_time = time.time()
    model = model or api_key.model
    
    try:
        if api_key.provider == 'openai':
            headers = {
                'Authorization': f'Bearer {api_key.api_key}',
                'Content-Type': 'application/json'
            }
            base_url = api_key.base_url or 'https://api.openai.com/v1'
            payload = {
                'model': model,
                'messages': messages,
                'temperature': temperature
            }
            if max_tokens:
                payload['max_tokens'] = max_tokens
            
            response = requests.post(
                f'{base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': result,
                    'usage': result.get('usage', {})
                }
            else:
                return {'success': False, 'message': f'API Error: {response.text}'}
        
        elif api_key.provider == 'anthropic':
            headers = {
                'x-api-key': api_key.api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json'
            }
            base_url = api_key.base_url or 'https://api.anthropic.com/v1'
            
            anthropic_messages = []
            for msg in messages:
                anthropic_messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            payload = {
                'model': model,
                'messages': anthropic_messages,
                'max_tokens': max_tokens or 1024,
                'temperature': temperature
            }
            
            response = requests.post(
                f'{base_url}/messages',
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': {
                        'choices': [{
                            'message': {
                                'role': 'assistant',
                                'content': result['content'][0]['text']
                            }
                        }],
                        'usage': {
                            'prompt_tokens': result['usage']['input_tokens'],
                            'completion_tokens': result['usage']['output_tokens'],
                            'total_tokens': result['usage']['input_tokens'] + result['usage']['output_tokens']
                        }
                    },
                    'usage': {
                        'prompt_tokens': result['usage']['input_tokens'],
                        'completion_tokens': result['usage']['output_tokens'],
                        'total_tokens': result['usage']['input_tokens'] + result['usage']['output_tokens']
                    }
                }
            else:
                return {'success': False, 'message': f'API Error: {response.text}'}
        
        elif api_key.provider in ['moonshot', 'deepseek']:
            headers = {
                'Authorization': f'Bearer {api_key.api_key}',
                'Content-Type': 'application/json'
            }
            base_url = api_key.base_url
            payload = {
                'model': model,
                'messages': messages,
                'temperature': temperature
            }
            if max_tokens:
                payload['max_tokens'] = max_tokens
            
            response = requests.post(
                f'{base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': result,
                    'usage': result.get('usage', {})
                }
            else:
                return {'success': False, 'message': f'API Error: {response.text}'}
        
        elif api_key.provider == 'zhipu':
            headers = {
                'Authorization': f'Bearer {api_key.api_key}',
                'Content-Type': 'application/json'
            }
            base_url = api_key.base_url
            payload = {
                'model': model,
                'messages': messages,
                'temperature': temperature
            }
            if max_tokens:
                payload['max_tokens'] = max_tokens
            
            response = requests.post(
                f'{base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': result,
                    'usage': result.get('usage', {})
                }
            else:
                return {'success': False, 'message': f'API Error: {response.text}'}
        
        elif api_key.provider == 'qwen':
            headers = {
                'Authorization': f'Bearer {api_key.api_key}',
                'Content-Type': 'application/json'
            }
            base_url = api_key.base_url
            payload = {
                'model': model,
                'input': {'messages': messages},
                'parameters': {'temperature': temperature}
            }
            if max_tokens:
                payload['parameters']['max_tokens'] = max_tokens
            
            response = requests.post(
                f'{base_url}/services/aigc/text-generation/generation',
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': {
                        'choices': [{
                            'message': {
                                'role': 'assistant',
                                'content': result['output']['text']
                            }
                        }],
                        'usage': result.get('usage', {})
                    },
                    'usage': result.get('usage', {})
                }
            else:
                return {'success': False, 'message': f'API Error: {response.text}'}
        
        elif api_key.provider == 'minimax':
            headers = {
                'Authorization': f'Bearer {api_key.api_key}',
                'Content-Type': 'application/json'
            }
            base_url = api_key.base_url
            payload = {
                'model': model,
                'messages': messages,
                'temperature': temperature
            }
            if max_tokens:
                payload['tokens_to_generate'] = max_tokens
            
            response = requests.post(
                f'{base_url}/text/chatcompletion_v2',
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': result,
                    'usage': result.get('usage', {})
                }
            else:
                return {'success': False, 'message': f'API Error: {response.text}'}
        
        elif api_key.provider == 'azure':
            headers = {
                'api-key': api_key.api_key,
                'Content-Type': 'application/json'
            }
            base_url = api_key.base_url
            deployment = model or 'gpt-35-turbo'
            payload = {
                'messages': messages,
                'temperature': temperature
            }
            if max_tokens:
                payload['max_tokens'] = max_tokens
            
            response = requests.post(
                f'{base_url}/openai/deployments/{deployment}/chat/completions?api-version=2024-02-15-preview',
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'response': result,
                    'usage': result.get('usage', {})
                }
            else:
                return {'success': False, 'message': f'API Error: {response.text}'}
        
        else:
            return {'success': False, 'message': f'未支持的提供商: {api_key.provider}'}
    
    except Exception as e:
        return {'success': False, 'message': str(e)}

def record_usage(user_id, api_key, result):
    request_time = time.time()
    usage = result.get('usage', {})
    
    record = UsageRecord(
        user_id=user_id,
        api_key_id=api_key.id,
        provider=api_key.provider,
        model=api_key.model,
        prompt_tokens=usage.get('prompt_tokens', 0),
        completion_tokens=usage.get('completion_tokens', 0),
        total_tokens=usage.get('total_tokens', 0),
        status='success'
    )
    
    api_key.used_tokens_today += record.total_tokens
    api_key.last_used_at = datetime.utcnow()
    
    db.session.add(record)
    db.session.commit()

@api_bp.route('/reset-usage/<int:key_id>', methods=['POST'])
@login_required
def reset_usage(key_id):
    api_key = APIKey.query.filter_by(id=key_id, user_id=current_user.id).first_or_404()
    api_key.used_tokens_today = 0
    db.session.commit()
    flash(f'{api_key.name} 今日用量已重置', 'success')
    return redirect(url_for('api.api_keys'))
