import gradio as gr
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils.auth_db import get_user_quiz_history


def build_score_chart(records):
    """Build a matplotlib line chart of score over time from quiz history records."""
    fig, ax = plt.subplots(figsize=(6, 3))

    if not records:
        ax.set_title("No quiz history yet")
        ax.set_ylim(0, 100)
        fig.tight_layout()
        return fig

    records_sorted = sorted(records, key=lambda r: r["date"])
    dates = [r["date"].split(" ")[0] for r in records_sorted]
    scores = [r["score"] if r["score"] is not None else 0 for r in records_sorted]

    ax.plot(range(len(dates)), scores, marker="o", color="#4f6ef7")
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels(dates, rotation=45, ha="right")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 100)
    ax.set_title("Score over time")
    fig.tight_layout()
    return fig


def build_history_table(records):
    """Build a pandas DataFrame of quiz history for display, most recent first."""
    if not records:
        return pd.DataFrame(columns=["Date", "Topic", "Difficulty", "Score"])
    rows = [
        {
            "Date": r["date"],
            "Topic": r["topic"],
            "Difficulty": r["difficulty"],
            "Score": r["score"] if r["score"] is not None else "N/A",
        }
        for r in records
    ]
    return pd.DataFrame(rows)


def get_performance_ui(current_user_state: gr.State) -> gr.Tab:
    """
    Create the performance tracking UI: a table and a chart of the user's quiz history.

    Args:
        current_user_state (gr.State): State holding the logged-in username.

    Returns:
        gr.Tab: Gradio tab containing the performance tracking UI.
    """
    with gr.Tab("Performance", render=False) as performance_tab:
        gr.Markdown("<h2 style='text-align: center;'>Your Quiz Performance</h2>")

        refresh_btn = gr.Button("Refresh")
        score_chart = gr.Plot(label="Score over time")
        history_table = gr.Dataframe(
            headers=["Date", "Topic", "Difficulty", "Score"],
            interactive=False,
            label="Quiz History",
        )

        def load_history(username):
            records = get_user_quiz_history(username)
            return build_score_chart(records), build_history_table(records)

        refresh_btn.click(fn=load_history, inputs=[current_user_state], outputs=[score_chart, history_table])
        performance_tab.select(fn=load_history, inputs=[current_user_state], outputs=[score_chart, history_table])

    return performance_tab