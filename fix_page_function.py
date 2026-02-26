#!/usr/bin/env python3
"""
修复DeepSeek页面功能脚本
解决"新建DeepSeek页面功能失效"问题
"""

import os
import sys
from pathlib import Path

def fix_page_function():
    """修复页面功能"""
    print("=== DeepSeek页面功能修复工具 ===")
    
    # 1. 检查并修复main.py中的URL导航逻辑
    main_py_path = "/Users/xurongyu/Desktop/01_项目文件夹/appleweb/main.py"
    if os.path.exists(main_py_path):
        print("✅ 找到 main.py 文件")
        
        # 修复navigate_to_url方法
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加更健壮的URL处理逻辑
        if "def navigate_to_url(self):" in content:
            # 替换现有的navigate_to_url方法
            new_method = '''    def navigate_to_url(self):
        """导航到指定URL - 修复版"""
        url_text = self.url_bar.currentText().strip()
        if not url_text:
            QMessageBox.warning(self, "URL为空", "请输入有效的URL地址")
            return
            
        # 增强的URL格式处理
        if not url_text.startswith(('http://', 'https://')):
            if '.' in url_text and not url_text.startswith('www.'):
                url_text = 'https://' + url_text
            elif url_text.startswith('www.'):
                url_text = 'https://' + url_text
            else:
                url_text = 'https://chat.deepseek.com'
        
        try:
            # 尝试解析URL
            from urllib.parse import urlparse
            parsed = urlparse(url_text)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("无效的URL格式")
                
            # 设置URL
            self.browser.setUrl(QUrl(url_text))
            self.statusBar().showMessage(f"正在导航到: {url_text}")
            
        except Exception as e:
            QMessageBox.warning(self, "URL错误", f"无法解析URL: {str(e)}\n请检查URL格式")
            self.statusBar().showMessage("URL格式错误，请输入有效的网址")
    
'''
            # 替换方法
            start_idx = content.find("def navigate_to_url(self):")
            if start_idx > -1:
                end_idx = content.find("\n    def ", start_idx + 1)
                if end_idx == -1:
                    end_idx = len(content)
                
                old_method = content[start_idx:end_idx]
                content = content.replace(old_method, new_method)
                
                with open(main_py_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print("✅ 已修复 main.py 中的URL导航逻辑")
            else:
                print("⚠️ 未找到 navigate_to_url 方法")
        else:
            print("⚠️ main.py 中未找到 navigate_to_url 方法")
    
    # 2. 创建增强版启动脚本
    enhanced_start_script = '''#!/bin/bash
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
'''

    with open("/Users/xurongyu/Desktop/01_项目文件夹/appleweb/start_fixed.sh", 'w') as f:
        f.write(enhanced_start_script)
    os.chmod("/Users/xurongyu/Desktop/01_项目文件夹/appleweb/start_fixed.sh", 0o755)
    print("✅ 已创建增强版启动脚本: start_fixed.sh")

    # 3. 创建诊断命令
    diagnostic_cmd = '''# 诊断命令
echo "=== 页面功能诊断 ==="
echo "1. 检查端口: lsof -i :8766"
echo "2. 检查进程: ps aux | grep python"
echo "3. 测试API: curl http://127.0.0.1:8766/api/tags"
echo "4. 测试页面: python debug_tool.py"
'''
    
    with open("/Users/xurongyu/Desktop/01_项目文件夹/appleweb/diagnostic_commands.txt", 'w') as f:
        f.write(diagnostic_cmd)
    print("✅ 已创建诊断命令文件")

    print("\n=== 修复完成 ===")
    print("请执行以下步骤:")
    print("1. 运行: ./start_fixed.sh 启动修复版程序")
    print("2. 或直接运行: python main.py")
    print("3. 如果仍有问题，请运行: python page_diagnostic_tool.py 进行详细诊断")

if __name__ == "__main__":
    fix_page_function()