#!/usr/bin/env python3
"""
简单API测试：验证CLINE集成
"""

import urllib.request
import json
import os

def test_simple_api():
    """使用urllib测试API"""
    url = "http://127.0.0.1:8765/v1/chat/completions"
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user", 
                "content": "写一个Python的hello world程序"
            }
        ]
    }
    
    try:
        print("正在发送请求...")
        req = urllib.request.Request(url)
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(payload).encode('utf-8')
        
        with urllib.request.urlopen(req, timeout=180) as response:
            data = response.read().decode('utf-8')
            print(f"HTTP状态码: {response.getcode()}")
            
            if response.getcode() == 200:
                content = json.loads(data)
                message_content = content.get('message', {}).get('content', '')
                print(f"响应内容长度: {len(message_content)} 字符")
                
                # 检查是否包含代码
                if '```python' in message_content:
                    print("✅ 发现Python代码块")
                    # 尝试保存文件
                    with open('test_hello_simple.py', 'w', encoding='utf-8') as f:
                        f.write(message_content)
                    print("✅ 成功创建 test_hello_simple.py")
                    
                    # 显示文件内容
                    with open('test_hello_simple.py', 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(f"文件内容预览: {content[:200]}...")
                        
                else:
                    print("❌ 未发现代码块格式")
                    print(f"响应内容: {message_content[:300]}...")
                    
            else:
                print(f"❌ 请求失败: {data}")
                
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== 简单API测试 ===")
    test_simple_api()