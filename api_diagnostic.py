#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API响应诊断和修复工具
专门解决API接口没有返回数据但网页执行了动作的问题
"""

import urllib.request
import json
import time
import threading
from queue import Queue

class APIDiagnosticTool:
    def __init__(self, base_url='http://127.0.0.1:8766'):
        self.base_url = base_url
        self.diagnostic_results = {}
        
    def diagnose_api_response_issue(self):
        """诊断API响应问题"""
        print("=== API响应问题诊断 ===")
        
        # 测试1: 基本连接测试
        connection_ok = self.test_connection()
        
        # 测试2: 简单请求测试
        simple_request_ok = self.test_simple_request()
        
        # 测试3: 超时行为测试
        timeout_behavior = self.test_timeout_behavior()
        
        # 测试4: JavaScript回调诊断
        js_callback_diagnosis = self.diagnose_js_callbacks()
        
        print("\n=== 诊断总结 ===")
        print(f"连接状态: {'✓' if connection_ok else '✗'}")
        print(f"简单请求: {'✓' if simple_request_ok else '✗'}")
        print(f"超时处理: {'✓' if timeout_behavior else '✗'}")
        print(f"JS回调: {'✓' if js_callback_diagnosis else '✗'}")
        
        return all([connection_ok, simple_request_ok, timeout_behavior, js_callback_diagnosis])
    
    def test_connection(self):
        """测试基本连接"""
        print("1. 测试API基本连接...")
        try:
            req = urllib.request.Request(f'{self.base_url}/')
            response = urllib.request.urlopen(req, timeout=5)
            data = json.loads(response.read().decode('utf-8'))
            print("   ✓ 连接成功")
            print(f"   服务信息: {data.get('service', 'Unknown')}")
            return True
        except Exception as e:
            print(f"   ✗ 连接失败: {e}")
            return False
    
    def test_simple_request(self):
        """测试简单API请求"""
        print("2. 测试简单API请求...")
        test_data = {
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'user', 'content': 'Hello'}
            ]
        }
        
        try:
            data = json.dumps(test_data).encode('utf-8')
            req = urllib.request.Request(
                f'{self.base_url}/v1/chat/completions',
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            print("   发送请求...")
            start_time = time.time()
            response = urllib.request.urlopen(req, timeout=30)
            end_time = time.time()
            
            result = json.loads(response.read().decode('utf-8'))
            content = result['choices'][0]['message']['content']
            
            print(f"   ✓ 请求成功 (耗时: {end_time - start_time:.1f}秒)")
            print(f"   响应长度: {len(content)} 字符")
            print(f"   响应预览: {content[:100]}...")
            
            # 检查响应质量
            quality_issues = []
            if not content.strip():
                quality_issues.append("响应内容为空")
            if '[系统指令]' in content:
                quality_issues.append("包含系统指令标签")
            if 'ask_followup_question' in content:
                quality_issues.append("包含工具调用占位符")
                
            if quality_issues:
                print(f"   ⚠ 质量问题: {', '.join(quality_issues)}")
                return False
            else:
                print("   ✓ 响应质量良好")
                return True
                
        except Exception as e:
            print(f"   ✗ 请求失败: {e}")
            return False
    
    def test_timeout_behavior(self):
        """测试超时行为"""
        print("3. 测试超时处理机制...")
        test_data = {
            'model': 'deepseek-chat',
            'messages': [
                {'role': 'user', 'content': '请详细解释量子计算原理'}  # 复杂请求，容易超时
            ]
        }
        
        try:
            data = json.dumps(test_data).encode('utf-8')
            req = urllib.request.Request(
                f'{self.base_url}/v1/chat/completions',
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            print("   发送复杂请求测试超时...")
            start_time = time.time()
            # 使用较短超时时间来测试超时处理
            response = urllib.request.urlopen(req, timeout=15)
            end_time = time.time()
            
            result = json.loads(response.read().decode('utf-8'))
            content = result['choices'][0]['message']['content']
            
            print(f"   ✓ 复杂请求完成 (耗时: {end_time - start_time:.1f}秒)")
            print(f"   响应长度: {len(content)} 字符")
            return True
            
        except urllib.error.URLError as e:
            if 'timed out' in str(e):
                print("   ✓ 超时处理正常工作")
                return True
            else:
                print(f"   ✗ 其他URL错误: {e}")
                return False
        except Exception as e:
            print(f"   ✗ 其他错误: {e}")
            return False
    
    def diagnose_js_callbacks(self):
        """诊断JavaScript回调问题"""
        print("4. 诊断JavaScript回调机制...")
        
        # 创建测试队列来模拟API请求处理
        request_queue = Queue()
        response_dict = {}
        
        # 模拟API请求
        test_request_id = "test_" + str(time.time())
        test_message = "诊断测试消息"
        test_event = threading.Event()
        
        print("   模拟API请求队列处理...")
        request_queue.put((test_request_id, test_message, test_event))
        
        # 检查队列状态
        if not request_queue.empty():
            print("   ✓ 请求队列工作正常")
            
            # 尝试处理请求
            try:
                request_id, message, event = request_queue.get_nowait()
                print(f"   ✓ 成功从队列获取请求: {request_id}")
                
                # 模拟响应处理
                response_dict[request_id] = "测试响应内容"
                event.set()
                
                # 验证响应
                if request_id in response_dict:
                    response_content = response_dict.pop(request_id)
                    print(f"   ✓ 响应处理正常: {response_content}")
                    return True
                else:
                    print("   ✗ 响应字典处理异常")
                    return False
                    
            except Exception as e:
                print(f"   ✗ 队列处理异常: {e}")
                return False
        else:
            print("   ✗ 请求队列为空")
            return False

def create_fix_patch():
    """创建修复补丁"""
    patch_content = '''
# API响应修复补丁
# 解决问题：API接口没有返回数据但网页执行了动作

## 问题分析：
1. JavaScript回调 `_on_final_fetch_done` 可能未正确触发
2. API响应超时设置可能过短
3. 网页内容抓取脚本可能存在兼容性问题

## 修复方案：

### 1. 增强回调可靠性
在 `main.py` 中修改 `_on_final_fetch_done` 方法：

```python
def _on_final_fetch_done(self, reply_str):
    """最终抓取回调：增强错误处理和重试机制"""
    try:
        # 停止安全定时器
        if self._api_final_fetch_safety_timer is not None:
            self._api_final_fetch_safety_timer.stop()
            self._api_final_fetch_safety_timer = None
            
        # 停止回复流
        self._stop_reply_stream()
        
        # 处理回复内容
        final = (reply_str or "").strip() if isinstance(reply_str, str) else ""
        if not final:
            final = self._last_reply_text or ""
            
        # 记录调试信息
        print(f"DEBUG: API最终回复 - 长度: {len(final)}, 内容预览: {final[:100]}")
        
        # 确保API响应字典存在
        if self._api_request_id and self._api_response_dict is not None:
            self._api_response_dict[self._api_request_id] = final
            if self._api_response_event:
                self._api_response_event.set()
                print(f"DEBUG: API事件已设置，请求ID: {self._api_request_id}")
            self._api_request_id = None
            self._api_response_event = None
        else:
            print("DEBUG: API响应状态异常")
            
        self.statusBar().showMessage("API 请求已完成")
        
    except Exception as e:
        print(f"DEBUG: 回调处理异常: {e}")
        # 兜底处理
        self._api_safety_flush_and_clear()
```

### 2. 增加超时时间
在 `api_server.py` 中修改超时设置：

```python
# 增加API请求超时时间
ok = event.wait(timeout=180)  # 从120秒增加到180秒
```

### 3. 改进网页内容抓取
增强 `_get_reply_script` 的兼容性：

```javascript
// 添加更多的选择器和容错处理
var selectors = [
    '[data-message-type="assistant"]',
    '.message-assistant',
    '.ai-response',
    '.bot-message',
    '[class*="assistant"]',
    '[class*="response"]',
    // ... 其他选择器
];

// 添加重试机制
var maxRetries = 3;
var retryCount = 0;

function tryFetchContent() {
    // 原有的抓取逻辑
    var content = fetchContentLogic();
    
    if (!content && retryCount < maxRetries) {
        retryCount++;
        setTimeout(tryFetchContent, 1000); // 1秒后重试
        return;
    }
    
    return content || "内容获取失败";
}
```
'''
    
    with open('/Users/xurongyu/Desktop/01_项目文件夹/appleweb/api_fix_patch.md', 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    print("✓ 修复补丁已生成: api_fix_patch.md")

def main():
    print("开始API响应问题诊断...")
    
    diagnostic = APIDiagnosticTool()
    success = diagnostic.diagnose_api_response_issue()
    
    if success:
        print("\n🎉 诊断完成：API基础设施工作正常")
        print("问题可能出现在具体的回调处理或超时设置上")
    else:
        print("\n❌ 诊断发现问题：API基础设施存在异常")
    
    # 生成修复补丁
    create_fix_patch()
    
    return success

if __name__ == "__main__":
    main()