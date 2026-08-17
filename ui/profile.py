import gradio as gr
from collections import Counter

from utils.auth_db import get_user_quiz_history, change_password


def get_profile_ui(current_user_state: gr.State) -> gr.Tab:
    """
    Create the Profile UI: shows the logged-in username, summary quiz stats, and a change password form.

    Args:
        current_user_state (gr.State): State holding the logged-in username.

    Returns:
        gr.Tab: Gradio tab containing the profile UI.
    """
    with gr.Tab("Profile", render=False) as profile_tab:
        gr.Markdown("<h2 style='text-align: center;'>Your Profile</h2>")

        refresh_btn = gr.Button("Refresh")
        profile_info = gr.Markdown()

        def load_profile(username):
            records = get_user_quiz_history(username)
            total_taken = len(records)

            scored_records = [r["score"] for r in records if r["score"] is not None]
            avg_score = round(sum(scored_records) / len(scored_records), 1) if scored_records else None
            best_score = max(scored_records) if scored_records else None

            avg_text = f"{avg_score}/100" if avg_score is not None else "N/A"
            best_text = f"{best_score}/100" if best_score is not None else "N/A"

            if records:
                topics = [r["topic"] for r in records if r["topic"]]
                favorite_topic = Counter(topics).most_common(1)[0][0] if topics else "N/A"
                last_date = records[0]["date"]
            else:
                favorite_topic = "N/A"
                last_date = "N/A"

            info = f"""
**Username:** {username}

**Total quizzes taken:** {total_taken}

**Average score:** {avg_text}

**Best score:** {best_text}

**Most attempted topic:** {favorite_topic}

**Last quiz taken:** {last_date}
"""
            return info

        refresh_btn.click(fn=load_profile, inputs=[current_user_state], outputs=[profile_info])
        profile_tab.select(fn=load_profile, inputs=[current_user_state], outputs=[profile_info])

        gr.Markdown("### Change Password")

        old_password_input = gr.Textbox(label="Current Password", type="password")
        new_password_input = gr.Textbox(label="New Password", type="password")
        confirm_password_input = gr.Textbox(label="Confirm New Password", type="password")
        change_password_btn = gr.Button("Change Password")
        password_message = gr.Markdown("")

        def do_change_password(username, old_password, new_password, confirm_password):
            if not old_password or not new_password or not confirm_password:
                return "❌ Please fill in all password fields.", "", "", ""
            if new_password != confirm_password:
                return "❌ New password and confirmation do not match.", "", "", ""

            success, msg = change_password(username, old_password, new_password)
            icon = "✅" if success else "❌"
            return f"{icon} {msg}", "", "", ""

        change_password_btn.click(
            fn=do_change_password,
            inputs=[current_user_state, old_password_input, new_password_input, confirm_password_input],
            outputs=[password_message, old_password_input, new_password_input, confirm_password_input],
        )

    return profile_tab