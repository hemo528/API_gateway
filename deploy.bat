@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo    API网关平台 - 一键部署脚本
echo ========================================
echo.

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if exist "venv" (
    echo [INFO] 发现虚拟环境，删除旧环境...
    rmdir /s /q "venv"
)

echo [STEP 1] 创建虚拟环境...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] 创建虚拟环境失败，请确保已安装Python 3.8+
    pause
    exit /b 1
)
echo [OK] 虚拟环境创建成功

echo.
echo [STEP 2] 激活虚拟环境...
call venv\Scripts\activate.bat
echo [OK] 虚拟环境已激活

echo.
echo [STEP 3] 安装依赖包...
pip install --upgrade pip
pip install flask flask-sqlalchemy flask-login flask-bcrypt requests python-dotenv werkzeug
if errorlevel 1 (
    echo [ERROR] 安装依赖失败
    pause
    exit /b 1
)
echo [OK] 依赖安装成功

echo.
echo [STEP 4] 检查配置文件...
if not exist "app\config.py" (
    echo [ERROR] 配置文件不存在
    pause
    exit /b 1
)
echo [OK] 配置文件检查通过

echo.
echo ========================================
echo    部署完成！
echo ========================================
echo.
echo 启动命令: venv\Scripts\python run.py
echo 默认地址: http://127.0.0.1:5000
echo.
echo 按任意键启动服务...
pause >nul

echo [INFO] 启动服务...
venv\Scripts\python run.py
