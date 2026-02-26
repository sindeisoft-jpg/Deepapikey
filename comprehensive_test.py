#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面的API功能测试脚本
测试各种场景下的API表现
"""

import urllib.request
import json
import time

BASE_URL = 'http://127.0.0.1:8766'

def make_api_call(messages, model='deepseek-chat'):
    """发起API调用"""
    data = {
        'model': model,
        'messages': messages
    }
    
    try:
        req_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(
            f'{BASE_URL}/v1/chat/completions',
            data=req_data,
            headers={'Content-Type': 'application/json'}
        )
        
        response = urllib.request.urlopen(req, timeout=30)
        return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"API调用失败: {e}")
        return None

def test_scenario(name, messages, expected_indicators=None):
    """测试特定场景"""
    print(f"\n=== 测试场景: {name} ===")
    
    result = make_api_call(messages)
    if not result:
        print("✗ 测试失败：API调用异常")
        return False
    
    content = result['choices'][0]['message']['content']
    print(f"生成内容长度: {len(content)} 字符")
    print("内容预览:")
    preview = content[:300] + "..." if len(content) > 300 else content
    print(preview)
    
    # 检查预期指标
    issues = []
    if expected_indicators:
        for indicator, should_contain in expected_indicators.items():
            if should_contain and indicator not in content:
                issues.append(f"缺少期望内容: {indicator}")
            elif not should_contain and indicator in content:
                issues.append(f"包含不应有的内容: {indicator}")
    
    if issues:
        print("⚠ 发现问题:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✓ 内容符合预期")
        return True

def main():
    print("开始全面API功能测试...")
    
    test_cases = [
        {
            'name': '基础代码生成',
            'messages': [
                {'role': 'user', 'content': '写一个Python的hello world程序'}
            ],
            'expected': {
                'print': True,
                '```python': True,
                '[系统指令]': False,
                'ask_followup_question': False
            }
        },
        {
            'name': '数据分析场景',
            'messages': [
                {'role': 'user', 'content': '如何用Python分析CSV文件中的数据？请提供完整示例'}
            ],
            'expected': {
                'pandas': True,
                '```python': True,
                'read_csv': True,
                'You are Cline': False
            }
        },
        {
            'name': '系统管理脚本',
            'messages': [
                {'role': 'user', 'content': '写一个bash脚本来备份重要文件'}
            ],
            'expected': {
                'bash': True,
                '```bash': True,
                '#!': True,
                'GLOBAL RULES': False
            }
        },
        {
            'name': 'Web开发示例',
            'messages': [
                {'role': 'user', 'content': '创建一个简单的Flask Web应用'}
            ],
            'expected': {
                'Flask': True,
                '```python': True,
                'from flask': True,
                '<task>': False
            }
        },
        {
            'name': '复杂项目结构',
            'messages': [
                {'role': 'user', 'content': '设计一个包含前端后端的完整项目结构，提供主要文件'}
            ],
            'expected': {
                '**': True,  # 文件名标记
                '```': True,  # 代码块
                'requirements.txt': True,
                'package.json': True
            }
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for test_case in test_cases:
        if test_scenario(
            test_case['name'], 
            test_case['messages'], 
            test_case['expected']
        ):
            passed += 1
        time.sleep(1)  # 避免请求过于频繁
    
    print(f"\n=== 测试总结 ===")
    print(f"通过: {passed}/{total}")
    if passed == total:
        print("🎉 所有测试通过！API功能完善")
    else:
        print("❌ 部分测试失败，需要进一步优化")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)