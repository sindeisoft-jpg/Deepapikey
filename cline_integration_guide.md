# CLINE 集成配置指南

## 🎯 问题诊断
CLINE无法创建代码文件的主要原因：
- "Cannot use checkpoints in Desktop directory" - 权限问题
- API返回内容为空或格式不正确
- 工作目录不匹配

## 🔧 解决方案

### 1. 确保API服务正常运行
```bash
# 激活虚拟环境
source venv/bin/activate

# 启动API服务（默认8765端口）
python main.py

# 或指定端口
DEEPSEEK_API_PORT=8765 python main.py
```

### 2. CLINE配置步骤

#### 方法A: 在项目目录中运行CLINE
1. 将CLINE工作目录设置为 `/Users/xurongyu/Desktop/01_项目文件夹/appleweb`
2. 确保CLINE配置指向正确的API端点：`http://127.0.0.1:8765`

#### 方法B: 配置CLINE API端点
在CLINE设置中添加：
```
API Endpoint: http://127.0.0.1:8765/v1/chat/completions
Model Name: deepseek-chat
```

### 3. 验证API功能
```bash
# 测试API连接
curl http://127.0.0.1:8765/api/tags

# 测试代码生成
curl -X POST http://127.0.0.1:8765/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "deepseek-chat", "messages": [{"role": "user", "content": "写一个Python的hello world程序"}]}'
```

### 4. 权限修复
如果仍有权限问题，确保：
- CLINE在项目目录下运行
- 项目目录有写入权限
- 不要在Desktop根目录创建文件

## 📋 预期结果
- CLINE能够成功接收API响应
- 生成的代码文件保存在项目目录中
- 不再显示"Cannot use checkpoints"错误

## 🚀 快速测试脚本
创建 `test_cline_fix.py` 运行验证：
```python
import requests
url = "http://127.0.0.1:8765/v1/chat/completions"
payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": "写一个Python hello world"}]}
response = requests.post(url, json=payload)
print("Status:", response.status_code)
print("Content length:", len(response.json().get('message', {}).get('content', '')))
```