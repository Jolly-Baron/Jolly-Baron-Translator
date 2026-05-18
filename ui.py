import gradio as gr
from config import N_CTX, load_settings, save_settings
from model_loader import get_model_list, load_model
from translator import translate_text

SOURCE_LANGUAGES = ["Japanese", "Russian", "French", "German", "Spanish"]
TARGET_LANGUAGES = ["English", "Russian", "French", "German", "Spanish"]

BASE_PROMPT_TEMPLATE = (
    "You are a {source}→{target} translator. "
    "Translate each line exactly as given. "
    "Output ONLY the translation. "
    "Do not add any explanations, notes, or alternatives."
)

def get_default_prompt(source_lang: str, target_lang: str) -> str:
    return BASE_PROMPT_TEMPLATE.format(source=source_lang, target=target_lang)

def create_ui():
    settings = load_settings()
    initial_max_tokens = settings.get("max_tokens", 512)
    initial_format = settings.get("prompt_format", "auto")
    initial_source = settings.get("source_lang", "Japanese")
    initial_target = settings.get("target_lang", "English")
    initial_system_prompt = settings.get("system_prompt", get_default_prompt(initial_source, initial_target))

    with gr.Blocks(title="Jolly Baron presents — Local Translator") as demo:
        gr.Markdown(
            "<h1 style='text-align: center; margin-bottom: 0;'>"
            "<span style='color: red;'>Jolly Baron</span>"
            "</h1>"
            "<p style='text-align: center; font-size: 1.5em; margin-top: 0; margin-bottom: 0;"
            " color: red; font-style: italic;'>presents</p>"
        )
        gr.Markdown(
            "<p style='text-align: center; font-size: 1.2em; margin-top: 0;'>"
            "⛩️ Local Translator</p>"
        )
        gr.Markdown(
            f"<p style='text-align: center;'>Context: <b>{N_CTX}</b> tokens. "
            "Flash Attention, 8‑bit KV‑cache. Line‑by‑line mode preserves rows.</p>"
        )

        confirm_state = gr.State(False)

        with gr.Tabs():
            with gr.TabItem("Translate"):
                with gr.Row():
                    model_dropdown = gr.Dropdown(
                        choices=get_model_list(),
                        value=None,
                        label="GGUF model",
                        interactive=True,
                        scale=4
                    )
                    with gr.Column(scale=1):
                        refresh_btn = gr.Button("🔄 Refresh")
                        load_btn = gr.Button("Load model", variant="primary")
                load_status = gr.Markdown(value="*Model not loaded*")

                with gr.Row():
                    source_lang_dropdown = gr.Dropdown(
                        choices=SOURCE_LANGUAGES,
                        value=initial_source,
                        label="Source language"
                    )
                    target_lang_dropdown = gr.Dropdown(
                        choices=TARGET_LANGUAGES,
                        value=initial_target,
                        label="Target language"
                    )

                with gr.Row():
                    input_text = gr.Textbox(
                        label="Source text",
                        placeholder="Enter text...",
                        lines=8, scale=2
                    )
                    output_text = gr.Textbox(
                        label="Translation",
                        lines=8, interactive=False, scale=2
                    )
                with gr.Row():
                    translate_btn = gr.Button("Translate", variant="secondary", size="lg")
                    stop_btn = gr.Button("⏹ Stop", variant="stop", size="lg")
                    new_btn = gr.Button("🆕 New translation")

            with gr.TabItem("Settings"):
                with gr.Row():
                    temperature = gr.Slider(0.0, 2.0, value=0.1, step=0.01, label="Temperature")
                    top_p = gr.Slider(0.0, 1.0, value=0.9, step=0.01, label="Top‑p")
                with gr.Row():
                    max_tokens = gr.Slider(1, 8192, value=initial_max_tokens, step=1, label="Max output tokens")
                line_by_line = gr.Checkbox(label="Line by line (for CSV)", value=True)
                prompt_format = gr.Dropdown(
                    choices=["auto", "chatml", "mistral", "gemma", "llama2"],
                    value=initial_format,
                    label="Prompt format",
                    info="Auto uses model's own template or falls back to ChatML"
                )
                system_prompt = gr.Textbox(
                    label="System prompt",
                    value=initial_system_prompt,
                    lines=4,
                    info="Automatically updated when languages change"
                )

        # --- Functions ---
        def save_max_tokens(val):
            s = load_settings()
            s["max_tokens"] = int(val)
            save_settings(s)

        def save_prompt_format(val):
            s = load_settings()
            s["prompt_format"] = val
            save_settings(s)

        def save_system_prompt(val):
            s = load_settings()
            s["system_prompt"] = val
            save_settings(s)

        def save_langs(source, target):
            s = load_settings()
            s["source_lang"] = source
            s["target_lang"] = target
            save_settings(s)

        def confirm_new_translation(current_input, current_output, confirmed):
            if confirmed:
                return "", "", False
            else:
                return current_input, current_output, False

        def refresh_dropdown():
            return gr.Dropdown(choices=get_model_list(), value=None)

        # --- Events ---
        max_tokens.change(fn=save_max_tokens, inputs=max_tokens, outputs=[])
        prompt_format.change(fn=save_prompt_format, inputs=prompt_format, outputs=[])
        system_prompt.change(fn=save_system_prompt, inputs=system_prompt, outputs=[])

        def on_langs_change(source, target):
            save_langs(source, target)
            new_prompt = get_default_prompt(source, target)
            return new_prompt

        source_lang_dropdown.change(
            fn=on_langs_change,
            inputs=[source_lang_dropdown, target_lang_dropdown],
            outputs=system_prompt
        )
        target_lang_dropdown.change(
            fn=on_langs_change,
            inputs=[source_lang_dropdown, target_lang_dropdown],
            outputs=system_prompt
        )

        refresh_btn.click(fn=refresh_dropdown, inputs=[], outputs=model_dropdown)
        load_btn.click(
            fn=lambda model_name: f"*{load_model(model_name)}*",
            inputs=model_dropdown,
            outputs=load_status
        )

        new_btn.click(
            fn=confirm_new_translation,
            inputs=[input_text, output_text, confirm_state],
            outputs=[input_text, output_text, confirm_state],
            js="(input, output, state) => confirm('Clear all text?')"
        )

        translate_event = translate_btn.click(
            fn=translate_text,
            inputs=[input_text, temperature, top_p, max_tokens, line_by_line, prompt_format, system_prompt],
            outputs=output_text
        )
        input_text.submit(
            fn=translate_text,
            inputs=[input_text, temperature, top_p, max_tokens, line_by_line, prompt_format, system_prompt],
            outputs=output_text
        )

        stop_btn.click(fn=None, inputs=[], outputs=[], cancels=[translate_event])

    return demo