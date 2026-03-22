import os, json
import gradio as gr
from openai import OpenAI
from mcp_server import get_transcript, calculate, get_weather

TOOLS = {"get_transcript": get_transcript, "calculate": calculate, "get_weather": get_weather}

SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_transcript",
            "description": "Get YouTube video transcript.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "YouTube video URL"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a math expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression e.g. 12 * 8"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name e.g. Tokyo"}
                },
                "required": ["city"],
            },
        },
    },
]

def run(url, query):
    # initialise client here — reads env var at call time, not at startup
    # this prevents a crash if Railway injects vars after the module loads
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return "Error: OPENROUTER_API_KEY not set. Add it in Railway → Variables."

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    messages = [
        {"role": "system", "content": "You are a helpful assistant. When a tool returns a result, always use that result to answer — never say you could not retrieve it. Only call get_transcript if a YouTube URL is provided."},
        {"role": "user",   "content": (f"URL: {url}\n\n" if url.strip() else "") + query},
    ]
    result_cache = {}

    while True:
        msg = client.chat.completions.create(model="openai/gpt-4o-mini", messages=messages, tools=SCHEMAS, tool_choice="auto").choices[0].message
        if not msg.tool_calls:
            return msg.content
        messages.append(msg)
        for tc in msg.tool_calls:
            fn_args   = json.loads(tc.function.arguments)
            cache_key = (tc.function.name, json.dumps(fn_args, sort_keys=True))
            if cache_key not in result_cache:
                result_cache[cache_key] = TOOLS[tc.function.name](**fn_args)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_cache[cache_key]})

with gr.Blocks(title="AI Assistant") as app:
    gr.Markdown("## 🤖 AI Assistant  —  video · math · weather")
    url = gr.Textbox(label="YouTube URL (optional)", placeholder="https://www.youtube.com/watch?v=...")
    qry = gr.Textbox(label="Question", placeholder="Summarise the video  /  128 * 37  /  Weather in Tokyo", lines=2)
    gr.Button("Ask").click(fn=run, inputs=[url, qry], outputs=gr.Textbox(label="Answer", lines=10))

app.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
