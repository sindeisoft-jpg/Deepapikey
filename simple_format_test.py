#!/usr/bin/env python3
"""
简单测试优化后的API输出格式
"""

import requests
import json

def simple_test():
    """简单测试API输出格式"""
    
    url = "http://127.0.0.1:8765/v1/chat/completions"
    
    # 简单测试
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": "创建一个Python hello world程序，使用<create_file>格式"
            }
        ],
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        print("发送请求...")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print("✅ 请求成功!")
            print(f"响应长度: {len(content)} 字符")
            print("\n=== 输出内容 ===")
            print(content)
            
            # 检查关键元素
            print("\n=== 格式检查 ===")
            checks = [
                ("<create_file>" in content, "包含 <create_file> 标签"),
                ("<file_path>" in content, "包含 <file_path> 标签"), 
                ("<file_content>" in content, "包含 <file_content> 标签"),
                ("```python" in content, "包含Python代码块"),
                ("if __name__" in content, "包含主程序入口")
            ]
            
            for check, desc in checks:
                status = "✅" if check else "❌"
                print(f"{status} {desc}")
                
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 异常: {e}")

if __name__ == "__main__":
    print("=== 简单API格式测试 ===")
    simple_test()