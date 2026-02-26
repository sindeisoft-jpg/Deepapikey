#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek网页交互调试工具
专门用来诊断网页提交问题
"""

import sys
import time
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QSplitter, QMessageBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings

class DebugDeepSeekBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("DeepSeek调试工具")
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：浏览器
        self.browser = QWebEngineView()
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        self.browser.setUrl(QUrl("https://chat.deepseek.com"))
        splitter.addWidget(self.browser)
        
        # 右侧：调试面板
        debug_panel = QWidget()
        debug_layout = QVBoxLayout(debug_panel)
        
        # 控制按钮
        self.test_button = QPushButton("测试输入框检测")
        self.test_button.clicked.connect(self.test_input_detection)
        debug_layout.addWidget(self.test_button)
        
        self.submit_button = QPushButton("测试消息提交")
        self.submit_button.clicked.connect(self.test_message_submission)
        debug_layout.addWidget(self.submit_button)
        
        # 日志显示
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        debug_layout.addWidget(QLabel("调试日志:"))
        debug_layout.addWidget(self.log_display)
        
        splitter.addWidget(debug_panel)
        splitter.setSizes([800, 400])
        layout.addWidget(splitter)
        
    def log(self, message):
        """添加日志"""
        self.log_display.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        print(message)  # 同时打印到控制台
        
    def test_input_detection(self):
        """测试输入框检测"""
        self.log("开始测试输入框检测...")
        
        detection_script = """
        // 确保页面完全加载
        if(document.readyState !== 'complete') {
            console.log('页面未完全加载，当前状态:', document.readyState);
            return {error: '页面未加载完成', readyState: document.readyState};
        }
        
        console.log('=== 开始输入框检测 ===');
        console.log('页面标题:', document.title);
        console.log('当前URL:', window.location.href);
        
        // 检测各种可能的输入元素
        var results = {
            textareas: [],
            inputs: [],
            contentEditable: [],
            classes: [],
            pageInfo: {
                title: document.title,
                url: window.location.href,
                readyState: document.readyState
            }
        };
        
        try {
            // 检测textarea
            var textareas = document.querySelectorAll('textarea');
            console.log('找到textarea元素数量:', textareas.length);
            for(var i = 0; i < textareas.length; i++) {
                var el = textareas[i];
                results.textareas.push({
                    index: i,
                    tagName: el.tagName,
                    className: el.className,
                    id: el.id,
                    placeholder: el.placeholder,
                    visible: el.offsetWidth > 0 && el.offsetHeight > 0,
                    offsetWidth: el.offsetWidth,
                    offsetHeight: el.offsetHeight,
                    outerHTML: el.outerHTML.substring(0, 100) + '...'
                });
            }
            
            // 检测input
            var inputs = document.querySelectorAll('input[type="text"], input[type="search"]');
            console.log('找到input元素数量:', inputs.length);
            for(var i = 0; i < inputs.length; i++) {
                var el = inputs[i];
                results.inputs.push({
                    index: i,
                    tagName: el.tagName,
                    className: el.className,
                    id: el.id,
                    placeholder: el.placeholder,
                    visible: el.offsetWidth > 0 && el.offsetHeight > 0,
                    offsetWidth: el.offsetWidth,
                    offsetHeight: el.offsetHeight,
                    outerHTML: el.outerHTML.substring(0, 100) + '...'
                });
            }
            
            // 检测contentEditable
            var editable = document.querySelectorAll('[contenteditable="true"]');
            console.log('找到contentEditable元素数量:', editable.length);
            for(var i = 0; i < editable.length; i++) {
                var el = editable[i];
                results.contentEditable.push({
                    index: i,
                    tagName: el.tagName,
                    className: el.className,
                    id: el.id,
                    visible: el.offsetWidth > 0 && el.offsetHeight > 0,
                    offsetWidth: el.offsetWidth,
                    offsetHeight: el.offsetHeight,
                    outerHTML: el.outerHTML.substring(0, 100) + '...'
                });
            }
            
            // 检测常见类名
            var classSelectors = ['.ProseMirror', '.chat-input', '.message-input', '[class*="input"]'];
            console.log('检测类选择器:', classSelectors);
            for(var i = 0; i < classSelectors.length; i++) {
                var elements = document.querySelectorAll(classSelectors[i]);
                console.log(classSelectors[i] + ' 找到元素数量:', elements.length);
                for(var j = 0; j < elements.length; j++) {
                    var el = elements[j];
                    results.classes.push({
                        selector: classSelectors[i],
                        index: j,
                        tagName: el.tagName,
                        className: el.className,
                        id: el.id,
                        visible: el.offsetWidth > 0 && el.offsetHeight > 0,
                        outerHTML: el.outerHTML.substring(0, 100) + '...'
                    });
                }
            }
            
            console.log('检测完成，结果:', results);
            return results;
            
        } catch(error) {
            console.error('检测过程中发生错误:', error);
            return {error: error.message, stack: error.stack};
        }
        """
        
        def on_result(result):
            self.log(f"输入框检测完成: {result}")
            if result:
                # 分析结果
                total_elements = 0
                visible_elements = 0
                
                if 'textareas' in result:
                    total_elements += len(result['textareas'])
                    visible_elements += sum(1 for el in result['textareas'] if el.get('visible', False))
                    
                if 'inputs' in result:
                    total_elements += len(result['inputs'])
                    visible_elements += sum(1 for el in result['inputs'] if el.get('visible', False))
                    
                self.log(f"总计找到元素: {total_elements}个")
                self.log(f"可见元素: {visible_elements}个")
                
                if visible_elements == 0:
                    self.log("⚠️  没有找到可见的输入元素！")
                else:
                    self.log("✅ 找到了可见的输入元素")
        
        self.browser.page().runJavaScript(detection_script, on_result)
        
    def test_message_submission(self):
        """测试消息提交"""
        self.log("开始测试消息提交...")
        
        submission_script = """
        console.log('=== 开始消息提交测试 ===');
        
        // 1. 首先检测输入元素
        var targetElement = null;
        var selectors = [
            'textarea[placeholder*="输入"]',
            'textarea[placeholder*="message"]',
            'textarea',
            'input[type="text"]',
            '[contenteditable="true"]',
            '.ProseMirror'
        ];
        
        for(var i = 0; i < selectors.length; i++) {
            var elements = document.querySelectorAll(selectors[i]);
            for(var j = 0; j < elements.length; j++) {
                var el = elements[j];
                if(el.offsetWidth > 0 && el.offsetHeight > 0) {
                    targetElement = el;
                    console.log('找到目标元素:', selectors[i], el.tagName, el.className);
                    break;
                }
            }
            if(targetElement) break;
        }
        
        if(!targetElement) {
            console.log('❌ 未找到合适的输入元素');
            return {success: false, reason: '找不到输入元素'};
        }
        
        // 2. 设置测试消息
        var testMessage = '你好，这是一个测试消息';
        console.log('设置消息:', testMessage);
        
        if(targetElement.tagName === 'TEXTAREA' || targetElement.tagName === 'INPUT') {
            targetElement.value = testMessage;
        } else if(targetElement.contentEditable === 'true') {
            targetElement.innerText = testMessage;
        }
        
        // 3. 触发事件
        targetElement.dispatchEvent(new Event('input', {bubbles: true}));
        targetElement.dispatchEvent(new Event('change', {bubbles: true}));
        
        // 4. 尝试找到发送按钮
        var sendButton = null;
        var buttonSelectors = [
            'button[type="submit"]',
            'button[aria-label*="send"]',
            'button:has(svg)',
            'button'
        ];
        
        for(var i = 0; i < buttonSelectors.length; i++) {
            var buttons = document.querySelectorAll(buttonSelectors[i]);
            for(var j = 0; j < buttons.length; j++) {
                var btn = buttons[j];
                if(btn.offsetWidth > 0 && btn.offsetHeight > 0 && !btn.disabled) {
                    sendButton = btn;
                    console.log('找到发送按钮:', btn.tagName, btn.className);
                    break;
                }
            }
            if(sendButton) break;
        }
        
        // 5. 点击发送按钮
        if(sendButton) {
            sendButton.click();
            console.log('✅ 已点击发送按钮');
            return {success: true, method: 'button_click'};
        } else {
            // 6. 如果找不到按钮，尝试回车键
            var enterEvent = new KeyboardEvent('keydown', {
                key: 'Enter',
                code: 'Enter',
                keyCode: 13,
                bubbles: true
            });
            targetElement.dispatchEvent(enterEvent);
            console.log('✅ 已触发回车事件');
            return {success: true, method: 'enter_key'};
        }
        """
        
        def on_result(result):
            self.log(f"提交测试结果: {result}")
            if result and result.get('success'):
                self.log(f"✅ 提交成功，使用方法: {result.get('method')}")
            else:
                self.log("❌ 提交失败")
        
        self.browser.page().runJavaScript(submission_script, on_result)

def main():
    app = QApplication(sys.argv)
    window = DebugDeepSeekBrowser()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()