#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API功能的简单脚本
"""

import urllib.request
import json
import urllib.parse

def test_api_connection():
    """测试API连接和基本功能"""
    print("=== 测试API连接 ===")
    
    try:
        # 测试根路径
        req = urllib.request.Request('http://127.0.0.1:8766/')
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        print("✓ API服务连接成功")
        print("服务信息:", json.dumps(data, indent=2, ensure_ascii=False))
        return True
    except Exception as e:
        print("✗ API服务连接失败:", str(e))
        return False

def test_basic_chat():
    """测试基本聊天功能"""
    print("\n=== 测试基本聊天功能 ===")
    
    test_data = {
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'user', 'content': '请用Python写一个hello world程序'}
        ]
    }
    
    try:
        data = json.dumps(test_data).encode('utf-8')
        req = urllib.request.Request(
            'http://127.0.0.1:8766/v1/chat/completions',
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode('utf-8'))
        
        print("✓ API调用成功")
        print("响应状态:", result.get('choices', [{}])[0].get('finish_reason'))
        print("\n--- 生成的内容 ---")
        content = result['choices'][0]['message']['content']
        print(content)
        print("--- 内容结束 ---")
        
        # 检查内容质量
        if '```python' in content and 'print' in content:
            print("✓ 内容格式正确，包含Python代码块")
        else:
            print("⚠ 内容可能缺少标准代码格式")
            
        return True
        
    except Exception as e:
        print("✗ API调用失败:", str(e))
        return False

def test_claude_compatibility():
    """测试Claude兼容性"""
    print("\n=== 测试Claude兼容性 ===")
    
    test_data = {
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'system', 'content': '你是一个专业的Python开发者，请直接提供代码解决方案'},
            {'role': 'user', 'content': '创建一个读取JSON文件并打印内容的Python脚本'}
        ]
    }
    
    try:
        data = json.dumps(test_data).encode('utf-8')
        req = urllib.request.Request(
            'http://127.0.0.1:8766/v1/chat/completions',
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode('utf-8'))
        
        content = result['choices'][0]['message']['content']
        print("生成内容预览:")
        print(content[:200] + "..." if len(content) > 200 else content)
        
        # 检查是否适合Claude处理
        issues = []
        if 'ask_followup_question' in content:
            issues.append("包含工具调用占位符")
        if '[约束]' in content or '[问题]' in content:
            issues.append("包含内部标签")
        if content.strip() == "":
            issues.append("内容为空")
            
        if issues:
            print("⚠ 发现潜在问题:", "; ".join(issues))
        else:
            print("✓ 内容看起来适合Claude等智能体处理")
            
        return len(issues) == 0
        
    except Exception as e:
        print("✗ 测试失败:", str(e))
        return False

if __name__ == "__main__":
    print("开始测试DeepSeek API功能...")
    
    success = True
    success &= test_api_connection()
    success &= test_basic_chat()
    success &= test_claude_compatibility()
    
    print(f"\n=== 测试总结 ===")
    if success:
        print("🎉 所有测试通过！API功能正常工作")
    else:
        print("❌ 部分测试失败，请检查API配置")