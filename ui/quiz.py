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
NUM_CODING_PROBLEMS = 3


def get_quiz_ui(llm: LLMManager, current_user_state: gr.State) -> gr.Tab:
    """
    Create the quiz UI: pick a topic, generate questions (conceptual or coding), answer, timed, graded on finish.

    Args:
        llm (LLMManager): LLM manager instance.
        current_user_state (gr.State): State holding the logged-in username.

    Returns:
        gr.Tab: Gradio tab containing the quiz UI.
    """
    with gr.Tab("Interview", render=False) as quiz_tab:
        gr.Markdown(
            "<h2 style='text-align: center;'>Pick a quiz type, topic, and difficulty, then generate questions and answer before time runs out.</h2>"
        )

        quiz_type_select = gr.Radio(
            choices=["Conceptual Q&A", "Coding Challenges"],
            value="Conceptual Q&A",
            label="Quiz Type",
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
        active_mode_state = gr.State("conceptual")

        # --- Conceptual Q&A area ---
        question_blocks = []
        answer_boxes = []
        with gr.Column(visible=False) as quiz_area:
            for i in range(NUM_QUESTIONS):
                q_md = gr.Markdown(f"**Question {i + 1}:**")
                a_box = gr.Textbox(
                    label="",
                    placeholder="Type your answer here...",
                    lines=3,
                )
                question_blocks.append(q_md)
                answer_boxes.append(a_box)
            finish_btn = gr.Button("Finish Interview", variant="stop")

        # --- Coding Challenges area ---
        problem_blocks = []
        code_boxes = []
        with gr.Column(visible=False) as coding_area:
            for i in range(NUM_CODING_PROBLEMS):
                p_md = gr.Markdown(f"**Problem {i + 1}:**")
                c_box = gr.Code(
                    label=f"Your code for Problem {i + 1}",
                    language="python",
                    lines=12,
                )
                problem_blocks.append(p_md)
                code_boxes.append(c_box)
            finish_coding_btn = gr.Button("Finish Interview", variant="stop")

        feedback_area = gr.Markdown(visible=False)

        def toggle_quiz_type(quiz_type):
            return "coding" if quiz_type == "Coding Challenges" else "conceptual"

        quiz_type_select.change(fn=toggle_quiz_type, inputs=[quiz_type_select], outputs=[active_mode_state])

        # --- Conceptual Q&A generation ---
        def generate_questions(topic, difficulty, time_limit):
            questions = llm.generate_quiz_questions(topic, difficulty)
            while len(questions) < NUM_QUESTIONS:
                questions.append("Question could not be generated. Please skip or type N/A.")
            questions = questions[:NUM_QUESTIONS]

            q_updates = [gr.update(value=f"**Question {i + 1}:** {questions[i]}") for i in range(NUM_QUESTIONS)]
            a_updates = [gr.update(value="") for _ in range(NUM_QUESTIONS)]

            total_seconds = int(time_limit) * 60
            mins, secs = divmod(total_seconds, 60)

            return (
                questions,
                *q_updates,
                *a_updates,
                gr.update(visible=True),
                gr.update(visible=False),
                gr.update(interactive=False),
                total_seconds,
                False,
                gr.update(value=f"⏱ Time remaining: {mins:02d}:{secs:02d}", visible=True),
                gr.update(active=True),
                gr.update(visible=False),
            )

        # --- Coding Challenges generation ---
        def generate_coding(topic, difficulty, time_limit):
            problems = llm.generate_coding_challenges(topic, difficulty)
            while len(problems) < NUM_CODING_PROBLEMS:
                problems.append("Problem could not be generated. Please try again.")
            problems = problems[:NUM_CODING_PROBLEMS]

            p_updates = [gr.update(value=f"**Problem {i + 1}:**\n\n{problems[i]}") for i in range(NUM_CODING_PROBLEMS)]
            c_updates = [gr.update(value="") for _ in range(NUM_CODING_PROBLEMS)]

            total_seconds = int(time_limit) * 60
            mins, secs = divmod(total_seconds, 60)

            return (
                problems,
                *p_updates,
                *c_updates,
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(interactive=False),
                total_seconds,
                False,
                gr.update(value=f"⏱ Time remaining: {mins:02d}:{secs:02d}", visible=True),
                gr.update(active=True),
                gr.update(visible=False),
            )

        def dispatch_generate(quiz_type, topic, difficulty, time_limit):
            if quiz_type == "Coding Challenges":
                problems, *p_updates_c_updates_rest = generate_coding(topic, difficulty, time_limit)
                # Pad conceptual outputs with no-ops since they're not used in this mode
                q_no_ops = [gr.update() for _ in range(NUM_QUESTIONS)]
                a_no_ops = [gr.update() for _ in range(NUM_QUESTIONS)]
                p_no_ops = p_updates_c_updates_rest[:NUM_CODING_PROBLEMS]
                c_no_ops = p_updates_c_updates_rest[NUM_CODING_PROBLEMS : NUM_CODING_PROBLEMS * 2]
                rest = p_updates_c_updates_rest[NUM_CODING_PROBLEMS * 2 :]
                return (problems, *q_no_ops, *a_no_ops, *p_no_ops, *c_no_ops, *rest)
            else:
                questions, *q_updates_a_updates_rest = generate_questions(topic, difficulty, time_limit)
                q_upd = q_updates_a_updates_rest[:NUM_QUESTIONS]
                a_upd = q_updates_a_updates_rest[NUM_QUESTIONS : NUM_QUESTIONS * 2]
                rest = q_updates_a_updates_rest[NUM_QUESTIONS * 2 :]
                p_no_ops = [gr.update() for _ in range(NUM_CODING_PROBLEMS)]
                c_no_ops = [gr.update() for _ in range(NUM_CODING_PROBLEMS)]
                return (questions, *q_upd, *a_upd, *p_no_ops, *c_no_ops, *rest)

        generate_btn.click(
            fn=dispatch_generate,
            inputs=[quiz_type_select, topic_select, difficulty_select, time_limit_select],
            outputs=[
                questions_state,
                *question_blocks,
                *answer_boxes,
                *problem_blocks,
                *code_boxes,
                quiz_area,
                coding_area,
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
            return remaining, f"⏱ Time remaining: {mins:02d}:{secs:02d}", gr.update(active=True), False

        timer.tick(
            fn=tick,
            inputs=[remaining_seconds],
            outputs=[remaining_seconds, timer_display, timer, time_expired],
        )

        def finish_quiz(topic, difficulty, questions, username, *answers):
            answers = list(answers)
            feedback, score = llm.grade_quiz(topic, questions, answers)
            save_quiz_result(username, topic, difficulty, score, feedback, questions, answers)
            score_text = f"## Your Score: {score}/100\n\n" if score is not None else ""
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(value=score_text + feedback, visible=True),
                gr.update(active=False),
                gr.update(visible=False),
                gr.update(interactive=True),
            )

        def finish_coding(topic, difficulty, problems, username, *code_answers):
            code_answers = list(code_answers)
            feedback, score = llm.grade_coding_challenges(topic, problems, code_answers)
            save_quiz_result(username, topic, difficulty, score, feedback, problems, code_answers)
            score_text = f"## Your Score: {score}/100\n\n" if score is not None else ""
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(value=score_text + feedback, visible=True),
                gr.update(active=False),
                gr.update(visible=False),
                gr.update(interactive=True),
            )

        def dispatch_finish(mode, topic, difficulty, questions, username, *all_answers):
            if mode == "coding":
                code_answers = list(all_answers[:NUM_CODING_PROBLEMS])
                return finish_coding(topic, difficulty, questions, username, *code_answers)
            else:
                text_answers = list(all_answers[NUM_CODING_PROBLEMS:])
                return finish_quiz(topic, difficulty, questions, username, *text_answers)

        # Auto-submit when timer hits zero, for whichever mode is active
        time_expired.change(
            fn=dispatch_finish,
            inputs=[active_mode_state, topic_select, difficulty_select, questions_state, current_user_state, *code_boxes, *answer_boxes],
            outputs=[quiz_area, coding_area, feedback_area, timer, timer_display, generate_btn],
        )

        finish_btn.click(
            fn=finish_quiz,
            inputs=[topic_select, difficulty_select, questions_state, current_user_state, *answer_boxes],
            outputs=[quiz_area, coding_area, feedback_area, timer, timer_display, generate_btn],
        )

        finish_coding_btn.click(
            fn=finish_coding,
            inputs=[topic_select, difficulty_select, questions_state, current_user_state, *code_boxes],
            outputs=[quiz_area, coding_area, feedback_area, timer, timer_display, generate_btn],
        )

    return quiz_tab