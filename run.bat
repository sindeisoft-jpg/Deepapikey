@echo off
REM DeepSeek Qt浏览器应用启动脚本（Windows）

echo DeepSeek Qt浏览器应用启动脚本
echo.

REM 检查是否在虚拟环境中运行
if "%VIRTUAL_ENV%"=="" (
    echo 未检测到虚拟环境，尝试激活...
    
    REM 检查是否存在虚拟环境
    if exist "venv\Scripts\activate.bat" (
        call venv\Scripts\activate.bat
        echo 虚拟环境已激活
    ) else (
        echo 警告：未找到虚拟环境，将使用系统Python环境
        echo 建议先创建虚拟环境：python -m venv venv
    )
)

REM 检查Python版本
echo 检查Python版本...
python --version

REM 检查PyQt6是否安装
echo 检查PyQt6依赖...
python -c "import PyQt6; print('PyQt6已安装')" 2>nul
if errorlevel 1 (
    echo PyQt6未安装，正在安装...
    pip install PyQt6 PyQt6-WebEngine
)

REM 运行应用
echo 启动DeepSeek Qt浏览器应用...
python main.py

pause