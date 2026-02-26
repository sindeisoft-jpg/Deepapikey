#!/usr/bin/env python3
"""
DeepSeek页面功能诊断工具
用于诊断"新建DeepSeek页面功能失效"问题
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, QTimer

class DiagnosticBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("DeepSeek页面诊断工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧：浏览器
        browser_panel = QWidget()
        browser_layout = QVBoxLayout(browser_panel)
        
        # 浏览器控制栏
        control_layout = QHBoxLayout()
        
        self.back_button = QPushButton("←")
        self.forward_button = QPushButton("→")
        self.refresh_button = QPushButton("刷新")
        self.home_button = QPushButton("首页")
        
        self.url_bar = QTextEdit()
        self.url_bar.setMaximumHeight(30)
        self.url_bar.setText("https://chat.deepseek.com")
        
        self.go_button = QPushButton("前往")
        
        control_layout.addWidget(self.back_button)
        control_layout.addWidget(self.forward_button)
        control_layout.addWidget(self.refresh_button)
        control_layout.addWidget(self.home_button)
        control_layout.addWidget(QLabel("URL:"))
        control_layout.addWidget(self.url_bar)
        control_layout.addWidget(self.go_button)
        
        browser_layout.addLayout(control_layout)
        
        # Web浏览器
        self.browser = QWebEngineView()
        self.browser.settings().setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        self.browser.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        self.browser.settings().setAttribute(
            QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, True)
        self.browser.setUrl(QUrl("https://chat.deepseek.com"))
        
        browser_layout.addWidget(self.browser, 1)
        
        # 右侧：诊断面板
        diag_panel = QWidget()
        diag_layout = QVBoxLayout(diag_panel)
        
        # 标题
        title_label = QLabel("页面功能诊断")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        diag_layout.addWidget(title_label)
        
        # 状态显示
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setMaximumHeight(150)
        diag_layout.addWidget(QLabel("状态信息:"))
        diag_layout.addWidget(self.status_display)
        
        # 测试按钮
        test_layout = QHBoxLayout()
        
        self.test_url_button = QPushButton("测试URL导航")
        self.test_js_button = QPushButton("测试JS注入")
        self.test_elements_button = QPushButton("测试元素检测")
        
        test_layout.addWidget(self.test_url_button)
        test_layout.addWidget(self.test_js_button)
        test_layout.addWidget(self.test_elements_button)
        
        diag_layout.addLayout(test_layout)
        
        # 日志显示
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        diag_layout.addWidget(QLabel("诊断日志:"))
        diag_layout.addWidget(self.log_display)
        
        # 添加分割器
        splitter = QWidget()
        splitter_layout = QHBoxLayout(splitter)
        splitter_layout.addWidget(browser_panel)
        splitter_layout.addWidget(diag_panel)
        
        main_layout.addWidget(splitter)
        
        # 连接信号
        self.go_button.clicked.connect(self.navigate_to_url)
        self.url_bar.textChanged.connect(self.on_url_changed)
        self.test_url_button.clicked.connect(self.test_url_navigation)
        self.test_js_button.clicked.connect(self.test_js_injection)
        self.test_elements_button.clicked.connect(self.test_element_detection)
        
        self.browser.loadStarted.connect(self.on_load_started)
        self.browser.loadFinished.connect(self.on_load_finished)
        
        self.update_status("诊断工具已启动，准备就绪")
    
    def update_status(self, message):
        """更新状态显示"""
        self.status_display.setText(message)
        self.log(f"[{self.get_time()}] {message}")
    
    def log(self, message):
        """添加日志"""
        self.log_display.append(message)
    
    def get_time(self):
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def on_load_started(self):
        """浏览器开始加载"""
        self.update_status("页面开始加载...")
    
    def on_load_finished(self, success):
        """页面加载完成"""
        if success:
            self.update_status("页面加载完成！正在检测功能...")
            QTimer.singleShot(2000, self.detect_page_features)
        else:
            self.update_status("页面加载失败！")
    
    def navigate_to_url(self):
        """导航到指定URL"""
        url_text = self.url_bar.toPlainText().strip()
        if not url_text:
            self.update_status("请输入有效的URL")
            return
            
        if not url_text.startswith(('http://', 'https://')):
            url_text = 'https://' + url_text
            
        self.update_status(f"正在导航到: {url_text}")
        self.browser.setUrl(QUrl(url_text))
    
    def on_url_changed(self):
        """URL变化"""
        pass
    
    def test_url_navigation(self):
        """测试URL导航功能"""
        self.update_status("开始测试URL导航功能...")
        test_urls = [
            "https://chat.deepseek.com",
            "https://www.deepseek.com",
            "https://www.deepseek.com/zh",
            "https://www.google.com"
        ]
        
        for i, url in enumerate(test_urls):
            self.update_status(f"测试 {i+1}/{len(test_urls)}: {url}")
            self.browser.setUrl(QUrl(url))
            QTimer.singleShot(3000, lambda u=url: self.check_navigation_result(u))
    
    def check_navigation_result(self, url):
        """检查导航结果"""
        current_url = self.browser.url().toString()
        if current_url == url:
            self.log(f"✅ URL导航成功: {url}")
        else:
            self.log(f"❌ URL导航失败: 期望 {url}, 实际 {current_url}")
    
    def test_js_injection(self):
        """测试JS注入功能"""
        self.update_status("开始测试JS注入功能...")
        js_script = """
        (function() {
            console.log('JS注入测试成功！');
            return 'JS注入测试完成';
        })();
        """
        
        def on_js_result(result):
            self.log(f"JS注入结果: {result}")
            if result:
                self.update_status("✅ JS注入测试成功")
            else:
                self.update_status("❌ JS注入测试失败")
        
        self.browser.page().runJavaScript(js_script, on_js_result)
    
    def test_element_detection(self):
        """测试元素检测功能"""
        self.update_status("开始测试元素检测功能...")
        detection_script = """
        (function() {
            var elements = {
                textareas: document.querySelectorAll('textarea').length,
                inputs: document.querySelectorAll('input[type="text"]').length,
                buttons: document.querySelectorAll('button').length,
                links: document.querySelectorAll('a').length
            };
            return elements;
        })();
        """
        
        def on_detection_result(result):
            self.log(f"元素检测结果: {result}")
            if result and isinstance(result, dict):
                self.update_status(f"✅ 检测到: {result.get('textareas', 0)}个文本框, {result.get('inputs', 0)}个输入框")
            else:
                self.update_status("❌ 元素检测失败")
        
        self.browser.page().runJavaScript(detection_script, on_detection_result)
    
    def detect_page_features(self):
        """检测页面功能"""
        self.update_status("正在检测页面功能...")
        self.test_js_injection()
        self.test_element_detection()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = DiagnosticBrowser()
    window.show()
    sys.exit(app.exec())

def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = DiagnosticBrowser()
    window.show()
    sys