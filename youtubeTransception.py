import gradio as gr
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
)
from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    elif "v=" in url:
        query = urlparse(url)
        return parse_qs(query.query)["v"][0]
    return url.split("/")[-1]

def get_transcript(video_url):
    try:
        video_id = extract_video_id(video_url)
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["en", "tr"]
        )
        return " ".join([entry["text"] for entry in transcript])
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
        return f"Hata: {str(e)}"
    except Exception as e:
        return f"Beklenmeyen hata: {str(e)}"

def generate_content(transcript, word_count, model, target_lang, action, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model)
        prompt = f"{transcript}\n\n{action} this text to {target_lang} in {word_count} words."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Üretim hatası: {str(e)}"

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 📺 YouTube Video Summarizer/Translator")
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### Giriş Ayarları")
            video_url = gr.Textbox(
                label="YouTube Video URL",
                placeholder="https://www.youtube.com/watch?v=...",
            )
            GEMINI_API_KEY = gr.Textbox(
                label="Gemini API Key", 
                type="password",
                info="https://aistudio.google.com/app/apikey"
            )
            action_sel = gr.Radio(
                ["Summarize", "Translate"],
                label="İşlem Türü",
                value="Summarize",
            )
            
            with gr.Group():
                lang_sel = gr.Dropdown(
                    ["English", "Turkish", "German"],
                    label="Hedef Dil",
                    value="English",
                )
                word_count = gr.Slider(
                    minimum=50,
                    maximum=1000,
                    value=200,
                    step=50,
                    label="Kelime Sayısı",
                )
                model_sel = gr.Dropdown(
                 choices=[
                    ("Gemini 2.0 Flash (Hızlı)", "gemini-2.0-flash"),
                    ("Gemini 2.0 Flash Lite (Hafif)", "gemini-2.0-flash-lite"), 
                    ("Gemini 1.5 Flash (Güncel)", "gemini-1.5-flash"),
                    ("Gemini 1.5 Flash 8B (Küçük)", "gemini-1.5-flash-8b"),
                    ("Gemini 1.5 Pro (Gelişmiş)", "gemini-1.5-pro")
                                                    ],
                            value="gemini-2.0-flash",
                            label="Model Seçimi",
                            info="""Modellerin Özellikleri:
                            - Flash: Hızlı yanıt süreleri
                            - Lite: Düşük kaynak kullanımı
                            - Pro: Gelişmiş analiz yetenekleri
                            - 8B: 8 milyar parametreli küçük model"""
                   )
            
            with gr.Row():
                trs_btn = gr.Button("Transkripti Al", variant="primary")
                sum_btn = gr.Button("İşlemi Başlat", variant="secondary")

        with gr.Column(scale=3):
            gr.Markdown("### Çıktılar")
            transkript_text = gr.Textbox(
                label="Transkript",
                lines=10,
                interactive=False,
            )
            sum_text = gr.Textbox(
                label="Sonuç",
                lines=10,
                interactive=False,
            )

    # Olay İşleyicileri
    trs_btn.click(
        fn=get_transcript,
        inputs=video_url,
        outputs=transkript_text,
        api_name="get_transcript",
    )

    sum_btn.click(
        fn=generate_content,
        inputs=[
            transkript_text,
            word_count,
            model_sel,
            lang_sel,
            action_sel,
            GEMINI_API_KEY
        ],
        outputs=sum_text,
        api_name="generate_content"
    )

if __name__ == "__main__":
    demo.launch(server_port=7860, share=False)