import gradio as gr

from utils.ui import get_status_color

INTRO = """
# About This Project

This is an AI-powered Interview Preparation Platform built to help students and job seekers practice technical interview questions on their own, at their own pace.

**What it does:**
- Generates a 10-question technical quiz on a topic and difficulty level of your choice.
- Lets you type your answers within a time limit, just like a real quick-fire interview round.
- Uses AI to grade your answers, giving you a score out of 100 and detailed question-by-question feedback.
- Tracks your performance over time, so you can see your progress across multiple attempts.
- Includes a resume analysis tool that reviews your resume and gives AI-generated feedback and suggestions.

The goal is to give you a simple, self-contained way to practice technical interview topics and track your improvement, without needing another person to interview you.
"""

INTERFACE = """
# How to Use the Interview Tab

### 1. Set up your quiz
Choose a **Topic**, **Difficulty**, and **Time limit** (in minutes), then click **"Generate Questions"**.

### 2. Answer the questions
The AI will generate 10 technical questions on your chosen topic. Type your answer directly in the box below each question. A countdown timer at the top shows how much time you have left for the whole quiz.

### 3. Finish the quiz
Click **"Finish Interview"** at any time to submit your answers early, or let the timer run out — your answers will be submitted automatically when time is up.

### 4. Review your feedback
You'll see an overall score out of 100, along with feedback on each individual question explaining what was correct, partially correct, or incorrect.

### 5. Track your progress
Visit the **Performance** tab to see a chart of your scores over time, along with a full history table of every quiz you've taken.
"""


def get_instructions_ui(llm, tts, stt, default_audio_params):
    with gr.Tab("About", render=False) as instruction_tab:
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown(INTRO)
            with gr.Column(scale=1):
                space = "&nbsp;" * 10

                tts_status = get_status_color(tts)
                gr.Markdown(f"TTS status: {tts_status}{space}{tts.config.tts.name}", elem_id="tts_status")

                stt_status = get_status_color(stt)
                gr.Markdown(f"STT status: {stt_status}{space}{stt.config.stt.name}", elem_id="stt_status")

                llm_status = get_status_color(llm)
                gr.Markdown(f"LLM status: {llm_status}{space}{llm.config.llm.name}", elem_id="llm_status")

        with gr.Row():
            gr.Markdown(INTERFACE)

    return instruction_tab