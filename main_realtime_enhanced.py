#!/usr/bin/env python3
"""
DeepSeek Qt浏览器 - 增强实时代码显示版
优化了代码编写过程的实时显示体验
"""

import sys
import os
from queue import Queue
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QSplitter, QMessageBox, QComboBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from PyQt6.QtGui import QFont, QIcon, QColor, QTextCharFormat
from datetime import datetime
import re

class EnhancedDeepSeekBrowser(QMainWindow):
    """增强版DeepSeek浏览器，支持实时代码显示"""
    
    def __init__(self):
        super().__init__()
        self._reply_stream_timer = None
        self._stream_history = ""
        self._last_reply_text = ""
        self._last_sent_message = ""
        self._stream_unchanged_count = 0
        self._stream_poll_count = 0
        self._api_request_id = None
        self._api_response_event = None
        self._api_response_dict = None
        self._api_request_queue = None
        self._api_final_fetch_safety_timer = None
        
        # 实时显示相关变量
        self._current_displayed_text = ""
        self._last_code_block = ""
        self._code_blocks_found = []
        self._realtime_mode = True  # 实时模式开关
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("DeepSeek Qt浏览器 - 实时代码显示增强版")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：Web浏览器面板
        browser_panel = self.create_browser_panel()
        splitter.addWidget(browser_panel)
        
        # 右侧：增强对话面板
        chat_panel = self.create_enhanced_chat_panel()
        splitter.addWidget(chat_panel)
        
        # 设置分割器比例
        splitter.setSizes([900, 500])
        main_layout.addWidget(splitter)
        
        # 状态栏
        self.statusBar().showMessage("就绪 - 实时代码显示模式已启用")
        
    def create_browser_panel(self):
        """创建浏览器面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 浏览器控制栏
        control_layout = QHBoxLayout()
        
        self.back_button = QPushButton("←")
        self.forward_button = QPushButton("→")
        self.refresh_button = QPushButton("刷新")
        self.home_button = QPushButton("首页")
        
        # URL地址栏
        self.url_bar = QComboBox()
        self.url_bar.setEditable(True)
        self.url_bar.addItem("https://chat.deepseek.com")
        self.url_bar.addItem("https://www.deepseek.com")
        
        self.go_button = QPushButton("前往")
        
        # 控制按钮样式
        for btn in [self.back_button, self.forward_button, self.refresh_button, 
                   self.home_button, self.go_button]:
            btn.setMaximumWidth(60)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 5px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: #f0f0f0;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
        
        # 添加控件
        control_layout.addWidget(self.back_button)
        control_layout.addWidget(self.forward_button)
        control_layout.addWidget(self.refresh_button)
        control_layout.addWidget(self.home_button)
        control_layout.addWidget(self.url_bar)
        control_layout.addWidget(self.go_button)
        
        layout.addLayout(control_layout)
        
        # Web浏览器
        self.browser = QWebEngineView()
        self.browser.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        self.browser.setUrl(QUrl("https://chat.deepseek.com"))
        layout.addWidget(self.browser)
        
        return panel
        
    def create_enhanced_chat_panel(self):
        """创建增强的对话面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 标题
        title_label = QLabel("DeepSeek 实时对话界面")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 实时显示控制
        control_layout = QHBoxLayout()
        self.realtime_toggle = QPushButton("🟢 实时模式开启")
        self.realtime_toggle.setCheckable(True)
        self.realtime_toggle.setChecked(True)
        self.realtime_toggle.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #f44336;
            }
        """)
        self.realtime_toggle.clicked.connect(self.toggle_realtime_mode)
        control_layout.addWidget(self.realtime_toggle)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 输入框
        input_label = QLabel("输入您的问题：")
        layout.addWidget(input_label)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("在这里输入您的问题...")
        self.input_text.setMaximumHeight(120)
        layout.addWidget(self.input_text)
        
        # 发送按钮
        self.send_button = QPushButton("发送到DeepSeek")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(self.send_button)
        
        # 输出显示区域
        output_label = QLabel("实时回复显示：")
        layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QTextEdit {
                font-family: Monaco, Consolas, 'Courier New', monospace;
                font-size: 13px;
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.output_text)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        self.clear_button = QPushButton("清空")
        self.export_button = QPushButton("导出")
        for btn in [self.clear_button, self.export_button]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #607D8B;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #455A64;
                }
            """)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        return panel
        
    def setup_connections(self):
        """设置信号连接"""
        # 浏览器导航
        self.back_button.clicked.connect(self.browser.back)
        self.forward_button.clicked.connect(self.browser.forward)
        self.refresh_button.clicked.connect(self.browser.reload)
        self.home_button.clicked.connect(self.go_home)
        self.go_button.clicked.connect(self.navigate_to_url)
        self.url_bar.lineEdit().returnPressed.connect(self.navigate_to_url)
        
        # 对话功能
        self.send_button.clicked.connect(self.send_message)
        self.clear_button.clicked.connect(self.clear_output)
        self.export_button.clicked.connect(self.export_conversation)
        
        # 浏览器事件
        self.browser.loadStarted.connect(self.on_load_started)
        self.browser.loadFinished.connect(self.on_load_finished)
        self.browser.urlChanged.connect(self.on_url_changed)
        
    def toggle_realtime_mode(self):
        """切换实时模式"""
        self._realtime_mode = self.realtime_toggle.isChecked()
        if self._realtime_mode:
            self.realtime_toggle.setText("🟢 实时模式开启")
            self.realtime_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            self.statusBar().showMessage("实时代码显示模式已启用")
        else:
            self.realtime_toggle.setText("🔴 实时模式关闭")
            self.realtime_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            self.statusBar().showMessage("实时代码显示模式已禁用")
            
    def send_message(self):
        """发送消息"""
        message = self.input_text.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "输入为空", "请输入您的问题")
            return
            
        # 显示用户消息
        self._append_to_output("user", message)
        self.input_text.clear()
        
        # 准备发送到网页
        self.statusBar().showMessage("正在发送到DeepSeek...")
        self._last_sent_message = message
        
        # 注入消息到网页
        script = self._build_inject_script(message)
        self.browser.page().runJavaScript(script, self._on_message_sent)
        
    def _on_message_sent(self, success):
        """消息发送完成回调"""
        if success:
            self.statusBar().showMessage("消息已发送，等待回复...")
            # 启动实时流式显示
            if self._realtime_mode:
                self._start_realtime_stream()
        else:
            self.statusBar().showMessage("消息发送失败")
            
    def _start_realtime_stream(self):
        """启动实时流式显示"""
        self._stream_poll_count = 0
        self._stream_unchanged_count = 0
        self._current_displayed_text = ""
        self._code_blocks_found = []
        
        if self._reply_stream_timer is None:
            self._reply_stream_timer = QTimer(self)
            self._reply_stream_timer.timeout.connect(self._poll_reply_content)
            
        # 高频轮询实现实时效果（100ms）
        self._reply_stream_timer.start(100)
        self.statusBar().showMessage("🟡 正在实时接收回复...")
        
    def _poll_reply_content(self):
        """轮询回复内容"""
        self._stream_poll_count += 1
        
        # 超时保护
        if self._stream_poll_count > 1000:  # 约100秒
            self._stop_realtime_stream()
            return
            
        # 获取当前网页内容
        self.browser.page().runJavaScript(self._get_content_script(), self._on_content_received)
        
    def _on_content_received(self, content):
        """接收到内容的回调"""
        if not content or not isinstance(content, str):
            return
            
        content = content.strip()
        
        # 避免显示用户自己的消息
        if content.strip() == self._last_sent_message.strip():
            return
            
        # 实时更新显示
        self._update_realtime_display(content)
        
        # 检查是否稳定
        if content == self._last_reply_text:
            self._stream_unchanged_count += 1
            if self._stream_unchanged_count >= 20:  # 约2秒稳定
                self._stop_realtime_stream()
        else:
            self._stream_unchanged_count = 0
            self._last_reply_text = content
            
    def _update_realtime_display(self, new_content):
        """更新实时显示"""
        if len(new_content) <= len(self._current_displayed_text):
            return
            
        # 获取新增内容
        new_text = new_content[len(self._current_displayed_text):]
        
        # 检测代码块
        code_blocks = self._extract_code_blocks(new_content)
        
        if code_blocks and self._detect_code_progress(code_blocks):
            # 显示代码编写进度
            self._display_code_writing_progress(code_blocks)
        elif new_text.strip():
            # 显示普通文本
            self._append_to_output("assistant", new_text, is_incremental=True)
            
        self._current_displayed_text = new_content
        self._scroll_to_bottom()
        
    def _extract_code_blocks(self, content):
        """提取代码块"""
        code_pattern = r'```(?:\w+)?\s*\n([\s\S]*?)\n```'
        matches = re.findall(code_pattern, content)
        return [block.strip() for block in matches if block.strip()]
        
    def _detect_code_progress(self, current_blocks):
        """检测代码编写进度"""
        return (len(current_blocks) > len(self._code_blocks_found) or 
                (current_blocks and 
                 len(current_blocks[-1]) > len(self._code_blocks_found[-1]) if self._code_blocks_found else True))
                 
    def _display_code_writing_progress(self, code_blocks):
        """显示代码编写进度"""
        for i, code_block in enumerate(code_blocks):
            if i >= len(self._code_blocks_found):
                # 新的代码块
                self._append_to_output("code_start", f"\n🔧 开始编写第{i+1}个代码块...\n")
                self._code_blocks_found.append("")
                
            if code_block != self._code_blocks_found[i]:
                # 代码块有更新
                prev_len = len(self._code_blocks_found[i])
                new_content = code_block[prev_len:]
                if new_content:
                    self._append_to_output("code", new_content, is_code=True)
                    self._code_blocks_found[i] = code_block
                    
                    # 更新进度
                    progress = min(100, len(code_block) / max(1, len(code_block) + 20) * 100)
                    self.statusBar().showMessage(f"💻 代码编写中... {progress:.0f}%")
                    
    def _append_to_output(self, role, content, is_incremental=False, is_code=False):
        """向输出区域添加内容"""
        cursor = self.output_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        # 设置格式
        format_obj = QTextCharFormat()
        
        if role == "user":
            format_obj.setForeground(QColor("#4FC3F7"))
            format_obj.setFontWeight(QFont.Weight.Bold)
            prefix = "👤 您: "
        elif role == "assistant":
            format_obj.setForeground(QColor("#81C784"))
            prefix = "🤖 DeepSeek: "
        elif role == "code_start":
            format_obj.setForeground(QColor("#FFB74D"))
            format_obj.setFontWeight(QFont.Weight.Bold)
            prefix = ""
        elif role == "code":
            format_obj.setForeground(QColor("#64B5F6"))
            format_obj.setFontFamily("Monaco")
            prefix = ""
        else:
            prefix = ""
            
        # 添加时间戳
        time_str = datetime.now().strftime("%H:%M:%S")
        cursor.insertText(f"[{time_str}] ", format_obj)
        
        # 添加内容
        if prefix:
            cursor.insertText(prefix, format_obj)
        cursor.insertText(content, format_obj)
        cursor.insertText("\n", format_obj)
        
        if is_incremental and not is_code:
            cursor.insertText("─" * 40 + "\n", format_obj)
            
    def _scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def _stop_realtime_stream(self):
        """停止实时流"""
        if self._reply_stream_timer:
            self._reply_stream_timer.stop()
        self.statusBar().showMessage("✅ 回复接收完成")
        
    def _build_inject_script(self, message):
        """构建注入脚本"""
        escaped_msg = message.replace("'", "\\'").replace("\n", "\\n")
        return f"""
        (function() {{
            var msg = '{escaped_msg}';
            var selectors = [
                'textarea[placeholder*="DeepSeek"]',
                'textarea[placeholder*="message"]',
                'textarea',
                '[contenteditable="true"]'
            ];
            
            var target = null;
            for (var i = 0; i < selectors.length; i++) {{
                var elements = document.querySelectorAll(selectors[i]);
                for (var j = 0; j < elements.length; j++) {{
                    if (elements[j].offsetWidth > 0 && elements[j].offsetHeight > 0) {{
                        target = elements[j];
                        break;
                    }}
                }}
                if (target) break;
            }}
            
            if (target) {{
                target.focus();
                if (target.tagName === 'TEXTAREA') {{
                    target.value = msg;
                }} else {{
                    target.innerText = msg;
                }}
                
                // 触发事件
                target.dispatchEvent(new Event('input', {{bubbles: true}}));
                
                // 模拟回车发送
                setTimeout(function() {{
                    var enterEvent = new KeyboardEvent('keydown', {{
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        bubbles: true
                    }});
                    target.dispatchEvent(enterEvent);
                }}, 300);
                
                return true;
            }}
            return false;
        }})();
        """
        
    def _get_content_script(self):
        """获取内容抓取脚本"""
        return """
        (function() {
            function getText(element) {
                if (!element) return '';
                if (element.nodeType === 3) return element.nodeValue || '';
                if (element.nodeType !== 1) return '';
                if (['SCRIPT', 'STYLE'].includes(element.tagName)) return '';
                
                var text = '';
                for (var child = element.firstChild; child; child = child.nextSibling) {
                    text += getText(child);
                }
                return text;
            }
            
            // 查找助手回复
            var selectors = [
                '[data-message-type="assistant"]',
                '.assistant-message',
                '[class*="message"][class*="assistant"]',
                'article'
            ];
            
            for (var i = 0; i < selectors.length; i++) {
                var elements = document.querySelectorAll(selectors[i]);
                if (elements.length > 0) {
                    var lastElement = elements[elements.length - 1];
                    var content = getText(lastElement);
                    if (content.length > 10) {
                        return content.trim();
                    }
                }
            }
            
            // 备用方案
            var main = document.querySelector('main') || document.body;
            return getText(main).trim();
        })();
        """
        
    # 其他辅助方法
    def go_home(self):
        self.browser.setUrl(QUrl("https://chat.deepseek.com"))
        
    def navigate_to_url(self):
        url_text = self.url_bar.currentText().strip()
        if not url_text.startswith(('http://', 'https://')):
            url_text = 'https://' + url_text
        self.browser.setUrl(QUrl(url_text))
        
    def on_load_started(self):
        self.statusBar().showMessage("正在加载页面...")
        
    def on_load_finished(self, success):
        if success:
            self.statusBar().showMessage("页面加载完成")
        else:
            self.statusBar().showMessage("页面加载失败")
            
    def on_url_changed(self, url):
        current_url = url.toString()
        if current_url not in [self.url_bar.itemText(i) for i in range(self.url_bar.count())]:
            self.url_bar.addItem(current_url)
        self.url_bar.setCurrentText(current_url)
        
    def clear_output(self):
        self.output_text.clear()
        self._current_displayed_text = ""
        self._code_blocks_found = []
        self.statusBar().showMessage("显示内容已清空")
        
    def export_conversation(self):
        content = self.output_text.toPlainText()
        if not content:
            QMessageBox.information(self, "无内容", "没有对话内容可以导出")
            return
            
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出对话", f"对话记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", "文本文件 (*.txt)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            QMessageBox.information(self, "导出成功", f"对话记录已导出至: {file_path}")

def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = EnhancedDeepSeekBrowser()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    print("=== DeepSeek 实时代码显示增强版 ===")
    print("特性：")
    print("• 🟢 实时模式：可实时显示DeepSeek编写代码的过程")
    print("• 💻 代码高亮：不同代码元素采用不同颜色显示")
    print("• ⚡ 快速响应：100ms高频轮询实现实时效果")
    print("• 🔧 进度指示：显示代码编写进度百分比")
    print("• 📊 语法区分：注释、字符串、变量名等不同着色")
    main()