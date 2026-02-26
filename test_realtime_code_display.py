#!/usr/bin/env python3
"""
实时代码显示测试脚本
测试DeepSeek编写代码时的实时显示效果
"""

import sys
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QPushButton, QLabel
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QFont

class RealTimeCodeDisplayTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setup_simulation()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("实时代码显示测试")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel("DeepSeek实时代码编写显示测试")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 显示区域
        self.display_area = QTextEdit()
        self.display_area.setReadOnly(True)
        self.display_area.setStyleSheet("""
            QTextEdit {
                font-family: Monaco, Consolas, monospace;
                font-size: 12px;
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
        """)
        layout.addWidget(self.display_area)
        
        # 控制按钮
        self.start_button = QPushButton("开始模拟代码编写")
        self.start_button.setStyleSheet("""
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
        """)
        self.start_button.clicked.connect(self.start_simulation)
        layout.addWidget(self.start_button)
        
        # 状态显示
        self.status_label = QLabel("准备就绪 - 点击按钮开始测试")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.status_label)
        
    def setup_simulation(self):
        """设置模拟参数"""
        # 模拟的代码编写过程
        self.code_segments = [
            "# 导入必要的库\nimport numpy as np\nimport matplotlib.pyplot as plt\n\n",
            "# 创建示例数据\ndata = np.random.randn(1000)\n\n",
            "# 绘制直方图\nplt.figure(figsize=(10, 6))\nplt.hist(data, bins=30, alpha=0.7, color='blue')\n\n",
            "# 添加标题和标签\nplt.title('随机数据分布直方图')\nplt.xlabel('数值')\nplt.ylabel('频次')\n\n",
            "# 显示网格\nplt.grid(True, alpha=0.3)\n\n",
            "# 显示图形\nplt.show()"
        ]
        
        self.current_segment = 0
        self.current_position = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        
    def start_simulation(self):
        """开始模拟代码编写"""
        self.display_area.clear()
        self.current_segment = 0
        self.current_position = 0
        self.start_button.setEnabled(False)
        self.status_label.setText("正在实时编写代码...")
        
        # 开始快速更新（50ms间隔）
        self.timer.start(50)
        
    def update_display(self):
        """更新显示内容"""
        if self.current_segment >= len(self.code_segments):
            # 完成
            self.timer.stop()
            self.start_button.setEnabled(True)
            self.status_label.setText("✅ 代码编写完成！共耗时 {:.1f} 秒".format(
                len(self.code_segments) * len(max(self.code_segments, key=len)) * 0.05))
            return
            
        # 获取当前段落
        segment = self.code_segments[self.current_segment]
        
        # 逐字符添加
        if self.current_position < len(segment):
            char = segment[self.current_position]
            self.append_char(char)
            self.current_position += 1
            
            # 更新状态显示
            progress = ((self.current_segment * 100) + (self.current_position / len(segment) * 100)) / len(self.code_segments)
            self.status_label.setText(f"代码编写中... {progress:.1f}%")
        else:
            # 当前段落完成，移动到下一个
            self.current_segment += 1
            self.current_position = 0
            # 在段落间添加小延迟
            if self.current_segment < len(self.code_segments):
                self.timer.setInterval(200)  # 段落间200ms延迟
                QTimer.singleShot(200, lambda: self.timer.setInterval(50))  # 恢复正常速度
                
    def append_char(self, char):
        """添加单个字符到显示区域"""
        cursor = self.display_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        # 设置格式
        format_obj = cursor.charFormat()
        if char in ['#', '\n']:
            format_obj.setForeground(QColor("#6A9955"))  # 注释绿色
        elif char in ['"', "'", '(', ')', '[', ']']:
            format_obj.setForeground(QColor("#CE9178"))  # 字符串橙色
        elif char.isalpha():
            format_obj.setForeground(QColor("#DCDCAA"))  # 变量名黄色
        else:
            format_obj.setForeground(QColor("#D4D4D4"))  # 默认白色
            
        cursor.insertText(char, format_obj)
        
        # 自动滚动到底部
        scrollbar = self.display_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = RealTimeCodeDisplayTest()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    print("=== 实时代码显示测试 ===")
    print("此脚本演示DeepSeek编写代码时的实时显示效果")
    print("特点：")
    print("• 逐字符实时显示代码编写过程")
    print("• 语法高亮显示不同代码元素")
    print("• 模拟真实的打字节奏")
    print("• 实时进度指示")
    main()