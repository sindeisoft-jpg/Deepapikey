#!/usr/bin/env python3
"""
CLINE集成测试脚本
验证API能否生成代码文件并解决权限问题
"""

import os
import json
import urllib.request
from datetime import datetime

def test_cline_integration():
    """完整的CLINE集成测试"""
    print("=== CLINE集成测试开始 ===")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"项目目录: /Users/xurongyu/Desktop/01_项目文件夹/appleweb")
    
    # 测试1: API连接性
    print("\n🔍 测试1: API连接性")
    try:
        req = urllib.request.Request("http://127.0.0.1:8765/api/tags")
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.getcode() == 200:
                data = response.read().decode('utf-8')
                models = json.loads(data).get('models', [])
                print(f"✅ API连接成功，发现 {len(models)} 个模型:")
                for model in models:
                    print(f"  - {model.get('name')}")
            else:
                print(f"❌ API连接失败: {response.getcode()}")
    except Exception as e:
        print(f"❌ API连接异常: {e}")
        return False
    
    # 测试2: 代码生成能力
    print("\n📝 测试2: 代码生成能力")
    try:
        url = "http://127.0.0.1:8765/v1/chat/completions"
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "user", 
                    "content": "写一个Python的hello world程序，要求包含Shebang行、UTF-8编码声明、函数封装主逻辑、标准的if __name__ == '__main__'入口点"
                }
            ]
        }
        
        req = urllib.request.Request(url)
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(payload).encode('utf-8')
        
        with urllib.request.urlopen(req, timeout=180) as response:
            if response.getcode() == 200:
                data = response.read().decode('utf-8')
                content = json.loads(data)
                message_content = content.get('message', {}).get('content', '')
                
                print(f"✅ API响应成功")
                print(f"内容长度: {len(message_content)} 字符")
                
                # 检查代码块
                if '```python' in message_content:
                    print("✅ 发现Python代码块")
                    
                    # 尝试保存文件
                    filename = f"test_hello_{datetime.now().strftime('%H%M%S')}.py"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(message_content)
                    print(f"✅ 成功创建文件: {filename}")
                    
                    # 验证文件
                    with open(filename, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        print(f"文件大小: {len(file_content)} 字符")
                        
                    # 检查是否包含关键元素
                    required_elements = ['#!/usr/bin/env python3', '# -*- coding: utf-8 -*-', 'def main():', 'if __name__ == "__main__":']
                    found_elements = []
                    for element in required_elements:
                        if element in file_content:
                            found_elements.append(element)
                    
                    print(f"找到的关键元素: {found_elements}")
                    
                    if len(found_elements) >= 3:
                        print("✅ 代码结构完整")
                        return True
                    else:
                        print("⚠️ 代码结构不完整")
                        return False
                else:
                    print("❌ 未发现代码块格式")
                    print(f"响应内容预览: {message_content[:200]}...")
                    return False
                    
            else:
                print(f"❌ 请求失败: {response.getcode()}")
                return False
                
    except Exception as e:
        print(f"❌ 代码生成异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    success = test_cline_integration()
    
    print(f"\n=== 测试结果 ===")
    if success:
        print("🎉 CLINE集成测试通过！")
        print("✅ API服务正常")
        print("✅ 代码生成正常")
        print("✅ 文件创建正常")
    else:
        print("❌ CLINE集成测试失败")
        print("请检查:")
        print("1. API服务是否在8765端口运行")
        print("2. 工作目录是否为项目目录")
        print("3. 权限设置是否正确")
    
    return success

if __name__ == "__main__":
    main()