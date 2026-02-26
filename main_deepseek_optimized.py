#!/usr/bin/env python3
"""
DeepSeek Qt浏览器 - 深度优化版
专门针对deepseek聊天页面优化的版本
"""

import sys
import time
import random
from datetime import datetime
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal, QObject
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QSplitter, QMessageBox,
    QGroupBox, QFrame, QProgressBar, QComboBox, QCheckBox, QLineEdit
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor, QPalette, QKeySequence
from PyQt6.QtCore import QEvent, QKeyEvent


class DeepSeekOptimizedBrowser(QMainWindow):
    """深度优化版主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.conversation_history = []
        self.is_processing = False
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("DeepSeek Qt浏览器 - 深度优化版")
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
                color: #000000;
                background-color: #ffffff;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox QAbstractItemView {
                color: #000000;
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
        
        # Web浏览器
        self.browser = QWebEngineView()
        
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
        title_label = QLabel("DeepSeek 深度优化对话")
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
        settings_group = QGroupBox("深度优化设置")
        settings_layout = QVBoxLayout()
        
        # 交互模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("交互策略:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["智能注入", "直接操作", "模拟用户", "暴力破解"])
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        settings_layout.addLayout(mode_layout)
        
        # 选项
        self.auto_scroll_check = QCheckBox("自动滚动到最新消息")
        self.auto_scroll_check.setChecked(True)
        self.save_history_check = QCheckBox("保存对话历史")
        self.save_history_check.setChecked(True)
        self.debug_mode_check = QCheckBox("调试模式")
        self.debug_mode_check.setChecked(False)
        
        settings_layout.addWidget(self.auto_scroll_check)
        settings_layout.addWidget(self.save_history_check)
        settings_layout.addWidget(self.debug_mode_check)
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 对话历史框
        history_label = QLabel("对话历史:")
        layout.addWidget(history_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("深度优化对话历史将显示在这里...")
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
                color: #333333;
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
        
        self.send_button = QPushButton("深度发送 (Ctrl+Enter)")
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
        
        self.test_button = QPushButton("测试深度交互")
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
        self.send_button.clicked.connect(self.deep_send_message)
        self.clear_button.clicked.connect(self.clear_conversation)
        self.test_button.clicked.connect(self.test_deep_interaction)
        
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
            self.chat_status.setText("页面加载完成，正在深度检测...")
            
            # 页面加载完成后，深度检测页面元素
            QTimer.singleShot(3000, self.deep_detect_page)
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
        
    def deep_detect_page(self):
        """深度检测页面元素"""
        self.chat_status.setText("正在深度检测deepseek页面...")
        
        # 注入深度检测JavaScript
        deep_detection_script = """
        // 深度检测deepseek聊天页面的交互元素
        console.log('开始深度检测deepseek页面元素...');
        
        // 方法1：查找所有可能的输入元素
        var allElements = document.querySelectorAll('*');
        var inputCandidates = [];
        
        for (var i = 0; i < allElements.length; i++) {
            var el = allElements[i];
            
            // 检查元素是否可能是输入框
            var isInputCandidate = false;
            var reasons = [];
            
            // 检查标签名
            if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
                isInputCandidate = true;
                reasons.push('tagName: ' + el.tagName);
            }
            
            // 检查contenteditable属性
            if (el.contentEditable === 'true' || el.contentEditable === 'plaintext-only') {
                isInputCandidate = true;
                reasons.push('contentEditable');
            }
            
            // 检查类名和ID
            var className = el.className || '';
            var id = el.id || '';
            var text = el.innerText || el.textContent || '';
            
            if (className.toLowerCase().includes('input') || 
                className.toLowerCase().includes('text') ||
                className.toLowerCase().includes('message') ||
                className.toLowerCase().includes('chat') ||
                className.toLowerCase().includes('prompt') ||
                id.toLowerCase().includes('input') ||
                id.toLowerCase().includes('text') ||
                id.toLowerCase().includes('message') ||
                id.toLowerCase().includes('chat') ||
                id.toLowerCase().includes('prompt')) {
                isInputCandidate = true;
                reasons.push('className/id: ' + className + '/' + id);
            }
            
            // 检查placeholder
            if (el.placeholder && (el.placeholder.toLowerCase().includes('message') ||
                                  el.placeholder.toLowerCase().includes('输入') ||
                                  el.placeholder.toLowerCase().includes('ask') ||
                                  el.placeholder.toLowerCase().includes('type'))) {
                isInputCandidate = true;
                reasons.push('placeholder: ' + el.placeholder);
            }
            
            // 检查aria-label
            if (el.getAttribute('aria-label') && el.getAttribute('aria-label').toLowerCase().includes('message')) {
                isInputCandidate = true;
                reasons.push('aria-label: ' + el.getAttribute('aria-label'));
            }
            
            // 检查data-testid
            if (el