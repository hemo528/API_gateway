# API网关平台 - 部署文档

## 目录
- [环境要求](#环境要求)
- [快速部署](#快速部署)
- [详细部署步骤](#详细部署步骤)
- [Docker部署](#docker部署)
- [配置说明](#配置说明)
- [API使用说明](#api使用说明)
- [常见问题](#常见问题)
- [维护指南](#维护指南)

---

## 环境要求

### 基础环境
- **Python**: 3.8 或更高版本
- **操作系统**: Windows / Linux / macOS
- **内存**: 至少 512MB RAM
- **磁盘空间**: 至少 200MB

### Python依赖
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-Bcrypt==1.0.1
requests==2.31.0
python-dotenv==1.0.0
Werkzeug==3.0.1
gunicorn==21.2.0
```

### 可选环境
- **Docker**: 20.10 或更高版本（用于Docker部署）
- **Docker Compose**: 2.0 或更高版本

---

## 快速部署

### Windows
```bash
双击运行 deploy.bat
```

### Linux/Mac
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## 详细部署步骤

### 1. 克隆或下载项目
```bash
git clone <repository-url>
cd API_gateway
```

### 2. 创建虚拟环境

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 启动服务

**开发模式:**
```bash
python run.py
```

**生产模式:**
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 "app:create_app()"
```

### 5. 访问应用
打开浏览器访问: http://127.0.0.1:5000

---

## Docker部署

### 1. 构建镜像
```bash
docker build -t api-gateway .
```

### 2. 使用Docker Compose启动
```bash
docker-compose up -d
```

### 3. 查看日志
```bash
docker-compose logs -f
```

### 4. 停止服务
```bash
docker-compose down
```

---

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| SECRET_KEY | Flask密钥 | dev-secret-key |
| SQLALCHEMY_DATABASE_URI | 数据库连接串 | sqlite:///api_gateway.db |

### 配置文件

编辑 `app/config.py`:
```python
class Config:
    SECRET_KEY = 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///your_database.db'
```

### 生产环境建议

1. **更改SECRET_KEY**:
```python
import os
SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
```

2. **使用MySQL/PostgreSQL**:
```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@localhost/dbname'
```

3. **启用HTTPS**

---

## API使用说明

### 接口地址
```
http://127.0.0.1:5000/v1/chat
```

### 认证方式
在请求头中添加API Key:
```
Authorization: Bearer sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 请求示例

**Python:**
```python
import requests

url = "http://127.0.0.1:5000/v1/chat"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer sk-您的API密钥"
}
data = {
    "messages": [
        {"role": "user", "content": "你好"}
    ],
    "model": "moonshot-v1-8k"
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

**curl:**
```bash
curl -X POST http://127.0.0.1:5000/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-您的API密钥" \
  -d '{"messages": [{"role": "user", "content": "你好"}]}'
```

### 响应格式
```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "回复内容"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

---

## 常见问题

### Q1: 启动时报错 "No module named 'flask'"
**解决:** 确保已激活虚拟环境并安装了依赖
```bash
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Q2: 数据库错误 "no such column"
**解决:** 删除旧数据库文件，让系统重新创建
```bash
del instance\api_gateway.db  # Windows
rm -f instance/api_gateway.db  # Linux/Mac
```

### Q3: 端口被占用
**解决:** 使用其他端口
```bash
# 修改 run.py 中的端口
app.run(host='0.0.0.0', port=8080)
```

### Q4: 中文编码错误
**解决:** 使用 `json=data` 参数而不是 `json=data`
```python
response = requests.post(url, headers=headers, json=data)
```

### Q5: API调用返回401错误
**解决:** 检查API Key是否正确，确保在请求头中正确传递

---

## 维护指南

### 1. 备份数据库
```bash
# 定期备份
copy instance\api_gateway.db backup\api_gateway_backup.db
```

### 2. 查看日志

**开发模式:** 日志直接输出到控制台

**生产模式:**
```bash
# 使用gunicorn日志
gunicorn --access-logfile access.log --error-logfile error.log "app:create_app()"
```

### 3. 更新代码
```bash
# 拉取最新代码
git pull

# 重启服务
# 先停止旧服务
# 然后重新启动
python run.py  # 开发
gunicorn ...  # 生产
```

### 4. 监控

建议使用以下工具监控服务:
- **PM2** (Node.js) - 进程管理
- **Supervisor** - 进程守护
- **systemd** (Linux) - 系统服务

### 5. 安全建议

1. 定期更改SECRET_KEY
2. 使用HTTPS
3. 限制数据库访问
4. 定期备份数据
5. 监控异常请求

---

## 技术支持

如遇到问题，请检查:
1. Python版本是否满足要求 (3.8+)
2. 所有依赖是否正确安装
3. 端口5000是否被占用
4. 数据库文件是否可写

---

## 许可证

MIT License
