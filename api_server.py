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

    # 默认 system：让网页端 DeepSeek 输出与官方 API 一致，且代码格式可被 Cline/ALINE 等正确解析
    DEFAULT_SYSTEM = (
        "你正在模拟 DeepSeek 官方 API 的助手回复，输出会直接作为 choices[0].message.content，供 Cline 等智能体解析。\n"
        "【必须】\n"
        "- 只输出助手应返回的纯文本内容，一次输出完整，不要分多段试探。\n"
        "- 代码必须使用 markdown 围栏代码块：先写 ```语言（如 python、bash），换行后写代码，最后换行写 ```。禁止单独一行只写「python」或「bash」再直接写代码。\n"
        "- 多文件时格式固定为：**文件名** 或 文件名: 换行后紧跟 ```语言 换行 代码 换行 ```。例如：**server.py**\\n```python\\nimport socket\\n...\\n```\\n**client.py**\\n```python\\n...\\n```。\n"
        "- 使用说明中的命令用 ```bash 代码块；简要说明可放在代码块之前或之后，保持结构清晰。\n"
        "【禁止】\n"
        "- 不要输出 [约束]、[问题]、[系统指令]、[用户输入] 等标签。\n"
        "- 不要以「根据您的要求」「好的，我来」「以下是」「下面是」等开场白开头。\n"
        "- 不要以「希望可以帮到你」「如有疑问欢迎继续问」等结尾语收尾。\n"
        "- 不要输出 JSON 外壳（如 {\"content\": \"...\"}），只输出 content 内的等价内容。\n"
        "- 不要用「服务器端代码 (server.py)」后跟单独一行「python」再写代码；必须用 **server.py** 或 server.py: 后直接接 ```python 代码块。\n"
        "- 禁止输出任何工具调用格式：不要输出 ask_followup_question、access_mcp_resource、tool_calls 等；不要输出「Aline 有一个问题」「Your question here」或类似占位符。只输出最终答案或代码，不要反问或请求澄清。"
    )

    def _normalize_content(raw: str, want_json_only: bool = False) -> str:
        """去掉常见开场白、多余标签、结尾语；合并多余空行；若需要则只保留第一个合法 JSON。"""
        if not raw or not isinstance(raw, str):
            return raw or ""
        s = raw.strip()
        # 去掉可能混入的标签或 UI 文案
        for line in ("[系统指令]", "[用户输入]", "[约束]", "[问题]", "系统指令", "用户输入", "复制", "深度思考", "联网搜索", "互联网搜索", "下载"):
            s = s.replace(line, "").strip()
        # 若整段是 Aline 占位符（ask_followup_question / Your question here），清空以免触发客户端工具调用
        if re.search(r"ask_followup_question|Aline\s*有一个问题|Your\s*question\s*here", s, re.IGNORECASE) and not re.search(r"```[\s\S]*```", s):
            s = ""
        # 去掉仅由这些词组成的行
        lines = s.split("\n")
        lines = [ln for ln in lines if ln.strip() not in ("复制", "深度思考", "联网搜索", "互联网搜索", "下载", "Your question here", "Aline 有一个问题：")]
        s = "\n".join(lines).strip()
        # 去掉以「Aline 有一个问题：」或「Your question here」开头的整段（避免被解析为工具调用）
        for prefix in ("Aline 有一个问题：", "Aline 有一个问题:", "Your question here"):
            if s.strip().startswith(prefix) and len(s.strip()) < 200:
                s = ""
                break
        # 若包含「已思考」段落：去掉该段，只保留示例/代码部分，便于 ALINE 等智能体直接解析并生成文件
        if "已思考" in s:
            out_lines = []
            skip = True
            for ln in s.split("\n"):
                line = ln.strip()
                if skip:
                    if "已思考" in line:
                        continue
                    if "第一次调用" in line or "第二次调用" in line or ("标记" in line and "完成" in line):
                        continue
                    if "代码内容要" in line or "我们使用" in line and "标准库" in line:
                        continue
                    if "示例代码" in line or line in ("代码:", "示例代码:") or (line.startswith("```") or re.match(r"^[\w\.\-]+\.(py|js|ts|json|md|cpp|java)\s*:?\s*$", line)):
                        skip = False
                out_lines.append(ln)
            s = "\n".join(out_lines).strip()
        # 合并多余空行（连续多个换行压成最多两个），并统一修剪每行首尾空白
        s = re.sub(r"\n{3,}", "\n\n", s)
        lines = [ln.strip() for ln in s.split("\n")]
        s = "\n".join(lines).strip()
        # 将网页常见「文件名)\npython\n代码」转为 Cline 可解析的「**文件名**\n```python\n代码\n```」
        s = re.sub(
            r"([^\n]*?)\s*\(([a-zA-Z0-9_]+\.(?:py|js|ts|sh))\)\s*\n\s*python\s*\n",
            r"**\2**\n```python\n",
            s,
            flags=re.IGNORECASE,
        )
        s = re.sub(
            r"([^\n]*?)\s*\(([a-zA-Z0-9_]+\.(?:sh|bash))\)\s*\n\s*bash\s*\n",
            r"**\2**\n```bash\n",
            s,
            flags=re.IGNORECASE,
        )
        s = re.sub(r"(?<=\n)(python|bash)\s*\n(?=(?:import |def |class |#))", r"```\1\n", s, flags=re.IGNORECASE)
        # 为未闭合的 ``` 补闭合：若 ``` 个数为奇，在最后一个 ```语言 代码块后补 \n```
        if s.count("```") % 2 == 1:
            for lang in ("python", "bash"):
                fence = "```" + lang
                idx = s.rfind(fence)
                if idx >= 0:
                    start = idx + len(fence)
                    rest = s[start:]
                    end = rest.find("\n\n**") if "\n\n**" in rest else rest.find("\n\n```")
                    if end >= 0:
                        s = s[: start + end] + "\n```" + s[start + end :]
                    else:
                        s = s + "\n```"
                    break
        # 去掉常见开场白（行首整句），与 DeepSeek 官方 API 的“直接内容”风格一致
        preamble_patterns = [
            r"^根据[您你]的?要求[，,]?\s*",
            r"^根据[您你]的?问题[，,]?\s*",
            r"^好的[，,]?\s*",
            r"^以下是?[：:]\s*",
            r"^下面是?[：:]\s*",
            r"^我来[为给]?你?\s*",
            r"^收到[，,]?\s*",
            r"^明白[了]?[，,]?\s*",
            r"^我的?回答[是：:]?\s*",
            r"^下面是我的?回答[：:]?\s*",
            r"^我理解了[，,]?\s*",
        ]
        for p in preamble_patterns:
            s = re.sub(p, "", s, flags=re.IGNORECASE).strip()
        # 去掉开头多行纯开场白（逐行）
        preamble_lines = (
            "根据您的要求", "根据你的要求", "根据您的问题", "好的，", "以下是", "下面是",
            "我来为你", "收到，", "明白。", "我的回答是", "下面是我的回答", "我理解了",
        )
        while True:
            first_line = (s.split("\n")[0] or "").strip()
            if not first_line:
                break
            dropped = False
            for pl in preamble_lines:
                if first_line.startswith(pl) and len(first_line) < 80:
                    lines = s.split("\n", 1)
                    s = (lines[1] if len(lines) > 1 else "").strip()
                    dropped = True
                    break
            if not dropped:
                break
        # 去掉常见结尾语（整行或段尾），使输出更接近 API 风格
        ending_lines = (
            "希望可以帮到你。", "希望可以帮到你", "如有疑问欢迎继续提问。", "如有疑问欢迎继续问。",
            "如有其他问题欢迎继续提问。", "如果还有问题可以继续问我。", "以上仅供参考。",
        )
        lines = s.split("\n")
        while lines:
            last = (lines[-1] or "").strip()
            if not last:
                lines.pop()
                continue
            if any(last == e or last.startswith(e) for e in ending_lines) and len(last) < 60:
                lines.pop()
                s = "\n".join(lines).strip()
                continue
            break
        s = "\n".join(lines).strip()
        # 若含 <write_to_file><path>...</path><content>...</content>，追加 Markdown 代码块便于 Aline 创建文件
        _ext_to_lang = {"java": "java", "py": "python", "js": "javascript", "ts": "typescript", "sh": "bash"}
        for write_match in re.finditer(
            r"<write_to_file>\s*<path>([^<]+)</path>\s*<content>([\s\S]*?)</content>",
            s,
            re.IGNORECASE,
        ):
            path = write_match.group(1).strip()
            code = write_match.group(2).strip()
            ext = path.split(".")[-1].lower() if "." in path else ""
            lang = _ext_to_lang.get(ext, ext or "text")
            md_block = f"\n\n**{path}**\n```{lang}\n{code}\n```"
            if f"**{path}**" not in s and md_block.strip() not in s:
                s = s + md_block
        # 若要求仅 JSON，尝试提取第一个 JSON 对象
        if want_json_only:
            # 先尝试 ```json ... ``` 或 ``` ... ```
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
        return s.strip()

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
        ok = event.wait(timeout=120)
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
