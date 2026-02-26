#!/usr/bin/env python3
"""
DeepSeek Qt浏览器应用
一个内嵌Web浏览器，打开deepseek官网，并提供对话界面的Qt应用
"""

import sys
import os
from queue import Queue
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSlot
try:
    from pynput.keyboard import Controller as KeyController, Key
    _HAS_PYNPUT = True
except ImportError:
    _HAS_PYNPUT = False
try:
    from api_server import start_api_server
    _HAS_API_SERVER = True
except ImportError:
    _HAS_API_SERVER = False
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QSplitter, QMessageBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtGui import QFont, QIcon


class DeepSeekBrowser(QMainWindow):
    """主窗口类，包含浏览器和对话界面"""
    
    def __init__(self):
        super().__init__()
        self._reply_stream_timer = None
        self._stream_history = ""
        self._last_reply_text = ""
        self._last_sent_message = ""  # 本次发送的用户内容，用于避免把用户消息当回复
        self._stream_unchanged_count = 0
        self._stream_poll_count = 0
        self._api_request_id = None
        self._api_response_event = None
        self._api_response_dict = None
        self._api_request_queue = None
        self._api_final_fetch_safety_timer = None  # 防止 runJavaScript 回调不触发导致第二次请求无法取到
        self._api_poll_timer = None
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("DeepSeek Qt浏览器")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器，左侧是浏览器，右侧是对话界面
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：Web浏览器
        self.browser = QWebEngineView()
        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        self.browser.setUrl(QUrl("https://chat.deepseek.com"))
        splitter.addWidget(self.browser)
        
        # 右侧：对话面板
        chat_panel = QWidget()
        chat_layout = QVBoxLayout(chat_panel)
        
        # 标题
        title_label = QLabel("DeepSeek 对话界面")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chat_layout.addWidget(title_label)
        
        # 输入框标签
        input_label = QLabel("输入您的问题：")
        chat_layout.addWidget(input_label)
        
        # 输入框
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("在这里输入您的问题...")
        self.input_text.setMaximumHeight(150)
        self.input_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                color: #333333;  /* 确保文字颜色可见 */
                background-color: #ffffff;
            }
            QTextEdit:focus {
                border-color: #4CAF50;
                background-color: #f8f9fa;
            }
        """)
        chat_layout.addWidget(self.input_text)
        
        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        chat_layout.addWidget(self.send_button)
        
        # 返回框标签
        output_label = QLabel("DeepSeek 回复：")
        chat_layout.addWidget(output_label)
        
        # 返回框
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("DeepSeek的回复将显示在这里...")
        chat_layout.addWidget(self.output_text)
        
        # 控制按钮区域
        control_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("清空")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        
        self.refresh_button = QPushButton("刷新页面")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        control_layout.addWidget(self.clear_button)
        control_layout.addWidget(self.refresh_button)
        control_layout.addStretch()
        
        chat_layout.addLayout(control_layout)
        
        # 添加右侧面板到分割器
        splitter.addWidget(chat_panel)
        
        # 设置分割器初始比例（70%浏览器，30%对话面板）
        splitter.setSizes([840, 360])
        
        # 将分割器添加到主布局
        main_layout.addWidget(splitter)
        
        # 状态栏
        self.statusBar().showMessage("就绪 - 已加载DeepSeek官网")
        
    def setup_connections(self):
        """设置信号和槽的连接"""
        self.send_button.clicked.connect(self.send_message)
        self.clear_button.clicked.connect(self.clear_output)
        self.refresh_button.clicked.connect(self.refresh_browser)
        
        # 浏览器加载状态变化
        self.browser.loadStarted.connect(self.on_load_started)
        self.browser.loadFinished.connect(self.on_load_finished)
        
    def on_load_started(self):
        """浏览器开始加载页面"""
        self.statusBar().showMessage("正在加载页面...")
        
    def on_load_finished(self, success):
        """浏览器完成加载页面"""
        if success:
            self.statusBar().showMessage("页面加载完成")
        else:
            self.statusBar().showMessage("页面加载失败")
            
    def _escape_for_js(self, text):
        """将文本转义后安全放入 JavaScript 单引号字符串中"""
        if not text:
            return ""
        return (text.replace("\\", "\\\\")
                    .replace("'", "\\'")
                    .replace("\r", "\\r")
                    .replace("\n", "\\n"))
    
    def _build_inject_script(self, message: str) -> str:
        """生成将 message 注入网页并触发发送的 JS。供 UI 与 API 共用。"""
        message_escaped = self._escape_for_js(message)
        return f"""
        (function() {{
            var msg = '{message_escaped}';
            setTimeout(function() {{
            var selectors = [
                'textarea[placeholder*="DeepSeek"]',
                'textarea[placeholder*="发送消息"]',
                'textarea[placeholder*="输入"]',
                'textarea[placeholder*="message"]',
                'textarea[placeholder*="说点什么"]',
                'textarea',
                'input[type="text"]',
                '[contenteditable="true"]',
                '[role="textbox"]',
                '.ProseMirror'
            ];
            var target = null;
            for (var i = 0; i < selectors.length; i++) {{
                var list = document.querySelectorAll(selectors[i]);
                for (var j = 0; j < list.length; j++) {{
                    var el = list[j];
                    if (el.offsetWidth > 0 && el.offsetHeight > 0) {{
                        target = el;
                        break;
                    }}
                }}
                if (target) break;
            }}
            if (!target) {{ return false; }}
            target.focus();
            if (target.tagName === 'TEXTAREA' || target.tagName === 'INPUT') {{
                var proto = target.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
                var desc = Object.getOwnPropertyDescriptor(proto, 'value');
                if (desc && desc.set) {{
                    desc.set.call(target, msg);
                }} else {{
                    target.value = msg;
                }}
                target.dispatchEvent(new InputEvent('input', {{ data: msg, inputType: 'insertText', bubbles: true }}));
                target.dispatchEvent(new Event('input', {{ bubbles: true }}));
                target.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }} else if (target.contentEditable === 'true' || target.getAttribute('role') === 'textbox') {{
                target.innerText = msg;
                target.textContent = msg;
                target.dispatchEvent(new InputEvent('input', {{ data: msg, inputType: 'insertText', bubbles: true }}));
                target.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }} else {{
                target.value = msg;
                target.innerText = msg;
                target.textContent = msg;
                target.dispatchEvent(new Event('input', {{ bubbles: true }}));
                target.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
            setTimeout(function() {{
                // 简化方案：直接模拟回车键
                console.log('直接模拟回车键发送...');
                
                // 确保输入框有焦点
                target.focus();
                
                // 延迟一小段时间确保焦点稳定
                setTimeout(function() {{
                    // 创建完整的回车键事件序列
                    var events = [
                        new KeyboardEvent('keydown', {{
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true,
                            cancelable: true
                        }}),
                        new KeyboardEvent('keypress', {{
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true,
                            cancelable: true
                        }}),
                        new KeyboardEvent('keyup', {{
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            which: 13,
                            bubbles: true,
                            cancelable: true
                        }})
                    ];
                    
                    // 依次触发所有事件
                    events.forEach(function(event, index) {{
                        console.log('触发事件', index + 1, ':', event.type);
                        target.dispatchEvent(event);
                    }});
                    
                    console.log('✅ 回车键模拟完成');
                }}, 100);
                
            }}, 300);
            }}, 150);
            return true;
        }})();
        """

    def send_message(self):
        """发送消息：将右侧输入提交到左侧 DeepSeek 网页的输入框并触发发送"""
        message = self.input_text.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "输入为空", "请输入您的问题")
            return
        self.output_text.append(f"您: {message}")
        self.output_text.append("")
        self.output_text.verticalScrollBar().setValue(
            self.output_text.verticalScrollBar().maximum()
        )
        self.input_text.clear()
        self.statusBar().showMessage("正在发送到网页...")
        self._last_sent_message = message
        self.browser.page().runJavaScript(
            self._build_inject_script(message), self._on_web_send_done
        )

    def _inject_and_send(self, message: str):
        """仅注入并发送到网页（供 API 调用，不更新右侧输入/输出）。"""
        self.statusBar().showMessage("API 请求处理中…")
        self._stream_history = self.output_text.toPlainText()
        self._last_reply_text = ""
        self._last_sent_message = message
        self._stream_unchanged_count = 0
        self._stream_poll_count = 0
        if self._reply_stream_timer is not None:
            self._reply_stream_timer.stop()
        self.browser.page().runJavaScript(
            self._build_inject_script(message), self._on_web_send_done
        )
    
    def _on_web_send_done(self, success):
        """网页注入/点击完成后的回调"""
        if success:
            self.statusBar().showMessage("已发送到网页，等待回复…")
            self._stream_history = self.output_text.toPlainText()
            self._last_reply_text = ""
            self._stream_unchanged_count = 0
            self._stream_poll_count = 0
            if self._reply_stream_timer is not None:
                self._reply_stream_timer.stop()
            QTimer.singleShot(500, self._simulate_enter_key)
            QTimer.singleShot(1500, self._start_reply_stream)
            
            # 添加调试信息
            debug_script = '''
            console.log("=== 调试信息 ===");
            console.log("页面标题:", document.title);
            console.log("当前URL:", window.location.href);
            console.log("页面状态:", document.readyState);
            
            // 检查输入框状态
            var inputElements = document.querySelectorAll("textarea, input[type='text'], [contenteditable='true']");
            console.log("找到输入元素数量:", inputElements.length);
            
            for(var i = 0; i < inputElements.length; i++) {
                var el = inputElements[i];
                console.log("元素" + i + ":", el.tagName, el.className, "可见:", el.offsetWidth > 0 && el.offsetHeight > 0, "值:", el.value || el.innerText);
            }
            
            // 检查按钮
            var buttons = document.querySelectorAll("button");
            console.log("找到按钮数量:", buttons.length);
            
            return {
                pageTitle: document.title,
                pageUrl: window.location.href,
                inputCount: inputElements.length,
                buttonCount: buttons.length
            };
            '''
            
            def debug_callback(result):
                print(f"调试结果: {result}")
                
            self.browser.page().runJavaScript(debug_script, debug_callback)
            
        else:
            self.statusBar().showMessage("未能找到网页输入框，请确认左侧已打开 DeepSeek 聊天页")
    
    def _simulate_enter_key(self):
        """用 pynput 模拟按下 Enter（系统级，页面会视为真实按键）"""
        self.activateWindow()
        self.raise_()
        self.browser.setFocus()
        if _HAS_PYNPUT:
            try:
                ctrl = KeyController()
                ctrl.press(Key.enter)
                ctrl.release(Key.enter)
            except Exception:
                pass

    def _start_reply_stream(self):
        """开始轮询网页中的回复，以流式方式更新到右侧"""
        self.statusBar().showMessage("正在获取网页回复…")
        self._stream_unchanged_count = 0
        self._stream_poll_count = 0
        if self._reply_stream_timer is None:
            self._reply_stream_timer = QTimer(self)
            self._reply_stream_timer.timeout.connect(self._poll_reply)
        self._reply_stream_timer.start(500)  # 500ms 一轮，减少 DOM 波动导致的断断续续

    def _stop_reply_stream(self):
        """停止轮询"""
        if self._reply_stream_timer is not None:
            self._reply_stream_timer.stop()
        self.statusBar().showMessage("回复已完整显示")

    def _poll_reply(self):
        """从网页抓取当前「最后一条」助手回复，避免第二次及以后取到第一条数据"""
        self.browser.page().runJavaScript(self._get_reply_script(), self._on_reply_chunk)

    def _on_reply_chunk(self, reply_str):
        """收到网页返回的回复片段，流式更新右侧显示；API 请求在稳定后做一次最终抓取再返回。"""
        self._stream_poll_count += 1
        if self._stream_poll_count > 200:
            self._stop_reply_stream()
            self._flush_api_response_if_any()
            return
        if reply_str is None:
            reply_str = ""
        if not isinstance(reply_str, str):
            reply_str = str(reply_str) if reply_str else ""
        reply_str = reply_str.strip()
        if reply_str and reply_str.strip() == (self._last_sent_message or "").strip():
            return
        # 防止 DOM 短暂切到其它节点导致内容突然变短（断断续续）
        if self._last_reply_text and len(reply_str) < len(self._last_reply_text) - 100:
            if len(reply_str) < max(100, int(len(self._last_reply_text) * 0.8)):
                return
        if reply_str == self._last_reply_text:
            self._stream_unchanged_count += 1
            if self._stream_unchanged_count >= 8:
                # 稳定 8 次（约 4s）后再做一次最终抓取，再写入 API 响应，避免用中间状态
                if self._api_request_id and self._api_response_dict is not None:
                    self._reply_stream_timer.stop()
                    # 若 runJavaScript 回调未触发，8s 后强制写回并清空状态，避免第二次请求永远不执行
                    if self._api_final_fetch_safety_timer is not None:
                        self._api_final_fetch_safety_timer.stop()
                    self._api_final_fetch_safety_timer = QTimer(self)
                    self._api_final_fetch_safety_timer.setSingleShot(True)
                    self._api_final_fetch_safety_timer.timeout.connect(self._api_safety_flush_and_clear)
                    self._api_final_fetch_safety_timer.start(8000)
                    QTimer.singleShot(600, self._final_fetch_for_api)  # 留时间让代码块渲染完再抓
                else:
                    self._stop_reply_stream()
                    if reply_str:
                        self._stream_history = self.output_text.toPlainText() + "\n\n"
                return
            return
        self._stream_unchanged_count = 0
        self._last_reply_text = reply_str
        if self._api_request_id is None:
            display = self._stream_history + "DeepSeek: " + reply_str
            self.output_text.setPlainText(display)
            self.output_text.verticalScrollBar().setValue(
                self.output_text.verticalScrollBar().maximum()
            )

    def _flush_api_response_if_any(self):
        """超时或停止时，若有未完成的 API 请求则用当前 _last_reply_text 写回并 set event。"""
        if not self._api_request_id or self._api_response_dict is None:
            return
        self._api_response_dict[self._api_request_id] = self._last_reply_text or ""
        if self._api_response_event:
            self._api_response_event.set()
        self._api_request_id = None
        self._api_response_event = None
        self.statusBar().showMessage("API 请求已完成")

    def _final_fetch_for_api(self):
        """稳定后做一次最终抓取，用此次结果作为 API 的 content，再停止轮询并写回。"""
        self.browser.page().runJavaScript(self._get_reply_script(), self._on_final_fetch_done)

    def _get_reply_script(self):
        """从页面抓取最后一条助手回复（含代码块），优先取整条消息根节点再提取全文。"""
        return """
        (function() {
            function getText(el) {
                if (!el) return '';
                var t = el.innerText || el.textContent || '';
                return (typeof t === 'string' ? t : '').trim();
            }
            function getCodeBlockLang(node) {
                var code = node.tagName === 'CODE' ? node : node.querySelector('code');
                var el = code || node;
                var cls = (el.className || '') + ' ' + (el.getAttribute('class') || '');
                var m = cls.match(/language-(\\w+)/);
                return m ? m[1] : '';
            }
            function toMarkdownLike(el) {
                if (!el) return '';
                var out = [];
                function walk(node) {
                    if (node.nodeType === 1) {
                        var tag = (node.tagName || '').toUpperCase();
                        if (tag === 'PRE') {
                            var code = node.querySelector('code');
                            var block = (code || node).innerText || (code || node).textContent || '';
                            var lang = getCodeBlockLang(node);
                            if (block) out.push('```' + (lang || '') + '\\n' + block.trim() + '\\n```');
                            return;
                        }
                        if (tag === 'DIV' && node.querySelector && !node.querySelector('pre')) {
                            var c = (node.className || '') + ' ' + (node.getAttribute('class') || '');
                            if (/code|Code|highlight/.test(c)) {
                                var block = getText(node);
                                if (block && block.length > 2) out.push('```\\n' + block + '\\n```');
                                return;
                            }
                        }
                        for (var i = 0; i < node.childNodes.length; i++) walk(node.childNodes[i]);
                    } else if (node.nodeType === 3) {
                        var t = (node.textContent || '').trim();
                        if (t) out.push(t);
                    }
                }
                walk(el);
                return out.join('\\n\\n').trim() || getText(el);
            }
            function isWelcome(t) {
                return t.indexOf('今天有什么可以帮') >= 0 || t.indexOf('有什么可以帮') >= 0;
            }
            function inDocOrder(a, b) {
                var pos = a.compareDocumentPosition(b);
                return (pos & Node.DOCUMENT_POSITION_FOLLOWING) ? -1 : 1;
            }
            // 1) 优先：只匹配「整条消息」的根节点（一条消息一个节点），避免取到不含代码的子块
            var rootSel = [
                '[data-message-type="assistant"]',
                '[class*="assistant"][class*="message"]',
                '[class*="message"][class*="assistant"]',
                '[role="article"][class*="assistant"]',
                'article[class*="assistant"]',
                'div[class*="assistant"][class*="message"]'
            ];
            for (var s = 0; s < rootSel.length; s++) {
                try {
                    var list = document.querySelectorAll(rootSel[s]);
                    if (list.length === 0) continue;
                    var roots = [];
                    for (var i = 0; i < list.length; i++) {
                        var el = list[i];
                        var t = getText(el);
                        if (t.length < 3 || isWelcome(t)) continue;
                        roots.push(el);
                    }
                    if (roots.length > 0) {
                        roots.sort(inDocOrder);
                        var lastRoot = roots[roots.length - 1];
                        return toMarkdownLike(lastRoot) || getText(lastRoot);
                    }
                } catch (e) {}
            }
            // 2) 回退：从任意节点中找「最后一条助手消息」的根（closest 到 message 根）
            var anySel = [
                '[class*="message"]', '[class*="Message"]',
                '[class*="assistant"]', '[class*="markdown"]', '[class*="content"]', '[class*="prose"]',
                'article', '[role="article"]', '[data-message-type="assistant"]', '[class*="reply"]',
                'pre', 'code'
            ];
            var candidates = [];
            for (var i = 0; i < anySel.length; i++) {
                var els = document.querySelectorAll(anySel[i]);
                for (var j = 0; j < els.length; j++) {
                    var el = els[j];
                    var t = getText(el);
                    if (t.length < 3 || isWelcome(t)) continue;
                    var root = el.closest && (
                        el.closest('[data-message-type="assistant"]') ||
                        el.closest('[class*="message"][class*="assistant"]') ||
                        el.closest('[class*="assistant"][class*="message"]') ||
                        el.closest('article[class*="assistant"]') ||
                        el.closest('[role="article"]') ||
                        el
                    );
                    var rootText = getText(root);
                    if (root && rootText.length > t.length + 20) t = rootText;
                    candidates.push({ el: root || el, text: t, len: (rootText || t).length });
                }
            }
            if (candidates.length === 0) {
                var main = document.querySelector('main') || document.querySelector('[role="main"]') || document.body;
                var full = getText(main);
                if (full.length > 50 && !isWelcome(full)) {
                    var idx = Math.max(full.lastIndexOf('您:'), full.lastIndexOf('You:'));
                    return idx >= 0 ? full.substring(idx).trim() : full;
                }
                var all = document.querySelectorAll('div, section, article');
                for (var k = all.length - 1; k >= 0; k--) {
                    var t = getText(all[k]);
                    if (t.length > 50 && t.length < 500000 && !isWelcome(t)) return t;
                }
                return '';
            }
            candidates.sort(function(a, b) { return inDocOrder(a.el, b.el); });
            var lastInDoc = candidates[candidates.length - 1].el;
            var fullContent = toMarkdownLike(lastInDoc) || getText(lastInDoc);
            if (fullContent.length > 50) return fullContent;
            var byLen = candidates.slice().sort(function(a, b) { return (b.len || b.text.length) - (a.len || a.text.length); });
            return toMarkdownLike(byLen[0].el) || byLen[0].text;
        })();
        """

    def _api_safety_flush_and_clear(self):
        """超时兜底：若最终抓取回调未触发，强制写回当前内容并清空状态，以便下一次 API 请求能执行。"""
        if self._api_final_fetch_safety_timer is not None:
            self._api_final_fetch_safety_timer.stop()
            self._api_final_fetch_safety_timer = None
        self._flush_api_response_if_any()

    def _on_final_fetch_done(self, reply_str):
        """最终抓取回调：用此次结果写回 API 并停止轮询。"""
        if self._api_final_fetch_safety_timer is not None:
            self._api_final_fetch_safety_timer.stop()
            self._api_final_fetch_safety_timer = None
        self._stop_reply_stream()
        final = (reply_str or "").strip() if isinstance(reply_str, str) else ""
        if not final:
            final = self._last_reply_text or ""
        if self._api_request_id and self._api_response_dict is not None:
            self._api_response_dict[self._api_request_id] = final
            if self._api_response_event:
                self._api_response_event.set()
            self._api_request_id = None
            self._api_response_event = None
        self.statusBar().showMessage("API 请求已完成")

    def set_api_queues(self, request_queue: Queue, response_dict: dict):
        """设置 API 请求队列与响应字典（由 main 在启动 API 服务后调用）。"""
        self._api_request_queue = request_queue
        self._api_response_dict = response_dict  # 与 api_server 共用，主线程写入回复

    def start_api_polling(self):
        """开始轮询 API 请求队列（需先 set_api_queues）。"""
        if self._api_request_queue is None or self._api_poll_timer is not None:
            return
        self._api_poll_timer = QTimer(self)
        self._api_poll_timer.timeout.connect(self._poll_api_request)
        self._api_poll_timer.start(500)

    def _poll_api_request(self):
        """从队列取 API 请求并在主线程执行注入与发送。"""
        if self._api_request_queue is None or self._api_request_id is not None:
            return
        try:
            request_id, message, event = self._api_request_queue.get_nowait()
        except Exception:
            return
        self._api_request_id = request_id
        self._api_response_event = event
        self._inject_and_send(message)

    def clear_output(self):
        """清空输出框"""
        if self._reply_stream_timer is not None:
            self._reply_stream_timer.stop()
        self._stream_history = ""
        self._last_reply_text = ""
        self.output_text.clear()
        self.statusBar().showMessage("输出已清空")
        
    def refresh_browser(self):
        """刷新浏览器页面"""
        self.browser.reload()
        self.statusBar().showMessage("正在刷新页面...")
        
    def closeEvent(self, event):
        """关闭窗口事件"""
        reply = QMessageBox.question(
            self, "确认退出",
            "确定要退出DeepSeek浏览器吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("DeepSeek Qt浏览器")
    app.setStyle("Fusion")

    window = DeepSeekBrowser()
    if _HAS_API_SERVER:
        try:
            request_queue = Queue()
            response_dict = {}
            port = int(os.environ.get("DEEPSEEK_API_PORT", "8765"))
            start_api_server(request_queue, response_dict, port=port)
            window.set_api_queues(request_queue, response_dict)
            window.start_api_polling()
            window.statusBar().showMessage(
                f"就绪 - 已加载 DeepSeek 官网 | Ollama 兼容 API: http://127.0.0.1:{port}/ (无 API Key)"
            )
        except Exception as e:
            window.statusBar().showMessage(f"就绪 - API 未启动: {e}")
    else:
        window.statusBar().showMessage("就绪 - 已加载 DeepSeek 官网")
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()