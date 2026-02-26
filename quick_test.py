#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速API功能验证测试
"""

import urllib.request
import json
import time

def test_api_quick():
    """快速测试API核心功能"""
    print("=== 快速API功能验证 ===")
    
    # 测试1: 基本连接
    try:
        req = urllib.request.Request('http://127.0.0.1:8766/')
        response = urllib.request.urlopen(req, timeout=5)
        data = json.loads(response.read().decode('utf-8'))
        print("✓ API服务连接正常")
    except Exception as e:
        print(f"✗ API连接失败: {e}")
        return False
    
    # 测试2: 简单代码生成
    test_data = {
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'user', 'content': 'print("Hello World")'}
        ]
    }
    
    try:
        data = json.dumps(test_data).encode('utf-8')
        req = urllib.request.Request(
            'http://127.0.0.1:8766/v1/chat/completions',
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print("正在调用API生成代码...")
        start_time = time.time()
        response = urllib.request.urlopen(req, timeout=60)  # 增加超时时间
        end_time = time.time()
        
        result = json.loads(response.read().decode('utf-8'))
        content = result['choices'][0]['message']['content']
        
        print(f"✓ API调用成功 (耗时: {end_time - start_time:.1f}秒)")
        print(f"生成内容长度: {len(content)} 字符")
        
        # 检查内容质量
        checks = {
            '不包含系统指令': '[系统指令]' not in content,
            '不包含Cline配置': 'You are Cline' not in content,
            '不包含占位符': 'ask_followup_question' not in content,
            '包含代码块标记': '```' in content or '**' in content
        }
        
        print("\n内容质量检查:")
        all_passed = True
        for check_name, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"  {status} {check_name}")
            if not passed:
                all_passed = False
        
        print(f"\n生成的内容预览:")
        preview = content[:200] + "..." if len(content) > 200 else content
        print(preview)
        
        return all_passed
        
    except Exception as e:
        print(f"✗ API调用失败: {e}")
        return False

if __name__ == "__main__":
    success = test_api_quick()
    if success:
        print("\n🎉 API功能验证通过！可以正常使用")
    else:
        print("\n❌ API功能存在问题，需要进一步调试")