#!/usr/bin/env python3
"""
Ollama 格式的本地 API 服务（无 API Key）
在独立线程中运行 Flask，提供 /api/chat、/api/tags，与 Ollama 接口一致；
通过 request_queue 将请求交给 Qt 主线程在 DeepSeek 网页中执行，通过 response_dict + Event 取回回复。
"""

import json
import re
import threading
import uuid
from queue import Queue
from datetime import datetime, timezone

try:
    from flask import Flask, request, jsonify, Response
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False


def _run_flask(port: int, request_queue: Queue, response_dict: dict, app: "Flask"):
    """在子线程中运行 Flask（开发模式禁用 reload）。"""
    app.run(host="127.0.0.1", port=port, threaded=True, use_reloader=False)


def create_app(request_queue: Queue, response_dict: dict) -> "Flask":
    """创建 Flask 应用，Ollama 接口格式，无 API Key。"""
    app = Flask(__name__)

    @app.after_request
    def cors_headers(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["X-Server"] = "DeepSeek-Qt-Ollama-Local"
        return resp

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "service": "DeepSeek Local API (Ollama + OpenAI 格式)",
            "hint": "无 API Key。支持 system 提示词与 tools 描述，输出贴近 API 便于智能体驱动。",
            "endpoints": [
                "GET /api/tags",
                "POST /api/chat",
                "POST /v1/chat/completions",
            ],
            "agent": "请求体可含 messages、tools/functions、enable_function_call、tool_choice，会告知 DeepSeek 开启 function call 并注入工具列表。",
        })

    @app.route("/api/tags", methods=["GET", "OPTIONS"])
    def list_models():
        """Ollama: 列出模型。"""
        if request.method == "OPTIONS":
            return "", 204
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        return jsonify({
            "models": [
                {
                    "name": "deepseek-chat",
                    "modified_at": now,
                    "size": 0,
                    "digest": "",
                    "details": {"parent_model": "", "format": "", "family": "deepseek"},
                },
                {
                    "name": "deepseek-reasoner",
                    "modified_at": now,
                    "size": 0,
                    "digest": "",
                    "details": {"parent_model": "", "format": "", "family": "deepseek"},
                },
            ],
        })

    # 专门为Cline/Aline智能体优化的系统提示词
    DEFAULT_SYSTEM = (
        "你是一个专业的代码助手，正在与Cline/Aline智能体协作完成编程任务。请严格按照以下格式输出：\n"
        "\n"
        "【文件创建格式 - 重要】\n"
        "当需要创建文件时，必须使用以下精确格式：\n"
        "<create_file>\n"
        "<file_path>文件路径</file_path>\n"
        "<file_content>\n"
        "文件内容\n"
        "</file_content>\n"
        "</create_file>\n"
        "\n"
        "【代码块格式】\n"
        "- Python代码：```python\n代码内容\n```\n"
        "- JavaScript代码：```javascript\n代码内容\n```\n"
        "- 其他语言类似\n"
        "\n"
        "【多文件项目格式】\n"
        "对于多文件项目，请分别列出每个文件：\n"
        "1. 主文件：\n"
        "<create_file>\n"
        "<file_path>main.py</file_path>\n"
        "<file_content>\n"
        "#!/usr/bin/env python3\n"
        "# -*- coding: utf-8 -*-\n"
        "\n"
        "代码内容\n"
        "\n"
        "if __name__ == '__main__':\n"
        "    # 主程序入口\n"
        "    pass\n"
        "</file_content>\n"
        "</create_file>\n"
        "\n"
        "2. 配置文件：\n"
        "<create_file>\n"
        "<file_path>requirements.txt</file_path>\n"
        "<file_content>\n"
        "依赖包列表\n"
        "</file_content>\n"
        "</create_file>\n"
        "\n"
        "【输出要求】\n"
        "- 直接输出最终答案，无需解释过程\n"
        "- 代码必须完整可执行，包含必要导入和错误处理\n"
        "- 使用UTF-8编码和适当的Shebang行\n"
        "- 遵循PEP 8或其他相应语言的最佳实践\n"
        "- 不要输出占位符或伪代码\n"
        "\n"
        "【特别注意】\n"
        "- 严格使用<create_file>标签格式创建文件\n"
        "- 文件路径使用相对路径，如src/main.py\n"
        "- 确保文件内容完整且语法正确\n"
        "- 不要在代码中包含创建文件的指令，只需输出文件内容\n"
        "- 对于简单任务可以直接输出代码块\n"
        "- 对于复杂项目使用多个<create_file>标签\n"
    )

    def _normalize_content(raw: str, want_json_only: bool = False) -> str:
        """优化的内容规范化处理 - 保留更多有用信息，确保与Claude等智能体兼容"""
        if not raw or not isinstance(raw, str):
            return raw or ""
        
        s = raw.strip()
        
        # 保留Cline/Aline的关键格式标签
        if "<create_file>" in s or "<file_path>" in s or "<file_content>" in s:
            # 这是文件创建格式，要特别小心处理
            return s  # 直接返回，不做过多清理
        
        # 移除系统指令和UI标签
        ui_tags = ["[系统指令]", "[用户输入]", "[约束]", "[问题]", "系统指令", "用户输入"]
        for tag in ui_tags:
            s = s.replace(tag, "").strip()
        
        # 移除Cline相关的配置信息（仅当不是代码块时）
        if "You are Cline" in s and "GLOBAL RULES" in s and "```" not in s:
            # 这是Cline的系统配置，应该移除
            lines = s.split("\n")
            filtered_lines = []
            skip_cline_config = False
            
            for line in lines:
                if "You are Cline" in line:
                    skip_cline_config = True
                    continue
                elif skip_cline_config and (line.startswith("##") or "MODES" in line or "EXECUTION FLOW" in line):
                    # 跳过Cline配置部分
                    if "<task>" in line:
                        skip_cline_config = False  # 任务开始，停止跳过
                        filtered_lines.append(line)
                    continue
                elif "<task>" in line:
                    skip_cline_config = False
                    filtered_lines.append(line)
                elif not skip_cline_config:
                    filtered_lines.append(line)
            
            s = "\n".join(filtered_lines).strip()
        
        # 保留有价值的分析内容，移除纯占位符
        if re.search(r"^(Aline\s*有一个问题|Your\s*question\s*here)[:\s]*$", s.strip(), re.IGNORECASE):
            s = ""
        
        # 移除明显无意义的单行内容
        meaningless_lines = ["复制", "联网搜索", "互联网搜索", "下载"]
        lines = s.split("\n")
        filtered_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped not in meaningless_lines:
                filtered_lines.append(line)
        s = "\n".join(filtered_lines).strip()
        
        # 优化代码块格式转换
        # 将常见的代码格式转换为标准markdown格式
        s = re.sub(
            r"^([a-zA-Z0-9_\.\-]+\.(?:py|js|ts|java|cpp|go|rs))\s*[)：:]?\s*\n\s*(python|javascript|java|cpp|go|rust)\s*\n",
            r"**\1**\n```\2\n",
            s,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        
        # 补全未闭合的代码块
        code_blocks = re.findall(r"```\w*", s)
        if len(code_blocks) % 2 == 1:
            s = s.rstrip() + "\n```"
        
        # 适度清理开头的冗余表述，但保留有价值的信息
        # 只移除非常明确的模板化开场白
        redundant_openings = [
            r"^好的[，,]?\s*",
            r"^收到[，,]?\s*",
            r"^明白[了]?[，,]?\s*",
        ]
        
        for pattern in redundant_openings:
            s = re.sub(pattern, "", s, flags=re.IGNORECASE).strip()
        
        # 保留有价值的分析性内容
        # 不要过度清理"根据您的要求"这类有价值的上下文信息
        
        # 适度清理结尾，但保留建设性内容
        constructive_endings = [
            "希望可以帮到你。", "希望可以帮到你", 
            "如有疑问欢迎继续提问。", "如有疑问欢迎继续问。"
        ]
        
        lines = s.split("\n")
        if lines and lines[-1].strip() in constructive_endings:
            lines.pop()
            s = "\n".join(lines).strip()
        
        # 标准化空白字符
        s = re.sub(r"\n{3,}", "\n\n", s)
        lines = [line.rstrip() for line in s.split("\n")]
        s = "\n".join(lines).strip()
        
        # JSON提取逻辑保持不变
        if want_json_only:
            for pattern in (r"```(?:json)?\s*([\s\S]*?)\s*```", r"```\s*([\s\S]*?)\s*```"):
                m = re.search(pattern, s)
                if m:
                    try:
                        obj = json.loads(m.group(1).strip())
                        return json.dumps(obj, ensure_ascii=False)
                    except Exception:
                        pass
            start = s.find("{")
            if start >= 0:
                depth = 0
                for i in range(start, len(s)):
                    if s[i] == "{":
                        depth += 1
                    elif s[i] == "}":
                        depth -= 1
                        if depth == 0:
                            try:
                                obj = json.loads(s[start : i + 1])
                                return json.dumps(obj, ensure_ascii=False)
                            except Exception:
                                pass
                            break
        
        return s

    def _run_chat(body):
        """解析 messages（含 system），可选 tools，投递队列，等待回复；返回 (content, model)。"""
        model = body.get("model") or "deepseek-chat"
        messages = body.get("messages") or []
        if not messages:
            return None, None, "messages is required"
        user_content = ""
        system_content = None
        for m in messages:
            role = (m.get("role") or "").strip().lower()
            c = m.get("content")
            if role == "system" and c:
                system_content = c.strip() if isinstance(c, str) else ""
                if isinstance(c, list):
                    for part in c:
                        if isinstance(part, dict) and part.get("type") == "text":
                            system_content = (part.get("text") or "").strip()
                            break
            elif role == "user":
                if isinstance(c, str):
                    user_content = c.strip()
                elif isinstance(c, list):
                    for part in c:
                        if isinstance(part, dict) and part.get("type") == "text":
                            user_content = (part.get("text") or "").strip()
                            break
        if not user_content:
            return None, None, "No user message in messages"
        system_instruction = system_content if system_content else DEFAULT_SYSTEM
        tools = body.get("tools") or body.get("functions")
        tool_choice = body.get("tool_choice")
        enable_function_call = body.get("enable_function_call", False)
        # 仅当客户端明确要求 function call 时才注入工具说明，避免 Aline/Cline 等仅带 tools 列表的请求
        # 被误当成“需要模型输出 tool_calls”，导致智能体去执行占位符 MCP 而非直接展示代码
        use_function_call = enable_function_call or (tool_choice and str(tool_choice).lower() not in ("none", "null", ""))
        if use_function_call:
            system_instruction = (
                "【Function Call 已开启】你已启用工具调用能力。"
                "当需要调用工具时，必须仅输出如下格式的 JSON，不要外加 markdown 或说明："
                ' {"tool_calls":[{"id":"call_1","type":"function","function":{"name":"<工具名>","arguments":"<JSON 字符串>"}}]}。'
                "不需要调用工具时直接回复正常文本。\n\n"
            ) + system_instruction
        if use_function_call and tools and isinstance(tools, list):
            tools_desc = []
            for t in tools[:20]:
                if isinstance(t, dict):
                    name = t.get("function", t).get("name", t.get("name", ""))
                    desc = t.get("function", t).get("description", t.get("description", ""))
                    params = t.get("function", t).get("parameters", t.get("parameters"))
                    if name:
                        tools_desc.append({"name": name, "description": desc or "", "parameters": params})
            if tools_desc:
                try:
                    system_instruction += "\n\n可用工具列表（调用时 function.name 必须从下列 name 中选择）：\n" + json.dumps(tools_desc, ensure_ascii=False, indent=2)
                    system_instruction += '\n\n调用时严格按此 JSON 格式回复，arguments 为 JSON 字符串：{"tool_calls":[{"id":"call_xxx","type":"function","function":{"name":"工具名","arguments":"{\\"key\\":\\"value\\"}"}}]}。'
                except Exception:
                    pass
        rf = body.get("response_format")
        want_json = isinstance(rf, dict) and (rf.get("type") == "json_object" or rf.get("type") == "json_schema")
        if want_json:
            system_instruction += "\n\n请仅输出合法 JSON，不要外加说明或 markdown 代码块包裹。"
        # 每次对话都提醒：与官方 API 一致、只输出答案或代码，不输出工具调用
        payload = (
            "[约束]\n"
            "【本次对话】输出=DeepSeek API 的 choices[0].message.content：只输出纯文本或代码，无标签与开场白、一次输出完整。"
            "禁止输出 ask_followup_question、tool_calls、Your question here 等；直接给出答案或代码。"
            "若有代码：必须用 ```语言\\n代码\\n```，多文件用 **文件名** 或 文件名: 后接代码块。\n\n"
            + system_instruction + "\n\n[问题]\n" + user_content
        )
        request_id = str(uuid.uuid4())
        event = threading.Event()
        request_queue.put((request_id, payload.strip(), event))
        ok = event.wait(timeout=180)  # 增加超时时间从120秒到180秒
        content = response_dict.pop(request_id, "")
        if not ok:
            content = content or "Request timeout (no reply within 120s)."
        content = _normalize_content(content, want_json_only=want_json)
        # 若清理后为空（例如被当作 ask_followup_question 占位符去掉），返回提示避免客户端出现空白或误触发工具
        if not (content or "").strip():
            content = "请直接描述你需要的代码或问题，我将直接给出代码或答案，无需额外确认。"
        return content, model, None

    @app.route("/api/chat", methods=["POST", "OPTIONS"])
    def chat():
        """Ollama: 对话接口，无 API Key。"""
        if request.method == "OPTIONS":
            return "", 204
        try:
            body = request.get_json(force=True, silent=True) or {}
        except Exception:
            return jsonify({"error": "Invalid JSON"}), 400
        content, model, err = _run_chat(body)
        if err:
            return jsonify({"error": err}), 400
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        return jsonify({
            "model": model,
            "created_at": now,
            "message": {"role": "assistant", "content": content},
            "done": True,
            "done_reason": "stop",
            "eval_count": max(0, len(content)),
            "eval_duration": 0,
        })

    @app.route("/v1/chat/completions", methods=["POST", "OPTIONS"])
    def chat_completions_deepseek():
        """DeepSeek/OpenAI 风格：与官方 API 输出格式一致；支持 stream=true 时以单次 SSE 返回，便于 Aline/Cline 对接。"""
        if request.method == "OPTIONS":
            return "", 204
        try:
            body = request.get_json(force=True, silent=True) or {}
        except Exception:
            return jsonify({"error": {"message": "Invalid JSON", "type": "invalid_request_error"}}), 400
        content, model, err = _run_chat(body)
        if err:
            return jsonify({"error": {"message": err, "type": "invalid_request_error"}}), 400
        cid = "chatcmpl-" + str(uuid.uuid4()).replace("-", "")[:24]
        created_ts = int(datetime.now(timezone.utc).timestamp())

        def _approx_tokens(text):
            if not text:
                return 0
            return max(1, (len(text) * 2) // 3)

        prompt_tokens = 0
        for m in body.get("messages") or []:
            c = m.get("content")
            if isinstance(c, str):
                prompt_tokens += _approx_tokens(c)
            elif isinstance(c, list):
                for p in c:
                    if isinstance(p, dict) and p.get("type") == "text":
                        prompt_tokens += _approx_tokens(p.get("text") or "")
                        break
        completion_tokens = _approx_tokens(content)
        total_tokens = prompt_tokens + completion_tokens

        if body.get("stream"):
            # Aline/Cline 可能要求 stream：以单次 SSE 返回完整内容，避免客户端一直等待或超时
            def gen():
                chunk = {
                    "id": cid,
                    "object": "chat.completion.chunk",
                    "created": created_ts,
                    "model": model,
                    "choices": [
                        {"index": 0, "delta": {"role": "assistant", "content": content}, "finish_reason": "stop"}
                    ],
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                    },
                }
                yield "data: " + json.dumps(chunk, ensure_ascii=False) + "\n\n"
                yield "data: [DONE]\n\n"

            return Response(
                gen(),
                mimetype="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        return jsonify({
            "id": cid,
            "object": "chat.completion",
            "created": created_ts,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "prompt_cache_hit_tokens": 0,
                "prompt_cache_miss_tokens": prompt_tokens,
            },
            "system_fingerprint": "local-qt-web-v1",
        })

    return app


def start_api_server(request_queue: Queue, response_dict: dict, port: int = 8765):
    """在后台线程中启动 API 服务。返回线程对象（可设为 daemon）。"""
    import os
    if not HAS_FLASK:
        raise RuntimeError("Flask is required. Install with: pip install flask")
    app = create_app(request_queue, response_dict)
    port = int(os.environ.get("DEEPSEEK_API_PORT", port))
    thread = threading.Thread(
        target=_run_flask,
        args=(port, request_queue, response_dict, app),
        daemon=True,
    )
    thread.start()
    return thread
