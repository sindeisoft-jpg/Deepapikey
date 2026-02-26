
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
