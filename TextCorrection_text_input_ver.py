from openai import AzureOpenAI
import pyperclip

# Azure OpenAI の設定
AZURE_OPENAI_ENDPOINT = "https://kizawa-openai.openai.azure.com/"
AZURE_OPENAI_KEY = "5a49f67fd79c448984e4771bcaa5fa33"
DEPLOYMENT_NAME = "kizawaai"


client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY,
    api_version="2023-05-15"
)

def correct_text(text):
    response = client.chat.completions.create(
        model=DEPLOYMENT_NAME,
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

def display_result(original_text, corrected_text):
    print("\n" + "="*50)
    print("元のテキスト:")
    print(original_text)
    print("\n" + "-"*50)
    print("校正結果:")
    print(corrected_text)
    print("="*50 + "\n")

def main():
    print("テキスト校正アプリケーションへようこそ！")
    while True:
        print("\nテキストを入力してください（終了する場合は 'q' を入力）：")
        input_text = input()
        
        if input_text.lower() == 'q':
            print("プログラムを終了します。")
            break
        
        print("\n校正中...\n")
        corrected_text = correct_text(input_text)
        
        display_result(input_text, corrected_text)
        
        pyperclip.copy(corrected_text)
        print("校正結果をクリップボードにコピーしました。\n")

if __name__ == "__main__":
    main()
