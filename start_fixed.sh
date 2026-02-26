#!/bin/bash
# 增强版启动脚本 - 解决页面功能失效问题

echo "启动DeepSeek Qt浏览器..."

# 激活虚拟环境
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 设置环境变量
export DEEPSEEK_API_PORT=8766
export QTWEBENGINE_CHROMIUM_FLAGS="--enable-features=NetworkService,NetworkServiceInProcess"

# 启动服务
echo "启动API服务..."
python main.py &
MAIN_PID=$!

# 等待服务启动
sleep 3

# 检查服务是否启动成功
if lsof -i :8766 >/dev/null 2>&1; then
    echo "✅ API服务启动成功 (端口 8766)"
else
    echo "❌ API服务启动失败"
    kill $MAIN_PID 2>/dev/null
    exit 1
fi

# 启动主程序
echo "启动主程序..."
wait $MAIN_PID

echo "程序已退出"
