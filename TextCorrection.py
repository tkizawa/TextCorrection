import tkinter as tk
from tkinter import scrolledtext, ttk
from openai import AzureOpenAI
import pyperclip
import json
import os
import threading
import time

# 設定ファイルの読み込み
def load_settings():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        settings_path = os.path.join(script_dir, 'setting.json')
        with open(settings_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"設定ファイルの読み込み中にエラーが発生しました: {e}")
        return None

# 設定の読み込み
settings = load_settings()
if not settings:
    print("設定ファイルを確認してください。")
    exit(1)

# Azure OpenAI クライアントの設定
try:
    client = AzureOpenAI(
        azure_endpoint=settings['AZURE_OPENAI_ENDPOINT'],
        api_key=settings['AZURE_OPENAI_KEY'],
        api_version="2023-05-15"
    )
except Exception as e:
    print(f"Azure OpenAI クライアントの初期化中にエラーが発生しました: {e}")
    exit(1)

def split_text(text, max_tokens=3000):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        word_length = len(word) + 1  # +1 for space
        if current_length + word_length > max_tokens:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_length = word_length
        else:
            current_chunk.append(word)
            current_length += word_length

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def process_text_chunk(chunk, mode):
    if mode == "校正":
        system_message = "あなたは優秀な文書校正者です。与えられたテキストを校正し、改善してください。"
        user_message = f"以下のテキストを校正してください：\n\n{chunk}"
    elif mode == "要約":
        system_message = "あなたは優秀な文書要約者です。与えられたテキストを簡潔に要約してください。"
        user_message = f"以下のテキストを要約してください：\n\n{chunk}"
    elif mode == "翻訳":
        system_message = "あなたは優秀な翻訳者です。与えられた英語のテキストを日本語に翻訳してください。"
        user_message = f"以下の英語テキストを日本語に翻訳してください：\n\n{chunk}"
    elif mode == "自然な文章":
        system_message = "あなたは文章を自然でわかりやすい表現に書き換えることができる専門家です。以下の文章を自然でわかりやすい文章に改善してください。"
        user_message = f"以下のテキストを自然でわかりやすい文章に書き換えてください：\n\n{chunk}"
    else:
        raise ValueError("Invalid mode")

    response = client.chat.completions.create(
        model=settings['DEPLOYMENT_NAME'],
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        temperature=0.7,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0
    )

    return response.choices[0].message.content.strip()

def process_text(text, mode, progress_callback):
    chunks = split_text(text)
    results = []
    
    for i, chunk in enumerate(chunks):
        result = process_text_chunk(chunk, mode)
        results.append(result)
        progress = int((i + 1) / len(chunks) * 100)
        progress_callback(progress)
        time.sleep(0.1)  # 進捗バーの動きを見せるための短い遅延

    return "\n\n".join(results)

def save_window_geometry(root):
    geometry = root.geometry()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    work_path = os.path.join(script_dir, 'work.json')
    with open(work_path, 'w') as f:
        json.dump({"geometry": geometry}, f)

def load_window_geometry(root):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    work_path = os.path.join(script_dir, 'work.json')
    if os.path.exists(work_path):
        with open(work_path, 'r') as f:
            data = json.load(f)
            root.geometry(data["geometry"])

class TextProcessingApp:
    def __init__(self, master):
        self.master = master
        master.title("テキスト処理アプリケーション")

        # ウィンドウのサイズ変更に対応
        master.columnconfigure(0, weight=1)
        master.rowconfigure(1, weight=1)
        master.rowconfigure(6, weight=1)

        # 入力テキストエリア
        self.input_label = tk.Label(master, text="入力テキスト:")
        self.input_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.input_text = scrolledtext.ScrolledText(master, height=10, width=50)
        self.input_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # 処理モード選択
        self.mode_label = tk.Label(master, text="処理モード:")
        self.mode_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.mode_var = tk.StringVar(value="校正")
        self.mode_dropdown = ttk.Combobox(master, textvariable=self.mode_var, values=["校正", "要約", "翻訳", "自然な文章"])
        self.mode_dropdown.grid(row=2, column=0, padx=5, pady=5)

        # 処理ボタン
        self.process_button = tk.Button(master, text="処理", command=self.process_text)
        self.process_button.grid(row=3, column=0, pady=5)

        # 進捗バー
        self.progress = ttk.Progressbar(master, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(row=4, column=0, pady=5)

        # 結果表示エリア
        self.output_label = tk.Label(master, text="処理結果:")
        self.output_label.grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.output_text = scrolledtext.ScrolledText(master, height=10, width=50)
        self.output_text.grid(row=6, column=0, sticky="nsew", padx=5, pady=5)

        # コピー・クリアボタン
        self.copy_button = tk.Button(master, text="コピー", command=self.copy_to_clipboard)
        self.copy_button.grid(row=7, column=0, pady=5)
        self.clear_button = tk.Button(master, text="クリア", command=self.clear_text)
        self.clear_button.grid(row=8, column=0, pady=5)

    def process_text(self):
        input_text = self.input_text.get("1.0", tk.END).strip()
        mode = self.mode_var.get()
        if input_text:
            self.process_button.config(state=tk.DISABLED)
            self.progress["value"] = 0
            threading.Thread(target=self.process_text_thread, args=(input_text, mode)).start()
        else:
            print("テキストが入力されていません。")

    def process_text_thread(self, input_text, mode):
        try:
            processed_text = process_text(input_text, mode, self.update_progress)
            self.master.after(0, self.update_output, processed_text)
            self.master.after(0, self.update_progress, 100)
        except Exception as e:
            error_message = f"エラーが発生しました: {str(e)}"
            self.master.after(0, self.update_output, error_message)
        finally:
            self.master.after(0, self.enable_process_button)

    def update_progress(self, value):
        self.progress["value"] = value

    def update_output(self, text):
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, text)
        pyperclip.copy(text)
        print(f"{self.mode_var.get()}結果をクリップボードにコピーしました。")

    def enable_process_button(self):
        self.process_button.config(state=tk.NORMAL)

    def clear_text(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.progress["value"] = 0

    def copy_to_clipboard(self):
        text = self.output_text.get("1.0", tk.END).strip()
        pyperclip.copy(text)
        print("出力結果をクリップボードにコピーしました。")

def main():
    root = tk.Tk()
    load_window_geometry(root)
    app = TextProcessingApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (save_window_geometry(root), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    main()