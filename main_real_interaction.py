#!/usr/bin/env python3
"""
DeepSeek Qt浏览器 - 真实交互版
真正与deepseek网站交互，发送消息并获取回复
"""

import sys
import time
import random
from datetime import datetime
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QSplitter, QMessageBox,
    QGroupBox, QFrame, QProgressBar, QComboBox, QCheckBox
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor, QPalette


class WebPage(QWebEnginePage):
    """自定义Web页面，用于处理JavaScript交互"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        """处理JavaScript控制台消息"""
        print(f"JS [{level}]: {message} (line {line_number})")


class RealInteractionDeepSeekBrowser(QMainWindow):
    """真实交互版主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.conversation_history = []
        self.is_processing = False
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("DeepSeek Qt浏览器 - 真实交互版")
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：Web浏览器面板
        browser_panel = self.create_browser_panel()
        splitter.addWidget(browser_panel)
        
        # 右侧：对话和控制面板
        chat_panel = self.create_chat_panel()
        splitter.addWidget(chat_panel)
        
        # 设置分割器初始比例
        splitter.setSizes([900, 500])
        
        # 将分割器添加到主布局
        main_layout.addWidget(splitter)
        
        # 状态栏
        self.status_label = QLabel("就绪 - 已加载DeepSeek聊天页面")
        self.statusBar().addPermanentWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)
        
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
        
        self.url_bar = QComboBox()
        self.url_bar.setEditable(True)
        self.url_bar.addItem("https://chat.deepseek.com")
        self.url_bar.addItem("https://www.deepseek.com")
        self.url_bar.addItem("https://www.deepseek.com/zh")
        # 设置地址栏文字颜色为黑色
        self.url_bar.setStyleSheet("""
            QComboBox {
                color: #000000;  /* 黑色文字 */
                background-color: #ffffff;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox QAbstractItemView {
                color: #000000;  /* 下拉列表文字颜色 */
                background-color: #ffffff;
            }
        """)
        
        self.go_button = QPushButton("前往")
        
        # 设置按钮样式
        for btn in [self.back_button, self.forward_button, self.refresh_button, 
                   self.home_button, self.go_button]:
            btn.setMaximumWidth(60)
            btn.setStyleSheet("""
                QPushButton {
                    padding: 5px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: #f5f5f5;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
        
        control_layout.addWidget(self.back_button)
        control_layout.addWidget(self.forward_button)
        control_layout.addWidget(self.refresh_button)
        control_layout.addWidget(self.home_button)
        control_layout.addWidget(QLabel("地址:"))
        control_layout.addWidget(self.url_bar, 1)
        control_layout.addWidget(self.go_button)
        
        layout.addLayout(control_layout)
        
        # Web浏览器 - 使用自定义页面
        self.browser = QWebEngineView()
        self.page = WebPage(self.browser)
        self.browser.setPage(self.page)
        
        # 获取页面设置
        settings = self.browser.settings()
        
        # 关键设置：启用所有必要的JavaScript和交互功能
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)
        
        # 启用现代Web功能
        settings.setAttribute(QWebEngineSettings.WebAttribute.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        
        # 允许跨域请求（重要！）
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        
        # 设置默认URL
        self.browser.setUrl(QUrl("https://chat.deepseek.com"))
        
        layout.addWidget(self.browser, 1)
        
        return panel
        
    def create_chat_panel(self):
        """创建对话面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("DeepSeek 真实交互对话")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(title_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #bdc3c7;")
        layout.addWidget(line)
        
        # 交互状态
        status_group = QGroupBox("交互状态")
        status_layout = QVBoxLayout()
        
        self.interaction_status = QLabel("等待页面加载完成...")
        self.interaction_status.setStyleSheet("""
            QLabel {
                padding: 8px;
                border-radius: 4px;
                background-color: #f0f0f0;
            }
        """)
        
        self.page_ready_check = QCheckBox("页面已准备就绪")
        self.page_ready_check.setEnabled(False)
        self.page_ready_check.setChecked(False)
        
        status_layout.addWidget(self.interaction_status)
        status_layout.addWidget(self.page_ready_check)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 设置组
        settings_group = QGroupBox("对话设置")
        settings_layout = QVBoxLayout()
        
        # 交互模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("交互模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["自动填写", "模拟点击", "JavaScript注入"])
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        settings_layout.addLayout(mode_layout)
        
        # 选项
        self.auto_scroll_check = QCheckBox("自动滚动到最新消息")
        self.auto_scroll_check.setChecked(True)
        self.save_history_check = QCheckBox("保存对话历史")
        self.save_history_check.setChecked(True)
        self.auto_detect_check = QCheckBox("自动检测页面元素")
        self.auto_detect_check.setChecked(True)
        
        settings_layout.addWidget(self.auto_scroll_check)
        settings_layout.addWidget(self.save_history_check)
        settings_layout.addWidget(self.auto_detect_check)
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 对话历史框
        history_label = QLabel("对话历史:")
        layout.addWidget(history_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("真实对话历史将显示在这里...")
        self.output_text.setMinimumHeight(250)
        
        # 设置对话历史框样式
        self.output_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                background-color: #f9f9f9;
            }
        """)
        layout.addWidget(self.output_text, 1)
        
        # 输入框
        input_label = QLabel("输入您的问题:")
        layout.addWidget(input_label)
        
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("在这里输入您的问题...（按Ctrl+Enter发送）")
        self.input_text.setMaximumHeight(100)
        self.input_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                color: #333333;  /* 确保文字颜色可见 */
                background-color: #ffffff;
            }
            QTextEdit:focus {
                border-color: #2980b9;
                background-color: #f8f9fa;
            }
        """)
        layout.addWidget(self.input_text)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.send_button = QPushButton("发送到网页 (Ctrl+Enter)")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        
        self.clear_button = QPushButton("清空历史")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 13px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        self.test_button = QPushButton("测试交互")
        self.test_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 13px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        
        button_layout.addWidget(self.send_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.test_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 状态提示
        self.chat_status = QLabel("等待页面加载...")
        self.chat_status.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(self.chat_status)
        
        return panel
        
    def setup_connections(self):
        """设置信号和槽的连接"""
        # 浏览器控制
        self.back_button.clicked.connect(self.browser.back)
        self.forward_button.clicked.connect(self.browser.forward)
        self.refresh_button.clicked.connect(self.browser.reload)
        self.home_button.clicked.connect(self.go_home)
        self.go_button.clicked.connect(self.navigate_to_url)
        self.url_bar.lineEdit().returnPressed.connect(self.navigate_to_url)
        
        # 对话功能
        self.send_button.clicked.connect(self.send_message_to_website)
        self.clear_button.clicked.connect(self.clear_conversation)
        self.test_button.clicked.connect(self.test_interaction)
        
        # 浏览器信号
        self.browser.loadStarted.connect(self.on_load_started)
        self.browser.loadProgress.connect(self.on_load_progress)
        self.browser.loadFinished.connect(self.on_load_finished)
        self.browser.urlChanged.connect(self.on_url_changed)
        
        # 快捷键
        self.send_button.setShortcut("Ctrl+Return")
        
    def on_load_started(self):
        """浏览器开始加载页面"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在加载页面...")
        self.chat_status.setText("页面加载中...")
        self.page_ready_check.setChecked(False)
        # 保持按钮可用，但添加提示
        self.send_button.setEnabled(True)
        self.send_button.setToolTip("页面正在加载，请稍后...")
        
    def on_load_progress(self, progress):
        """浏览器加载进度"""
        self.progress_bar.setValue(progress)
        
    def on_load_finished(self, success):
        """浏览器完成加载页面"""
        self.progress_bar.setVisible(False)
        if success:
            self.status_label.setText(f"页面加载完成 - {self.browser.url().toString()}")
            self.chat_status.setText("页面加载完成，正在检测交互元素...")
            
            # 页面加载完成后，检测交互元素
            QTimer.singleShot(2000, self.detect_page_elements)
        else:
            self.status_label.setText("页面加载失败")
            self.chat_status.setText("页面加载失败")
            QMessageBox.warning(self, "加载失败", "无法加载页面，请检查网络连接或URL地址")
            
    def on_url_changed(self, url):
        """URL变化"""
        current_url = url.toString()
        if current_url not in [self.url_bar.itemText(i) for i in range(self.url_bar.count())]:
            self.url_bar.addItem(current_url)
        self.url_bar.setCurrentText(current_url)
        
    def detect_page_elements(self):
        """检测页面交互元素"""
        self.chat_status.setText("正在检测页面交互元素...")
        
        # 注入JavaScript来检测页面元素
        detection_script = """
        // 检测deepseek聊天页面的交互元素
        console.log('开始检测deepseek页面元素...');
        
        // 查找可能的输入框
        var textareas = document.querySelectorAll('textarea');
        var inputs = document.querySelectorAll('input[type="text"], input[type="search"]');
        var contentEditable = document.querySelectorAll('[contenteditable="true"]');
        
        var elements = {
            textareas: [],
            inputs: [],
            contentEditable: []
        };
        
        // 处理文本区域
        for (var i = 0; i < textareas.length; i++) {
            var el = textareas[i];
            elements.textareas.push({
                id: el.id,
                className: el.className,
                placeholder: el.placeholder,
                tagName: el.tagName
            });
        }
        
        // 处理输入框
        for (var j = 0; j < inputs.length; j++) {
            var el = inputs[j];
            elements.inputs.push({
                id: el.id,
                className: el.className,
                placeholder: el.placeholder,
                tagName: el.tagName
            });
        }
        
        // 处理可编辑元素
        for (var k = 0; k < contentEditable.length; k++) {
            var el = contentEditable[k];
            elements.contentEditable.push({
                id: el.id,
                className: el.className,
                tagName: el.tagName
            });
        }
        
        // 查找可能的发送按钮
        var buttons = document.querySelectorAll('button');
        var sendButtons = [];
        for (var i = 0; i < buttons.length; i++) {
            var btn = buttons[i];
            var text = btn.innerText || btn.textContent || btn.value || '';
            if (text.toLowerCase().includes('send') || 
                text.toLowerCase().includes('发送') ||
                text.includes('➤') ||
                (btn.className && btn.className.toLowerCase().includes('send')) ||
                (btn.id && btn.id.toLowerCase().includes('send'))) {
                sendButtons.push({
                    id: btn.id,
                    className: btn.className,
                    text: text,
                    tagName: btn.tagName
                });
            }
        }
        
        elements.sendButtons = sendButtons;
        
        // 查找消息容器
        var messageContainers = document.querySelectorAll('.message, .chat-message, .conversation, .messages');
        elements.messageContainers = [];
        for (var l = 0; l < messageContainers.length; l++) {
            var container = messageContainers[l];
            elements.messageContainers.push({
                id: container.id,
                className: container.className,
                tagName: container.tagName
            });
        }
        
        console.log('检测到的元素:', elements);
        return elements;
        """
        
        self.browser.page().runJavaScript(detection_script, self.on_elements_detected)
        
    def on_elements_detected(self, result):
        """处理检测到的元素"""
        if result:
            textareas_count = len(result.get('textareas', []))
            inputs_count = len(result.get('inputs', []))
            send_buttons_count = len(result.get('sendButtons', []))
            
            self.chat_status.setText(f"检测到 {textareas_count} 个文本区域，{inputs_count} 个输入框，{send_buttons_count} 个发送按钮")
            
            if textareas_count > 0 or inputs_count > 0:
                self.page_ready_check.setChecked(True)
                self.send_button.setEnabled(True)
                self.interaction_status.setText("页面已准备就绪，可以发送消息")
                self.interaction_status.setStyleSheet("""
                    QLabel {
                        padding: 8px;
                        border-radius: 4px;
                        background-color: #d4edda;
                        color: #155724;
                    }
                """)
            else:
                self.interaction_status.setText("未找到输入框，可能需要手动操作")
                self.interaction_status.setStyleSheet("""
                    QLabel {
                        padding: 8px;
                        border-radius: 4px;
                        background-color: #fff3cd;
                        color: #856404;
                    }
                """)
        else:
            self.chat_status.setText("元素检测失败")
            self.interaction_status.setText("无法检测页面元素")
            
    def go_home(self):
        """返回首页"""
        self.browser.setUrl(QUrl("https://chat.deepseek.com"))
        
    def navigate_to_url(self):
        """导航到指定URL"""
        url_text = self.url_bar.currentText().strip()
        if not url_text.startswith(('http://', 'https://')):
            url_text = 'https://' + url_text
            
        self.browser.setUrl(QUrl(url_text))
        
    def send_message_to_website(self):
        """发送消息到网站"""
        if self.is_processing:
            QMessageBox.warning(self, "正在处理", "请等待当前消息处理完成")
            return
            
        message = self.input_text.toPlainText().strip()
        
        if not message:
            QMessageBox.warning(self, "输入为空", "请输入您的问题")
            return
            
        # 禁用发送按钮，防止重复发送
        self.is_processing = True
        self.send_button.setEnabled(False)
        self.chat_status.setText("正在发送消息到网页...")
        
        # 添加用户消息到历史
        self.add_message_to_history("user", message)
        
        # 清空输入框
        self.input_text.clear()
        
        # 根据选择的模式发送消息
        mode = self.mode_combo.currentText()
        
        if mode == "自动填写":
            self.auto_fill_message(message)
        elif mode == "模拟点击":
            self.simulate_click_message(message)
        else:  # JavaScript注入
            self.js_inject_message(message)
            
    def auto_fill_message(self, message):
        """自动填写消息到网页输入框"""
        # 改进的自动填写脚本
        improved_fill_script = f"""
        // 改进的自动填写方法
        console.log('改进自动填写消息: {message}');
        
        // 使用更智能的选择器
        var selectors = [
            'textarea[placeholder*="输入"]',
            'textarea[placeholder*="message"]',
            'textarea[placeholder*="说点什么"]',
            'textarea',
            'input[type="text"]',
            'input[type="search"]',
            '[contenteditable="true"]',
            '.ProseMirror',
            '.chat-input',
            '.message-input',
            '[role="textbox"]',
            '[data-testid="chat-input"]'
        ];
        
        var targetElement = null;
        
        // 首先尝试查找有焦点的元素
        if (document.activeElement && 
            (document.activeElement.tagName === 'TEXTAREA' || 
             document.activeElement.tagName === 'INPUT' ||
             document.activeElement.contentEditable === 'true' ||
             document.activeElement.getAttribute('role') === 'textbox')) {{
            targetElement = document.activeElement;
            console.log('使用当前焦点元素:', targetElement.tagName, targetElement.className);
        }}
        
        // 如果没有焦点元素，尝试所有选择器
        if (!targetElement) {{
            for (var i = 0; i < selectors.length; i++) {{
                var elements = document.querySelectorAll(selectors[i]);
                for (var j = 0; j < elements.length; j++) {{
                    var el = elements[j];
                    if (el.offsetWidth > 0 && el.offsetHeight > 0) {{
                        targetElement = el;
                        console.log('找到目标元素:', selectors[i], el.tagName, el.className);
                        break;
                    }}
                }}
                if (targetElement) break;
            }}
        }}
        
        if (targetElement) {{
            // 设置值
            if (targetElement.tagName === 'TEXTAREA' || targetElement.tagName === 'INPUT') {{
                targetElement.value = '{message}';
            }} else if (targetElement.contentEditable === 'true') {{
                targetElement.innerText = '{message}';
                targetElement.textContent = '{message}';
            }} else {{
                // 对于其他元素，尝试多种设置值的方法
                targetElement.value = '{message}';
                targetElement.innerText = '{message}';
                targetElement.textContent = '{message}';
            }}
            
            // 触发所有必要的事件
            var events = ['input', 'change', 'keydown', 'keypress', 'keyup'];
            for (var k = 0; k < events.length; k++) {{
                try {{
                    var event = new Event(events[k], {{ bubbles: true, cancelable: true }});
                    targetElement.dispatchEvent(event);
                }} catch (e) {{
                    console.log('触发事件失败:', events[k], e);
                }}
            }}
            
            // 查找并点击发送按钮
            var buttonSelectors = [
                'button[type="submit"]',
                'button[class*="send"]',
                'button[class*="submit"]',
                'button[aria-label*="send"]',
                'button[aria-label*="发送"]',
                '[data-testid="send-button"]',
                '.send-button',
                '.submit-button',
                'button', // 回退到所有按钮
                '[role="button"]' // 回退到角色为按钮的元素
            ];
            
            var clicked = false;
            
            // 延迟执行，确保输入事件已处理
            setTimeout(function() {{
                for (var l = 0; l < buttonSelectors.length; l++) {{
                    try {{
                        var buttons = document.querySelectorAll(buttonSelectors[l]);
                        for (var m = 0; m < buttons.length; m++) {{
                            var btn = buttons[m];
                            if (btn.offsetWidth > 0 && btn.offsetHeight > 0) {{
                                console.log('找到发送按钮:', buttonSelectors[l], btn.tagName, btn.className);
                                btn.click();
                                clicked = true;
                                break;
                            }}
                        }}
                    }} catch (e) {{
                        console.log('查找按钮失败:', buttonSelectors[l], e);
                    }}
                    if (clicked) break;
                }}
                
                // 如果没有找到按钮，尝试表单提交
                if (!clicked) {{
                    var form = targetElement.closest('form');
                    if (form) {{
                        console.log('找到表单，尝试提交');
                        form.submit();
                        clicked = true;
                    }}
                }}
                
                // 如果还没有点击，尝试触发回车事件
                if (!clicked) {{
                    try {{
                        var enterEvent = new KeyboardEvent('keydown', {{
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            charCode: 13,
                            bubbles: true,
                            cancelable: true
                        }});
                        targetElement.dispatchEvent(enterEvent);
                        clicked = true;
                    }} catch (e) {{
                        console.log('触发回车事件失败:', e);
                    }}
                }}
                
                return clicked;
            }}, 300);
            
            return true;
        }} else {{
            console.log('未找到合适的输入元素');
            return false;
        }}
        """
        
        self.browser.page().runJavaScript(improved_fill_script, self.on_message_sent)
        
    def simulate_click_message(self, message):
        """模拟点击方式发送消息"""
        # 改进的脚本：直接设置值并触发所有必要事件
        improved_script = f"""
        // 改进的模拟点击方法
        console.log('改进模拟点击发送消息: {message}');
        
        // 查找deepseek聊天页面的特定元素
        // 尝试多种选择器来匹配当前页面结构
        var selectors = [
            'textarea[placeholder*="输入"]',
            'textarea[placeholder*="message"]',
            'textarea[placeholder*="说点什么"]',
            'textarea',
            'input[type="text"]',
            'input[type="search"]',
            '[contenteditable="true"]',
            '.ProseMirror',
            '.chat-input',
            '.message-input'
        ];
        
        var targetElement = null;
        
        for (var i = 0; i < selectors.length; i++) {{
            var elements = document.querySelectorAll(selectors[i]);
            for (var j = 0; j < elements.length; j++) {{
                var el = elements[j];
                if (el.offsetWidth > 0 && el.offsetHeight > 0) {{
                    targetElement = el;
                    console.log('找到目标元素:', selectors[i], el.tagName, el.className);
                    break;
                }}
            }}
            if (targetElement) break;
        }}
        
        if (targetElement) {{
            // 聚焦到元素
            targetElement.focus();
            
            // 设置值
            if (targetElement.tagName === 'TEXTAREA' || targetElement.tagName === 'INPUT') {{
                targetElement.value = '{message}';
            }} else if (targetElement.contentEditable === 'true') {{
                targetElement.innerText = '{message}';
                targetElement.textContent = '{message}';
            }} else {{
                // 对于其他元素，尝试多种设置值的方法
                targetElement.value = '{message}';
                targetElement.innerText = '{message}';
                targetElement.textContent = '{message}';
            }}
            
            // 触发所有必要的事件
            var events = ['input', 'change', 'keydown', 'keypress', 'keyup', 'blur', 'focus'];
            for (var k = 0; k < events.length; k++) {{
                try {{
                    var event = new Event(events[k], {{ bubbles: true, cancelable: true }});
                    targetElement.dispatchEvent(event);
                }} catch (e) {{
                    console.log('触发事件失败:', events[k], e);
                }}
            }}
            
            // 尝试触发回车键事件（Enter键）
            try {{
                var enterEvent = new KeyboardEvent('keydown', {{
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    charCode: 13,
                    bubbles: true,
                    cancelable: true
                }});
                targetElement.dispatchEvent(enterEvent);
                
                var enterEvent2 = new KeyboardEvent('keypress', {{
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    charCode: 13,
                    bubbles: true,
                    cancelable: true
                }});
                targetElement.dispatchEvent(enterEvent2);
                
                var enterEvent3 = new KeyboardEvent('keyup', {{
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    charCode: 13,
                    bubbles: true,
                    cancelable: true
                }});
                targetElement.dispatchEvent(enterEvent3);
            }} catch (e) {{
                console.log('触发回车事件失败:', e);
            }}
            
            // 查找并点击发送按钮
            var buttonSelectors = [
                'button[type="submit"]',
                'button svg', // 包含图标的按钮
                'button[class*="send"]',
                'button[class*="submit"]',
                'button[aria-label*="send"]',
                'button[aria-label*="发送"]',
                'button', // 回退到所有按钮
                '[role="button"]' // 回退到角色为按钮的元素
            ];
            
            var clicked = false;
            
            // 方法1：直接查找按钮
            for (var l = 0; l < buttonSelectors.length; l++) {{
                try {{
                    var buttons = document.querySelectorAll(buttonSelectors[l]);
                    for (var m = 0; m < buttons.length; m++) {{
                        var btn = buttons[m];
                        if (btn.offsetWidth > 0 && btn.offsetHeight > 0) {{
                            console.log('找到发送按钮:', buttonSelectors[l], btn.tagName, btn.className);
                            btn.click();
                            clicked = true;
                            break;
                        }}
                    }}
                }} catch (e) {{
                    console.log('查找按钮失败:', buttonSelectors[l], e);
                }}
                if (clicked) break;
            }}
            
            // 方法2：通过表单提交
            if (!clicked) {{
                var form = targetElement.closest('form');
                if (form) {{
                    console.log('找到表单，尝试提交');
                    form.submit();
                    clicked = true;
                }}
            }}
            
            // 方法3：模拟Ctrl+Enter（如果页面支持）
            if (!clicked) {{
                try {{
                    var ctrlEnterEvent = new KeyboardEvent('keydown', {{
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        charCode: 13,
                        ctrlKey: true,
                        bubbles: true,
                        cancelable: true
                    }});
                    targetElement.dispatchEvent(ctrlEnterEvent);
                    clicked = true;
                }} catch (e) {{
                    console.log('模拟Ctrl+Enter失败:', e);
                }}
            }}
            
            return clicked;
        }} else {{
            console.log('未找到合适的输入元素');
            return false;
        }}
        """
        
        self.browser.page().runJavaScript(improved_script, self.on_message_sent)
            
    def js_inject_message(self, message):
        """通过JavaScript注入方式发送消息"""
        # 改进的JavaScript注入脚本
        improved_inject_script = f"""
        // 改进的JavaScript注入方法
        console.log('改进JS注入发送消息: {message}');
        
        // 使用多种选择器查找输入元素
        var inputSelectors = [
            'textarea[placeholder*="输入"]',
            'textarea[placeholder*="message"]',
            'textarea[placeholder*="说点什么"]',
            'textarea',
            'input[type="text"]',
            'input[type="search"]',
            '[contenteditable="true"]',
            '.ProseMirror',
            '.chat-input',
            '.message-input',
            '[role="textbox"]',
            '[data-testid="chat-input"]',
            '.chat-textarea',
            '.message-textarea'
        ];
        
        var targetElement = null;
        
        // 查找输入元素
        for (var i = 0; i < inputSelectors.length; i++) {{
            var elements = document.querySelectorAll(inputSelectors[i]);
            for (var j = 0; j < elements.length; j++) {{
                var el = elements[j];
                if (el.offsetWidth > 0 && el.offsetHeight > 0) {{
                    targetElement = el;
                    console.log('找到输入元素:', inputSelectors[i], el.tagName, el.className);
                    break;
                }}
            }}
            if (targetElement) break;
        }}
        
        if (targetElement) {{
            // 保存原始值（用于恢复）
            var originalValue = targetElement.value || targetElement.innerText || targetElement.textContent;
            
            // 设置值
            if (targetElement.tagName === 'TEXTAREA' || targetElement.tagName === 'INPUT') {{
                targetElement.value = '{message}';
            }} else if (targetElement.contentEditable === 'true') {{
                targetElement.innerText = '{message}';
                targetElement.textContent = '{message}';
            }} else {{
                // 对于其他元素，尝试多种设置值的方法
                targetElement.value = '{message}';
                targetElement.innerText = '{message}';
                targetElement.textContent = '{message}';
            }}
            
            // 触发所有必要的事件
            var events = ['input', 'change', 'keydown', 'keypress', 'keyup', 'blur', 'focus'];
            for (var k = 0; k < events.length; k++) {{
                try {{
                    var event = new Event(events[k], {{ bubbles: true, cancelable: true }});
                    targetElement.dispatchEvent(event);
                }} catch (e) {{
                    console.log('触发事件失败:', events[k], e);
                }}
            }}
            
            // 特别触发input事件多次（某些网站需要）
            for (var l = 0; l < 3; l++) {{
                setTimeout(function() {{
                    try {{
                        var inputEvent = new Event('input', {{ bubbles: true, cancelable: true }});
                        targetElement.dispatchEvent(inputEvent);
                    }} catch (e) {{
                        console.log('重复触发input事件失败:', e);
                    }}
                }}, l * 100);
            }}
            
            // 查找发送按钮
            var buttonSelectors = [
                'button[type="submit"]',
                'button svg',
                'button[class*="send"]',
                'button[class*="submit"]',
                'button[aria-label*="send"]',
                'button[aria-label*="发送"]',
                '[data-testid="send-button"]',
                '.send-button',
                '.submit-button',
                '[aria-label*="发送消息"]',
                '[title*="发送"]',
                'button', // 回退到所有按钮
                '[role="button"]' // 回退到角色为按钮的元素
            ];
            
            var clicked = false;
            
            // 延迟执行，确保事件已处理
            setTimeout(function() {{
                // 方法1：查找并点击按钮
                for (var m = 0; m < buttonSelectors.length; m++) {{
                    try {{
                        var buttons = document.querySelectorAll(buttonSelectors[m]);
                        for (var n = 0; n < buttons.length; n++) {{
                            var btn = buttons[n];
                            if (btn.offsetWidth > 0 && btn.offsetHeight > 0) {{
                                console.log('找到发送按钮:', buttonSelectors[m], btn.tagName, btn.className);
                                btn.click();
                                clicked = true;
                                break;
                            }}
                        }}
                    }} catch (e) {{
                        console.log('查找按钮失败:', buttonSelectors[m], e);
                    }}
                    if (clicked) break;
                }}
                
                // 方法2：表单提交
                if (!clicked) {{
                    var form = targetElement.closest('form');
                    if (form) {{
                        console.log('找到表单，尝试提交');
                        form.submit();
                        clicked = true;
                    }}
                }}
                
                // 方法3：触发回车事件
                if (!clicked) {{
                    try {{
                        var enterEvent = new KeyboardEvent('keydown', {{
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            charCode: 13,
                            bubbles: true,
                            cancelable: true
                        }});
                        targetElement.dispatchEvent(enterEvent);
                        
                        // 也尝试Ctrl+Enter
                        var ctrlEnterEvent = new KeyboardEvent('keydown', {{
                            key: 'Enter',
                            code: 'Enter',
                            keyCode: 13,
                            charCode: 13,
                            ctrlKey: true,
                            bubbles: true,
                            cancelable: true
                        }});
                        targetElement.dispatchEvent(ctrlEnterEvent);
                        clicked = true;
                    }} catch (e) {{
                        console.log('触发回车事件失败:', e);
                    }}
                }}
                
                // 方法4：如果以上都失败，尝试直接调用可能的提交函数
                if (!clicked) {{
                    try {{
                        // 尝试调用常见的提交函数
                        if (typeof window.submitMessage === 'function') {{
                            window.submitMessage('{message}');
                            clicked = true;
                        }} else if (typeof window.sendMessage === 'function') {{
                            window.sendMessage('{message}');
                            clicked = true;
                        }} else if (typeof window.chatSubmit === 'function') {{
                            window.chatSubmit('{message}');
                            clicked = true;
                        }}
                    }} catch (e) {{
                        console.log('调用提交函数失败:', e);
                    }}
                }}
                
                // 恢复原始值（如果发送失败）
                if (!clicked) {{
                    console.log('发送失败，恢复原始值');
                    if (targetElement.tagName === 'TEXTAREA' || targetElement.tagName === 'INPUT') {{
                        targetElement.value = originalValue;
                    }} else if (targetElement.contentEditable === 'true') {{
                        targetElement.innerText = originalValue;
                        targetElement.textContent = originalValue;
                    }}
                }}
                
                return clicked;
            }}, 500);
            
            return true;
        }} else {{
            console.log('未找到合适的输入元素');
            return false;
        }}
        """
        
        self.browser.page().runJavaScript(improved_inject_script, self.on_message_sent)
        
    def on_message_sent(self, success):
        """消息发送后的处理"""
        if success:
            self.chat_status.setText("消息已发送到网页，等待回复...")
            # 开始监控回复
            QTimer.singleShot(3000, self.monitor_response)
        else:
            self.chat_status.setText("消息发送失败，请尝试手动操作")
            self.is_processing = False
            self.send_button.setEnabled(True)
            
    def monitor_response(self):
        """监控网页回复"""
        self.chat_status.setText("正在监控网页回复...")
        
        # 注入JavaScript来检查是否有新回复
        monitor_script = """
        // 监控deepseek的回复
        console.log('开始监控回复...');
        
        // 查找消息容器
        var messageContainers = document.querySelectorAll('.message, .chat-message, .conversation, .messages, [class*="message"], [class*="chat"]');
        
        var latestMessages = [];
        
        for (var i = 0; i < messageContainers.length; i++) {
            var container = messageContainers[i];
            // 获取最近的消息
            var messages = container.querySelectorAll('div, p, span');
            for (var j = Math.max(0, messages.length - 5); j < messages.length; j++) {
                var msg = messages[j];
                var text = msg.innerText || msg.textContent || '';
                if (text.trim().length > 10 && !text.includes('正在思考') && !text.includes('正在输入')) {
                    latestMessages.push({
                        text: text.trim(),
                        element: msg
                    });
                }
            }
        }
        
        // 去重并返回
        var uniqueMessages = [];
        var seenTexts = new Set();
        
        for (var k = 0; k < latestMessages.length; k++) {
            var msg = latestMessages[k];
            if (!seenTexts.has(msg.text)) {
                seenTexts.add(msg.text);
                uniqueMessages.push(msg);
            }
        }
        
        console.log('找到的消息:', uniqueMessages);
        return uniqueMessages.slice(-3); // 返回最近3条消息
        """
        
        self.browser.page().runJavaScript(monitor_script, self.on_response_detected)
        
    def on_response_detected(self, messages):
        """处理检测到的回复"""
        if messages and len(messages) > 0:
            # 获取最新的AI回复（假设最后一条是AI的回复）
            latest_message = messages[-1]
            response_text = latest_message.get('text', '')
            
            if response_text and len(response_text) > 20:  # 确保是有效的回复
                self.add_message_to_history("ai", response_text)
                self.chat_status.setText("收到网页回复")
                
                # 保存到对话历史
                if self.save_history_check.isChecked():
                    self.conversation_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "ai": response_text,
                        "source": "网页"
                    })
                
                # 自动滚动
                if self.auto_scroll_check.isChecked():
                    self.scroll_to_bottom()
                    
                self.is_processing = False
                self.send_button.setEnabled(True)
                return
                
        # 如果没有检测到回复，继续监控
        self.chat_status.setText("等待回复中...")
        QTimer.singleShot(2000, self.monitor_response)
        
    def test_interaction(self):
        """测试交互功能"""
        test_message = "你好，这是一个测试消息。请回复'测试成功'。"
        self.input_text.setPlainText(test_message)
        self.send_message_to_website()
        
    def add_message_to_history(self, sender, message):
        """添加消息到对话历史"""
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # 设置消息样式
        format = QTextCharFormat()
        
        if sender == "user":
            format.setForeground(QColor("#2c3e50"))  # 深蓝色
            format.setFontWeight(QFont.Weight.Bold)
            prefix = "您 (发送到网页): "
        else:
            format.setForeground(QColor("#27ae60"))  # 绿色
            format.setFontItalic(True)
            prefix = "DeepSeek (网页回复): "
            
        # 添加时间戳
        time_str = datetime.now().strftime("%H:%M:%S")
        cursor.insertText(f"[{time_str}] ", format)
        
        # 添加消息
        cursor.insertText(f"{prefix}{message}\n\n", format)
        
    def scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def clear_conversation(self):
        """清空对话历史"""
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有对话历史吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.output_text.clear()
            self.conversation_history.clear()
            self.chat_status.setText("对话历史已清空")
            
    def closeEvent(self, event):
        """关闭窗口事件"""
        if self.is_processing:
            reply = QMessageBox.question(
                self, "正在处理",
                "有消息正在处理中，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
                
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("DeepSeek Qt浏览器 - 真实交互版")
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 设置调色板
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    app.setPalette(palette)
    
    window = RealInteractionDeepSeekBrowser()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
