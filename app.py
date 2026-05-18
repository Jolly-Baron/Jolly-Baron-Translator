import gradio as gr
from ui import create_ui
import tkinter as tk
from PIL import Image, ImageTk
import threading
import time
import webbrowser
import socket

LOG_FILE = "splash_debug.log"

def make_square(img, size=300, offset_x=0, offset_y=0):
    w, h = img.size
    new_edge = min(w, h)
    cx = w // 2 + offset_x
    cy = h // 2 + offset_y
    left = cx - new_edge // 2
    top = cy - new_edge // 2
    right = left + new_edge
    bottom = top + new_edge
    left = max(0, left)
    top = max(0, top)
    right = min(w, left + new_edge)
    bottom = min(h, top + new_edge)
    img = img.crop((left, top, right, bottom))
    img = img.resize((size, size), Image.LANCZOS)
    return img

def show_splash():
    try:
        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)

        # Параметры рамки
        border_width = 8
        canvas_size = 300 + 2 * border_width   # 316

        x = (root.winfo_screenwidth()  - canvas_size) // 2
        y = (root.winfo_screenheight() - canvas_size) // 2
        root.geometry(f"{canvas_size}x{canvas_size}+{x}+{y}")

        bg = tk.Canvas(root, width=canvas_size, height=canvas_size, bg="#1a1a2e", highlightthickness=0)
        bg.pack()

        # Красная рамка по самому краю холста
        bg.create_rectangle(
            0, 0, canvas_size - 1, canvas_size - 1,
            outline="red", width=border_width
        )

        try:
            img = Image.open("jolly baron.jpg")
            img = make_square(img, 300, offset_x=45, offset_y=0)
            tk_img = ImageTk.PhotoImage(img)
            bg.create_image(canvas_size//2, canvas_size//2, image=tk_img, anchor=tk.CENTER)
            root.img = tk_img
        except Exception as e:
            with open(LOG_FILE, "a") as f:
                f.write(f"Splash image error: {e}\n")

        root.after(3000, root.destroy)
        root.mainloop()
    except Exception as e:
        with open(LOG_FILE, "a") as f:
            f.write(f"Splash error: {e}\n")

def wait_for_server(host="127.0.0.1", port=7860, timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                with open(LOG_FILE, "a") as f:
                    f.write(f"Server ready after {time.time()-start:.1f}s\n")
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.5)
    with open(LOG_FILE, "a") as f:
        f.write("Timeout waiting for server.\n")
    return False

if __name__ == "__main__":
    with open(LOG_FILE, "w") as f:
        f.write("Starting application...\n")

    splash_thread = threading.Thread(target=show_splash, daemon=True)
    splash_thread.start()
    time.sleep(0.5)

    def open_browser_later():
        if wait_for_server():
            webbrowser.open("http://127.0.0.1:7860")
        else:
            webbrowser.open("http://127.0.0.1:7860")

    threading.Thread(target=open_browser_later, daemon=True).start()

    demo = create_ui()
    demo.launch(inbrowser=False, theme=gr.themes.Soft())