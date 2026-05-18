import os
import json
from config import log
import model_loader

# Загружаем пресеты форматов
PRESETS = {}
try:
    with open("model_info.json", "r", encoding="utf-8") as f:
        PRESETS = json.load(f)
except Exception as e:
    log(f"Failed to load model_info.json: {e}")

def get_preset(model_name):
    return PRESETS.get(model_name, {})

def apply_model_template(messages):
    if model_loader.llm is None:
        return None
    try:
        return model_loader.llm.apply_chat_template(messages)
    except AttributeError:
        template = model_loader.chat_template
        if not template:
            return None
        if "<|im_start|>" in template:
            return chatml_format(messages)
        return None

def chatml_format(messages):
    parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        parts.append(f"<|im_start|>{role}\n{content}<|im_end|>")
    parts.append("<|im_start|>assistant\n")
    return "\n".join(parts)

def mistral_format(messages):
    system = ""
    user = ""
    for msg in messages:
        if msg["role"] == "system":
            system = msg["content"] + "\n"
        elif msg["role"] == "user":
            user = msg["content"]
    return f"[INST] {system}{user} [/INST]"

def gemma_format(messages):
    system = ""
    user = ""
    for msg in messages:
        if msg["role"] == "system":
            system = msg["content"]
        elif msg["role"] == "user":
            user = msg["content"]
    prompt = ""
    if system:
        prompt += f"<start_of_turn>system\n{system}<end_of_turn>\n"
    prompt += f"<start_of_turn>user\n{user}<end_of_turn>\n<start_of_turn>model\n"
    return prompt

def llama2_format(messages):
    system = ""
    user = ""
    for msg in messages:
        if msg["role"] == "system":
            system = msg["content"]
        elif msg["role"] == "user":
            user = msg["content"]
    if system:
        return f"[INST] <<SYS>>\n{system}\n<</SYS>>\n{user} [/INST]"
    else:
        return f"[INST] {user} [/INST]"

FORMATTERS = {
    "chatml": chatml_format,
    "mistral": mistral_format,
    "gemma": gemma_format,
    "llama2": llama2_format,
}

def build_prompt(text, target_lang="en", format_override="auto", system_prompt=""):
    model_name = os.path.basename(model_loader.current_model_path)
    preset = get_preset(model_name)

    messages = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})
    messages.append({"role": "user", "content": f"Translate Japanese to English:\n{text}"})

    # 1. Явное переопределение формата
    if format_override != "auto" and format_override in FORMATTERS:
        return FORMATTERS[format_override](messages)

    # 2. Формат из пресета
    preset_format = preset.get("format")
    if preset_format and preset_format in FORMATTERS:
        return FORMATTERS[preset_format](messages)

    # 3. Использовать chat_template из модели
    prompt = apply_model_template(messages)
    if prompt:
        return prompt

    # 4. Fallback на ChatML
    return chatml_format(messages)