#!/usr/bin/env python3
"""
测试优化后的Cline/Aline兼容API输出
"""

import requests
import json
import time

def test_cline_compatible_output():
    """测试Cline兼容的API输出格式"""
    
    # API端点
    url = "http://127.0.0.1:8765/v1/chat/completions"
    
    # 测试用例1：简单代码生成
    print("=== 测试1: 简单Python代码生成 ===")
    test_messages_1 = [
        {
            "role": "user",
            "content": "请创建一个Python hello world程序"
        }
    ]
    
    payload_1 = {
        "model": "deepseek-chat",
        "messages": test_messages_1,
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        response_1 = requests.post(url, json=payload_1, timeout=30)
        if response_1.status_code == 200:
            result_1 = response_1.json()
            content_1 = result_1['choices'][0]['message']['content']
            print("✅ 简单代码生成测试成功")
            print("输出内容预览:")
            print(content_1[:300] + "..." if len(content_1) > 300 else content_1)
            
            # 检查是否包含正确的格式
            if "<create_file>" in content_1 and "<file_path>" in content_1:
                print("✅ 包含正确的文件创建格式")
            else:
                print("⚠️  可能缺少文件创建格式标签")
        else:
            print(f"❌ 请求失败: {response_1.status_code}")
            print(response_1.text)
    except Exception as e:
        print(f"❌ 测试1异常: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例2：多文件项目
    print("=== 测试2: 多文件项目生成 ===")
    test_messages_2 = [
        {
            "role": "user", 
            "content": "请创建一个简单的Python Web应用，包含主程序和requirements.txt"
        }
    ]
    
    payload_2 = {
        "model": "deepseek-chat",
        "messages": test_messages_2,
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        response_2 = requests.post(url, json=payload_2, timeout=60)  # 更长超时时间
        if response_2.status_code == 200:
            result_2 = response_2.json()
            content_2 = result_2['choices'][0]['message']['content']
            print("✅ 多文件项目测试成功")
            print("输出内容长度:", len(content_2))
            
            # 检查多文件格式
            create_file_count = content_2.count("<create_file>")
            file_path_count = content_2.count("<file_path>")
            file_content_count = content_2.count("<file_content>")
            
            print(f"检测到 {create_file_count} 个文件创建标签")
            print(f"检测到 {file_path_count} 个文件路径标签")  
            print(f"检测到 {file_content_count} 个文件内容标签")
            
            if create_file_count >= 2 and file_path_count >= 2 and file_content_count >= 2:
                print("✅ 多文件格式正确")
            else:
                print("⚠️  多文件格式可能不完整")
                
            print("输出内容预览:")
            print(content_2[:500] + "..." if len(content_2) > 500 else content_2)
        else:
            print(f"❌ 请求失败: {response_2.status_code}")
            print(response_2.text)
    except Exception as e:
        print(f"❌ 测试2异常: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 测试用例3：代码块格式检查
    print("=== 测试3: 代码块格式检查 ===")
    test_messages_3 = [
        {
            "role": "user",
            "content": "写一个计算斐波那契数列的Python函数"
        }
    ]
    
    payload_3 = {
        "model": "deepseek-chat", 
        "messages": test_messages_3,
        "temperature": 0.3,  # 更低温度确保一致性
        "stream": False
    }
    
    try:
        response_3 = requests.post(url, json=payload_3, timeout=30)
        if response_3.status_code == 200:
            result_3 = response_3.json()
            content_3 = result_3['choices'][0]['message']['content']
            print("✅ 代码块格式测试成功")
            
            # 检查代码块格式
            code_blocks = content_3.count("```")
            python_blocks = content_3.count("```python")
            
            print(f"检测到 {code_blocks} 个代码块标记")
            print(f"检测到 {python_blocks} 个Python代码块")
            
            if python_blocks > 0:
                print("✅ 包含Python代码块格式")
            elif code_blocks > 0:
                print("✅ 包含通用代码块格式")
            else:
                print("⚠️  缺少代码块格式")
                
            print("输出内容预览:")
            lines = content_3.split('\n')
            for i, line in enumerate(lines[:20]):  # 显示前20行
                print(f"{i+1:2d}: {line}")
        else:
            print(f"❌ 请求失败: {response_3.status_code}")
            print(response_3.text)
    except Exception as e:
        print(f"❌ 测试3异常: {e}")

def test_streaming_response():
    """测试流式响应"""
    print("\n=== 测试流式响应 ===")
    
    url = "http://127.0.0.1:8765/v1/chat/completions"
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": "用一句话解释什么是递归"
            }
        ],
        "temperature": 0.7,
        "stream": True  # 启用流式
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30, stream=True)
        if response.status_code == 200:
            print("✅ 流式响应测试成功")
            print("接收到的数据块:")
            
            chunk_count = 0
            for line in response.iter_lines():
                if line:
                    chunk_count += 1
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        data = decoded_line[6:]  # 移除 'data: ' 前缀
                        if data != '[DONE]':
                            try:
                                json_data = json.loads(data)
                                if 'choices' in json_data and len(json_data['choices']) > 0:
                                    delta = json_data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        print(f"块 {chunk_count}: {content}")
                            except json.JSONDecodeError:
                                print(f"块 {chunk_count}: 无法解析JSON")
                                
            print(f"总共接收到 {chunk_count} 个数据块")
        else:
            print(f"❌ 流式请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 流式测试异常: {e}")

if __name__ == "__main__":
    print("=== Cline/Aline兼容API测试 ===")
    print("测试优化后的API输出格式是否符合智能体要求\n")
    
    # 先等待API服务启动
    print("等待API服务启动...")
    time.sleep(2)
    
    # 运行各项测试
    test_cline_compatible_output()
    test_streaming_response()
    
    print("\n=== 测试完成 ===")
    print("如果所有测试都显示✅，说明API输出格式已优化完成")
    print("Cline/Aline智能体现在应该能够正确识别和执行文件写入操作")