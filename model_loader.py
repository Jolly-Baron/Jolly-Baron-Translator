import os
import glob
from llama_cpp import Llama
from config import MODELS_DIR, N_CTX, N_THREADS, N_BATCH, log

llm = None
current_model_path = ""
current_gpu_layers = 0
chat_template = None
model_metadata = {}

def get_model_list():
    if not os.path.isdir(MODELS_DIR):
        os.makedirs(MODELS_DIR, exist_ok=True)
        return []
    files = glob.glob(os.path.join(MODELS_DIR, "*.gguf"))
    return [os.path.basename(f) for f in files]

def unload_model():
    global llm, current_model_path, current_gpu_layers, chat_template, model_metadata
    if llm is not None:
        del llm
        llm = None
        current_model_path = ""
        current_gpu_layers = 0
        chat_template = None
        model_metadata = {}
        log("Model unloaded")

def load_model(model_name):
    global llm, current_model_path, current_gpu_layers, chat_template, model_metadata
    if not model_name:
        return "❌ Model not selected."
    model_path = os.path.join(MODELS_DIR, model_name)
    if not os.path.exists(model_path):
        return f"❌ File not found: {model_path}"
    unload_model()
    gpu_layers = -1
    while True:
        try:
            log(f"Loading model with n_gpu_layers={gpu_layers}...")
            llm = Llama(
                model_path=model_path,
                n_ctx=N_CTX,
                n_gpu_layers=gpu_layers,
                n_batch=N_BATCH,           # <-- увеличенная пачка
                verbose=False,
                n_threads=N_THREADS,
                type_k=8,
                type_v=8,
                flash_attn=True,
            )
            current_model_path = model_path
            current_gpu_layers = gpu_layers if gpu_layers != -1 else "all"
            model_metadata = llm.metadata
            chat_template = model_metadata.get("tokenizer.chat_template", None)
            if chat_template:
                log("Chat template loaded from model metadata.")
            msg = f"✅ Model loaded: {model_name} (GPU layers: {current_gpu_layers})"
            log(msg)
            return msg
        except Exception as e:
            err = str(e)
            log(f"Error: {err}")
            if "out of memory" in err.lower() or "cuda" in err.lower():
                if gpu_layers == -1:
                    gpu_layers = 99
                elif gpu_layers > 0:
                    gpu_layers -= 5
                    if gpu_layers < 0:
                        gpu_layers = 0
                else:
                    return f"❌ Failed to load model even on CPU. Error: {err}"
                continue
            else:
                return f"❌ Loading error: {err}"