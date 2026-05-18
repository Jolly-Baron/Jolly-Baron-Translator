import os
import model_loader
from config import N_CTX, log
from prompt_builder import build_prompt
import gradio as gr
from datetime import datetime

TRANSLATIONS_DIR = "Translations"
LOOP_DETECT_REPEAT = 4
LOOP_DETECT_PATTERN_SIZE = 6
LOOP_DETECT_PATTERN_REPEATS = 2
LOOP_DETECT_LENGTH_LIMIT = 500    # max символов до проверки повторов

def ensure_translations_dir():
    os.makedirs(TRANSLATIONS_DIR, exist_ok=True)

def save_translation(text, translation):
    ensure_translations_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(TRANSLATIONS_DIR, f"translation_{timestamp}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write("ORIGINAL:\n")
        f.write(text + "\n\n")
        f.write("TRANSLATION:\n")
        f.write(translation + "\n")
    log(f"Translation saved to {filename}")

def detect_loop(last_tokens, full_response):
    """Проверяет, не зациклилась ли модель."""
    # 1. Одинаковые одиночные токены подряд
    if len(last_tokens) >= LOOP_DETECT_REPEAT:
        recent = last_tokens[-LOOP_DETECT_REPEAT:]
        if len(set(recent)) == 1 and recent[0] != "":
            return True

    # 2. Повторяющийся короткий паттерн
    if len(last_tokens) >= LOOP_DETECT_PATTERN_SIZE * LOOP_DETECT_PATTERN_REPEATS:
        window = last_tokens[-LOOP_DETECT_PATTERN_SIZE * LOOP_DETECT_PATTERN_REPEATS:]
        pattern = "".join(window[:LOOP_DETECT_PATTERN_SIZE])
        full = "".join(window)
        expected = pattern * LOOP_DETECT_PATTERN_REPEATS
        if full == expected and len(pattern) > 0:
            return True

    # 3. Повторяющиеся подстроки в самом ответе (если длина > лимита)
    if len(full_response) > LOOP_DETECT_LENGTH_LIMIT:
        # Проверяем, не повторяется ли последний кусок текста
        last_chunk = full_response[-50:]   # последние 50 символов
        if last_chunk and full_response.count(last_chunk) > 10:   # более 10 повторов
            return True

    return False

def translate_single_chunk(text, temperature, top_p, max_tokens, format_override, system_prompt):
    prompt = build_prompt(text, format_override=format_override, system_prompt=system_prompt)
    stream = model_loader.llm(
        prompt,
        max_tokens=max_tokens,
        stop=["<|im_end|>", "<|im_start|>", "[INST]", "[/INST]", "<end_of_turn>", "<start_of_turn>"],
        echo=False,
        temperature=temperature,
        top_p=top_p,
        stream=True
    )
    full_response = ""
    last_tokens = []
    try:
        for output in stream:
            token = output["choices"][0].get("text", "")
            if token:
                last_tokens.append(token)
                max_window = max(LOOP_DETECT_REPEAT, LOOP_DETECT_PATTERN_SIZE * LOOP_DETECT_PATTERN_REPEATS)
                if len(last_tokens) > max_window:
                    last_tokens.pop(0)
            full_response += token
            # Проверка зацикливания при каждом новом токене
            if detect_loop(last_tokens, full_response):
                log(f"Loop detected at length {len(full_response)}: ...{full_response[-80:]}")
                break
            yield full_response
    except gr.exceptions.Abort:
        log("Translation aborted by user.")
        return
    log(f"Chunk translated, length {len(full_response)}: {full_response.strip()[:100]}...")

def translate_text(text, temperature, top_p, max_tokens, line_by_line, format_override, system_prompt):
    if model_loader.llm is None:
        yield "⚠️ Load a model first."
        return
    if not text.strip():
        yield ""
        return

    final_output = ""

    try:
        if line_by_line:
            lines = text.split('\n')
            total = len(lines)
            log(f"Line-by-line translation ({total} lines)")
            translated_lines = []
            for i, line in enumerate(lines):
                if not line.strip():
                    translated_lines.append("")
                    current_output = "\n".join(translated_lines)
                    yield current_output
                    final_output = current_output
                    continue
                log(f"Translating line {i+1}/{total}: {line[:50]}...")
                try:
                    result = ""
                    for partial in translate_single_chunk(line, temperature, top_p, max_tokens, format_override, system_prompt):
                        result = partial
                        current_output = "\n".join(translated_lines + [result])
                        yield current_output
                    cleaned = result.replace("\n", " ").strip()
                    translated_lines.append(cleaned if result else "")
                except gr.exceptions.Abort:
                    log(f"Aborted at line {i+1}.")
                    return
                except Exception as e:
                    log(f"Error line {i+1}: {e}")
                    translated_lines.append(f"[Error: {e}]")
                current_output = "\n".join(translated_lines)
                yield current_output
                final_output = current_output
            save_translation(text, final_output)
            return

        # Whole text translation
        prompt_overhead = 50
        estimated_input_tokens = len(text) // 2 + prompt_overhead

        if estimated_input_tokens + max_tokens <= N_CTX:
            log("Single chunk translation.")
            result = ""
            for partial in translate_single_chunk(text, temperature, top_p, max_tokens, format_override, system_prompt):
                result = partial
                yield result
            final_output = result
            save_translation(text, final_output)
            return

        paragraphs = text.split('\n')
        chunks = []
        current = ""
        for para in paragraphs:
            test = current + ("\n" if current else "") + para
            est = len(test) // 2 + prompt_overhead
            if est + max_tokens <= N_CTX:
                current = test
            else:
                if current:
                    chunks.append(current)
                current = para
        if current:
            chunks.append(current)

        if not chunks:
            yield "❌ Could not split text."
            return

        log(f"Text split into {len(chunks)} chunks.")
        translated_parts = []
        for i, chunk in enumerate(chunks):
            log(f"Translating chunk {i+1}/{len(chunks)}")
            try:
                res = ""
                for partial in translate_single_chunk(chunk, temperature, top_p, max_tokens, format_override, system_prompt):
                    res = partial
                translated_parts.append(res.strip() if res else "")
            except gr.exceptions.Abort:
                log(f"Aborted at chunk {i+1}.")
                return
            except Exception as e:
                log(f"Error chunk {i+1}: {e}")
                translated_parts.append(f"[Error: {e}]")
            current_output = "\n\n".join(translated_parts)
            yield current_output
            final_output = current_output
        save_translation(text, final_output)
    except gr.exceptions.Abort:
        log("Translation aborted by user.")
        if final_output:
            save_translation(text, final_output)
        return