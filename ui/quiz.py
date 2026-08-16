import gradio as gr
from typing import Any
from api.llm import LLMManager
from utils.auth_db import save_quiz_result

QUIZ_TOPICS = [
    "Data Structures",
    "Algorithms",
    "Databases and SQL",
    "System Design",
    "Operating Systems",
    "Networking",
    "Object-Oriented Programming",
    "Python",
    "Machine Learning Basics",
    "Web Development",
]

NUM_QUESTIONS = 10


def get_quiz_ui(llm: LLMManager, current_user_state: gr.State) -> gr.Tab:
    """
    Create the quiz UI: pick a topic, generate 10 questions, type answers, timed, graded on finish.

    Args:
        llm (LLMManager): LLM manager instance.
        current_user_state (gr.State): State holding the logged-in username.

    Returns:
        gr.Tab: Gradio tab containing the quiz UI.
    """
    with gr.Tab("Interview", render=False) as quiz_tab:
        gr.Markdown(
            "<h2 style='text-align: center;'>Pick a topic and difficulty, generate 10 questions, and type your answers before time runs out.</h2>"
        )

        with gr.Row() as setup_row:
            topic_select = gr.Dropdown(
                choices=QUIZ_TOPICS,
                value=QUIZ_TOPICS[0],
                label="Topic",
                allow_custom_value=True,
            )
            difficulty_select = gr.Dropdown(
                choices=["Easy", "Medium", "Hard"],
                value="Medium",
                label="Difficulty",
            )
            time_limit_select = gr.Dropdown(
                choices=["5", "10", "15", "20"],
                value="10",
                label="Time limit (minutes)",
            )

        generate_btn = gr.Button("Generate Questions", variant="primary")

        timer_display = gr.Markdown("", visible=False)
        timer = gr.Timer(1, active=False)
        remaining_seconds = gr.State(0)
        time_expired = gr.State(False)
        questions_state = gr.State([])

        question_blocks = []
        answer_boxes = []
        with gr.Column(visible=False) as quiz_area:
            for i in range(NUM_QUESTIONS):
                q_md = gr.Markdown(f"*Question {i + 1}:*")
                a_box = gr.Textbox(
                    label="",
                    placeholder="Type your answer here...",
                    lines=3,
                )
                question_blocks.append(q_md)
                answer_boxes.append(a_box)
            finish_btn = gr.Button("Finish Interview", variant="stop")

        feedback_area = gr.Markdown(visible=False)

        def generate_questions(topic, difficulty, time_limit):
            questions = llm.generate_quiz_questions(topic, difficulty)
            while len(questions) < NUM_QUESTIONS:
                questions.append("Question could not be generated. Please skip or type N/A.")
            questions = questions[:NUM_QUESTIONS]

            q_updates = [gr.update(value=f"*Question {i + 1}:* {questions[i]}") for i in range(NUM_QUESTIONS)]
            a_updates = [gr.update(value="") for _ in range(NUM_QUESTIONS)]

            total_seconds = int(time_limit) * 60
            mins, secs = divmod(total_seconds, 60)

            return (
                questions,
                *q_updates,
                *a_updates,
                gr.update(visible=True),
                gr.update(interactive=False),
                total_seconds,
                False,
                gr.update(value=f"⏱️ Time remaining: {mins:02d}:{secs:02d}", visible=True),
                gr.update(active=True),
                gr.update(visible=False),
            )

        generate_btn.click(
            fn=generate_questions,
            inputs=[topic_select, difficulty_select, time_limit_select],
            outputs=[
                questions_state,
                *question_blocks,
                *answer_boxes,
                quiz_area,
                generate_btn,
                remaining_seconds,
                time_expired,
                timer_display,
                timer,
                feedback_area,
            ],
        )

        def tick(remaining):
            remaining -= 1
            if remaining <= 0:
                return 0, "⏰ Time's up! Submitting your answers...", gr.update(active=False), True
            mins, secs = divmod(remaining, 60)
            return remaining, f"⏱️ Time remaining: {mins:02d}:{secs:02d}", gr.update(active=True), False

        def finish_quiz(topic, difficulty, questions, username, *answers):
            answers = list(answers)
            feedback, score = llm.grade_quiz(topic, questions, answers)
            save_quiz_result(username, topic, difficulty, score, feedback, questions, answers)
            score_text = f"## Your Score: {score}/100\n\n" if score is not None else ""
            return (
                gr.update(visible=False),
                gr.update(value=score_text + feedback, visible=True),
                gr.update(active=False),
                gr.update(visible=False),
            )

        def maybe_finish_on_expiry(expired, topic, difficulty, questions, username, *answers):
            if not expired:
                return gr.update(), gr.update(), gr.update(), gr.update()
            return finish_quiz(topic, difficulty, questions, username, *answers)

        timer.tick(
            fn=tick,
            inputs=[remaining_seconds],
            outputs=[remaining_seconds, timer_display, timer, time_expired],
        ).then(
            fn=maybe_finish_on_expiry,
            inputs=[time_expired, topic_select, difficulty_select, questions_state, current_user_state, *answer_boxes],
            outputs=[quiz_area, feedback_area, timer, timer_display],
        )

        finish_btn.click(
            fn=finish_quiz,
            inputs=[topic_select, difficulty_select, questions_state, current_user_state, *answer_boxes],
            outputs=[quiz_area, feedback_area, timer, timer_display],
        )

    return quiz_tab