#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API修复验证测试
验证改进后的内容抓取功能
"""

import urllib.request
import json
import time

def test_improved_api():
    """测试改进后的API功能"""
    print("=== 改进后API功能测试 ===")
    
    # 测试用例
    test_cases = [
        {
            'name': '简单问候',
            'message': '你好',
            'expected_keywords': ['你好', '帮助']
        },
        {
            'name': '代码请求',
            'message': '写一个Python的hello world程序',
            'expected_keywords': ['print', 'hello', 'world', '```python']
        },
        {
            'name': '复杂问题',
            'message': '如何用Python处理JSON数据',
            'expected_keywords': ['json', 'loads', 'dumps', 'Python']
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i}: {test_case['name']} ---")
        print(f"请求内容: {test_case['message']}")
        
        test_data = {
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'user', 'content': test_case['message']}
            ]
        }
        
        try:
            data = json.dumps(test_data).encode('utf-8')
            req = urllib.request.Request(
                'http://127.0.0.1:8766/v1/chat/completions',
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            print("发送请求...")
            start_time = time.time()
            response = urllib.request.urlopen(req, timeout=180)
            end_time = time.time()
            
            result = json.loads(response.read().decode('utf-8'))
            content = result['choices'][0]['message']['content']
            
            print(f"✓ 响应成功 (耗时: {end_time - start_time:.1f}秒)")
            print(f"响应长度: {len(content)} 字符")
            
            # 分析响应内容
            analysis = {
                'length': len(content),
                'is_empty': len(content.strip()) == 0,
                'is_default_prompt': '请直接描述你需要的代码或问题' in content,
                'has_expected_content': any(keyword.lower() in content.lower() 
                                          for keyword in test_case['expected_keywords'])
            }
            
            print("响应分析:")
            for key, value in analysis.items():
                status = "✓" if value else "✗"
                print(f"  {status} {key}: {value}")
            
            # 显示内容预览
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"内容预览: {preview}")
            
            # 判断测试结果
            if analysis['is_empty']:
                test_result = 'FAIL_EMPTY'
            elif analysis['is_default_prompt']:
                test_result = 'FAIL_DEFAULT'
            elif analysis['has_expected_content']:
                test_result = 'SUCCESS_EXPECTED'
            else:
                test_result = 'SUCCESS_UNEXPECTED'
                
            results.append({
                'test_name': test_case['name'],
                'result': test_result,
                'analysis': analysis,
                'content_length': len(content),
                'response_time': end_time - start_time
            })
            
        except Exception as e:
            print(f"✗ 请求失败: {e}")
            results.append({
                'test_name': test_case['name'],
                'result': 'ERROR',
                'error': str(e)
            })
        
        # 避免请求过于频繁
        time.sleep(2)
    
    # 总结测试结果
    print("\n" + "="*50)
    print("=== 测试结果总结 ===")
    
    success_count = sum(1 for r in results if r['result'].startswith('SUCCESS'))
    total_tests = len(results)
    
    print(f"总测试数: {total_tests}")
    print(f"成功测试: {success_count}")
    print(f"成功率: {success_count/total_tests*100:.1f}%")
    
    print("\n详细结果:")
    for result in results:
        status_icon = {
            'SUCCESS_EXPECTED': '🎉',
            'SUCCESS_UNEXPECTED': '⚠️',
            'FAIL_EMPTY': '❌',
            'FAIL_DEFAULT': '❌',
            'ERROR': '💥'
        }.get(result['result'], '❓')
        
        print(f"{status_icon} {result['test_name']}: {result['result']}")
        if 'content_length' in result:
            print(f"   长度: {result['content_length']} 字符, 耗时: {result['response_time']:.1f}秒")
    
    # 整体评估
    if success_count == total_tests:
        print("\n🎯 完美！所有测试都成功通过")
        print("API功能已完全修复")
    elif success_count > 0:
        print(f"\n✅ 基本功能正常 ({success_count}/{total_tests} 测试通过)")
        print("API可以正常使用，但可能需要进一步优化")
    else:
        print("\n❌ API功能仍有问题")
        print("需要进一步调试和修复")
    
    return success_count > 0

def main():
    print("开始API修复验证测试...")
    
    success = test_improved_api()
    
    if success:
        print("\n🚀 API修复成功！")
        print("现在可以正常使用API接口与Claude等智能体集成")
    else:
        print("\n🔧 API仍需进一步修复")
    
    return success

if __name__ == "__main__":
    main()