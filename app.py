import os
import json
import httpx
import chainlit as cl
from openai import AsyncOpenAI
os.environ["CHAINLIT_TELEMETRY"] = "false"
MCP_BASE = os.getenv("MCP_URL", "http://postgres-hr-mcp:8000/mcp")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("GPT_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ─── MCP SSE Transport ───────────────────────────────────────────────────────

async def mcp_request(method: str, params: dict = None) -> dict:
    sse_url = MCP_BASE
    messages_url = MCP_BASE.rstrip("/") + "/messages"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {},
    }

    result_data = None
    session_id = None
    event_type = ""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("GET", sse_url, headers={"Accept": "text/event-stream"}) as sse:
                async for raw_line in sse.aiter_lines():
                    line = raw_line.strip()
                    if not line:
                        event_type = ""
                        continue
                    print(f"DEBUG: {line}")
                    if line.startswith("event:") and "sessionId=" in line:
                        parts = line.split("sessionId=")
                        if len(parts) > 1:
                            session_id = parts[1].split("&")[0].strip()
                        event_type = line[6:].strip()
                    elif line.startswith("data:"):
                        data_str = line[5:].strip()

                        if event_type == "endpoint":
                            if "sessionId=" in data_str:
                                session_id = data_str.split("sessionId=")[-1].split("&")[0].strip()
                            if session_id:
                                post_resp = await client.post(
                                    messages_url,
                                    json=payload,
                                    params={"sessionId": session_id},
                                    headers={"Content-Type": "application/json"},
                                )
                                post_resp.raise_for_status()

                        elif event_type == "message":
                            try:
                                msg = json.loads(data_str)
                                if "result" in msg or "error" in msg:
                                    result_data = msg
                                    break
                            except json.JSONDecodeError:
                                pass
                        else:
                            try:
                                msg = json.loads(data_str)
                                if "result" in msg or "error" in msg:
                                    result_data = msg
                                    break
                            except Exception:
                                pass

                    if result_data:
                        break
    except httpx.ConnectError:
        raise RuntimeError(f"Không thể kết nối tới MCP tại {sse_url}. Kiểm tra Docker Network!")
    except Exception as e:
        raise RuntimeError(f"Lỗi MCP không xác định: {str(e)}")
                        
    if result_data is None:
        raise RuntimeError("MCP server không trả về response")
    if "error" in result_data:
        raise RuntimeError(result_data["error"].get("message", "MCP error"))
    return result_data.get("result", {})


async def list_mcp_tools() -> list[dict]:
    result = await mcp_request("tools/list")
    return result.get("tools", [])


async def call_mcp_tool(name: str, arguments: dict) -> str:
    result = await mcp_request("tools/call", {"name": name, "arguments": arguments})
    content = result.get("content", [])
    parts = [block["text"] for block in content if block.get("type") == "text"]
    return "\n".join(parts) if parts else json.dumps(result)


# ─── Gemini tool schema ──────────────────────────────────────────────────────

def mcp_tool_to_openai(tool: dict) -> dict:
    input_schema = tool.get("inputSchema") or tool.get("input_schema") or {}
    parameters = {
        "type": "object",
        "properties": input_schema.get("properties", {}) or {},
        "required": input_schema.get("required", []) or [],
        "additionalProperties": input_schema.get("additionalProperties", True),
    }
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool.get("description", "") or "",
            "parameters": parameters,
        },
    }


# ─── Chainlit ────────────────────────────────────────────────────────────────

import asyncio

@cl.on_chat_start
async def on_chat_start():
    try:
        # Giới hạn chờ MCP trong 5 giây, nếu lâu hơn sẽ văng lỗi Timeout
        tools = await asyncio.wait_for(list_mcp_tools(), timeout=5.0)
        cl.user_session.set("mcp_tools", tools)
        
        tool_names = ", ".join(t["name"] for t in tools) if tools else "None"
        await cl.Message(content=f"✅ Kết nối MCP thành công. Tools: `{tool_names}`").send()
    except Exception as e:
        # Nếu lỗi hoặc quá 5s, vẫn cho user chat nhưng không có tools
        await cl.Message(content=f"⚠️ Cảnh báo: Không load được Tools ({e}). Bạn vẫn có thể chat bình thường.").send()
        cl.user_session.set("mcp_tools", [])


@cl.on_message
async def on_message(message: cl.Message):
    mcp_tools: list = cl.user_session.get("mcp_tools", [])
    history: list = cl.user_session.get("history", [])

    if not openai_client:
        await cl.Message(content="❌ Thiếu `OPENAI_API_KEY` (hoặc `GPT_API_KEY`). Vui lòng cấu hình trong `.env`.").send()
        return

    openai_tools = [mcp_tool_to_openai(t) for t in mcp_tools] if mcp_tools else []

    system_instruction = (
        "Bạn là trợ lý HR Analytics thông minh. "
        "Khi user hỏi về dữ liệu nhân sự, sử dụng tools để truy vấn database. "
        "Ưu tiên: metric đã biết (headcount, attrition, new_hire, absent_days, tenure) "
        "→ dùng run_metric_query. Câu hỏi tự do → list_tables → describe_table → run_query. "
        "Trả lời tiếng Việt, rõ ràng. Dữ liệu dạng bảng → dùng markdown table."
    )

    messages = [{"role": "system", "content": system_instruction}]
    for h in history:
        role = "assistant" if h["role"] in ("model", "assistant") else "user"
        messages.append({"role": role, "content": h["content"]})
    messages.append({"role": "user", "content": message.content})

    thinking_msg = cl.Message(content="⏳ Đang xử lý...")
    await thinking_msg.send()

    try:
        final_text = ""
        for _ in range(8):
            resp = await openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=openai_tools if openai_tools else None,
                tool_choice="auto" if openai_tools else None,
            )

            choice = resp.choices[0]
            assistant_msg = choice.message
            tool_calls = getattr(assistant_msg, "tool_calls", None) or []

            if tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_msg.content or "",
                        "tool_calls": [tc.model_dump() for tc in tool_calls],
                    }
                )

                for tc in tool_calls:
                    tool_name = tc.function.name
                    try:
                        tool_args = json.loads(tc.function.arguments or "{}")
                    except json.JSONDecodeError:
                        tool_args = {}

                    thinking_msg.content += f"\n🔧 `{tool_name}`..."
                    await thinking_msg.update()

                    try:
                        tool_result = await call_mcp_tool(tool_name, tool_args)
                    except Exception as e:
                        tool_result = f"Error: {e}"

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": tool_result,
                        }
                    )
                continue

            final_text = assistant_msg.content or ""
            if not final_text:
                final_text = "Xin lỗi, không lấy được kết quả. Vui lòng thử lại."
            break
        else:
            final_text = "Xin lỗi, quá nhiều bước gọi tool. Vui lòng thử lại với câu hỏi ngắn hơn."

        thinking_msg.content = final_text
        await thinking_msg.update()

        history.append({"role": "user", "content": message.content})
        history.append({"role": "assistant", "content": final_text})
        cl.user_session.set("history", history[-20:])

    except Exception as e:
        thinking_msg.content = f"❌ Lỗi: {e}"
        await thinking_msg.update()
