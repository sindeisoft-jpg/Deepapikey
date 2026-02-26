#!/usr/bin/env python3
"""
测试CLINE集成：验证API能否生成代码文件
"""

import requests
import json
import os

def test_api_code_generation():
    """测试API代码生成功能"""
    url = "http://127.0.0.1:8766/v1/chat/completions"
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user", 
                "content": "写一个Python的hello world程序，要求包含Shebang行、UTF-8编码声明、函数封装主逻辑、标准的if __name__ == '__main__'入口点"
            }
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("正在向API发送请求...")
        response = requests.post(url, json=payload, headers=headers, timeout=180)
        print(f"HTTP状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            content = data.get('message', {}).get('content', '')
            print(f"API响应内容长度: {len(content)} 字符")
            
            # 检查是否包含代码块
            if '```python' in content:
                print("✅ 发现Python代码块")
                # 提取代码
                start_idx = content.find('```python')
                if start_idx > -1:
                    code_start = content.find('\n', start_idx) + 1
                    code_end = content.find('```', code_start)
                    if code_end > -1:
                        code = content[code_start:code_end].strip()
                        print("✅ 成功提取代码")
                        print("代码内容:")
                        print(code)
                        
                        # 尝试保存到文件
                        test_file = "test_hello.py"
                        with open(test_file, 'w', encoding='utf-8') as f:
                            f.write(code)
                        print(f"✅ 成功创建文件: {test_file}")
                        
                        # 验证文件内容
                        with open(test_file, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                            print(f"文件内容验证: {len(file_content)} 字符")
                            
                        return True
                    else:
                        print("❌ 未找到代码块结束标记")
                else:
                    print("❌ 未找到代码块开始标记")
            else:
                print("❌ 未发现代码块格式")
                
        else:
            print(f"❌ API请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        import traceback
        traceback.print_exc()
    
    return False

if __name__ == "__main__":
    print("=== 测试CLINE集成 ===")
    success = test_api_code_generation()
    print(f"\n测试结果: {'成功' if success else '失败'}")