import os
import gradio as gr

from api.audio import STTManager, TTSManager
from api.llm import LLMManager
from utils.config import Config
from resources.prompts import prompts
from ui.coding import get_problem_solving_ui
from ui.instructions import get_instructions_ui
from ui.resume import get_resume_ui
from utils.auth_db import init_db, register_user, check_login
from utils.params import default_audio_params
from ui.login import get_login_ui


def initialize_services():
    config = Config()
    llm = LLMManager(config, prompts)
    tts = TTSManager(config)
    stt = STTManager(config)

    default_audio_params["streaming"] = stt.streaming

    if os.getenv("SILENT", False):
        tts.read_last_message = lambda x: None

    return config, llm, tts, stt


def create_interface(llm, tts, stt, audio_params):
    with gr.Blocks(title="AI Interview Preparation Platform", theme=gr.themes.Soft(), css="""
    .gradio-container {
        max-width: 900px !important;
        margin: auto !important;
    }
    button.primary {
        border-radius: 8px !important;
    }
""") as demo:
        login_container, logged_in_state, login_button, username_input, password_input, message, do_login = get_login_ui()

        with gr.Column(visible=False) as main_app:
            audio_output = gr.Audio(label="Play audio", autoplay=True, visible=os.environ.get("DEBUG", False), streaming=tts.streaming)

            get_problem_solving_ui(llm, tts, stt, audio_params, audio_output).render()
            get_instructions_ui(llm, tts, stt, audio_params).render()
            get_resume_ui(llm)

        login_button.click(
            fn=do_login,
            inputs=[username_input, password_input],
            outputs=[login_container, main_app, logged_in_state, message],
        )

    return demo


def main():
    init_db()

    config, llm, tts, stt = initialize_services()
    demo = create_interface(llm, tts, stt, default_audio_params)

    demo.launch(show_api=False, server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    main()