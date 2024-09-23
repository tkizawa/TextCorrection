import tkinter as tk
from tkinter import scrolledtext
from openai import AzureOpenAI
import pyperclip
import json
import os

# 設定ファイルの読み込み
def load_settings():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    settings_path = os.path.join(script_dir, 'setting.json')
    with open(settings_path, 'r') as f:
        return json.load(f)

# 設定の読み込み
settings = load_settings()

# Azure OpenAI クライアントの設定
client = AzureOpenAI(
    azure_endpoint=settings['AZURE_OPENAI_ENDPOINT'],
    api_key=settings['AZURE_OPENAI_KEY'],
    api_version="2023-05-15"
)

def correct_text(text):
    response = client.chat.completions.create(
        model=settings['DEPLOYMENT_NAME'],
        messages=[
            {"role": "system", "content": "あなたは優秀な文書校正者です。与えられたテキストを校正し、改善してください。"},
            {"role": "user", "content": f"以下のテキストを校正してください：\n\n{text}"}
        ],
        temperature=0.7,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].message.content.strip()

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

class TextCorrectionApp:
    def __init__(self, master):
        self.master = master
        master.title("テキスト校正アプリケーション")

        # ウィンドウのサイズ変更に対応
        master.columnconfigure(0, weight=1)
        master.rowconfigure(1, weight=1)
        master.rowconfigure(4, weight=1)

        # 入力テキストエリア
        self.input_label = tk.Label(master, text="入力テキスト:")
        self.input_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.input_text = scrolledtext.ScrolledText(master, height=10, width=50)
        self.input_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # 校正ボタン
        self.correct_button = tk.Button(master, text="校正", command=self.correct_text)
        self.correct_button.grid(row=2, column=0, pady=5)

        # 結果表示エリア
        self.output_label = tk.Label(master, text="校正結果:")
        self.output_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.output_text = scrolledtext.ScrolledText(master, height=10, width=50)
        self.output_text.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)

        # クリアボタン
        self.clear_button = tk.Button(master, text="クリア", command=self.clear_text)
        self.clear_button.grid(row=5, column=0, pady=5)

    def correct_text(self):
        input_text = self.input_text.get("1.0", tk.END).strip()
        if input_text:
            corrected_text = correct_text(input_text)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, corrected_text)
            pyperclip.copy(corrected_text)
            print("校正結果をクリップボードにコピーしました。")
        else:
            print("テキストが入力されていません。")

    def clear_text(self):
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)

def main():
    root = tk.Tk()
    load_window_geometry(root)
    app = TextCorrectionApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (save_window_geometry(root), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    main()
