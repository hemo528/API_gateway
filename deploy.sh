#!/bin/bash

echo "========================================"
echo "   API网关平台 - 一键部署脚本"
echo "========================================"
echo ""

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

if [ -d "venv" ]; then
    echo "[INFO] 发现虚拟环境，删除旧环境..."
    rm -rf venv
fi

echo "[STEP 1] 创建虚拟环境..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "[ERROR] 创建虚拟环境失败，请确保已安装Python 3.8+"
    exit 1
fi
echo "[OK] 虚拟环境创建成功"

echo ""
echo "[STEP 2] 激活虚拟环境..."
source venv/bin/activate
echo "[OK] 虚拟环境已激活"

echo ""
echo "[STEP 3] 安装依赖包..."
pip install --upgrade pip
pip install flask flask-sqlalchemy flask-login flask-bcrypt requests python-dotenv werkzeug
if [ $? -ne 0 ]; then
    echo "[ERROR] 安装依赖失败"
    exit 1
fi
echo "[OK] 依赖安装成功"

echo ""
echo "[STEP 4] 检查配置文件..."
if [ ! -f "app/config.py" ]; then
    echo "[ERROR] 配置文件不存在"
    exit 1
fi
echo "[OK] 配置文件检查通过"

echo ""
echo "========================================"
echo "   部署完成！"
echo "========================================"
echo ""
echo "启动命令: ./venv/bin/python run.py"
echo "后台运行: nohup ./venv/bin/python run.py &"
echo "默认地址: http://127.0.0.1:5000"
echo ""
echo "是否现在启动服务? (y/n)"
read -r answer
if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
    echo "[INFO] 启动服务..."
    ./venv/bin/python run.py
fi
