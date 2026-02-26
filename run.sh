#!/bin/bash

# DeepSeek Qt浏览器应用启动脚本

# 检查是否在虚拟环境中运行
if [ -z "$VIRTUAL_ENV" ]; then
    echo "未检测到虚拟环境，尝试激活..."
    
    # 检查是否存在虚拟环境
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "虚拟环境已激活"
    else
        echo "警告：未找到虚拟环境，将使用系统Python环境"
        echo "建议先创建虚拟环境：python3 -m venv venv"
    fi
fi

# 检查Python版本
echo "检查Python版本..."
python3 --version

# 检查PyQt6是否安装
echo "检查PyQt6依赖..."
python3 -c "import PyQt6; print('PyQt6已安装')" 2>/dev/null || {
    echo "PyQt6未安装，正在安装..."
    pip install PyQt6 PyQt6-WebEngine
}

# 运行应用
echo "启动DeepSeek Qt浏览器应用..."
python3 main.py