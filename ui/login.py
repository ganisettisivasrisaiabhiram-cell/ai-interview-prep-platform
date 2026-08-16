import gradio as gr
from utils.auth_db import register_user, check_login


def get_login_ui():
    """Create a login/register screen. Returns UI pieces for app.py to wire up."""
    with gr.Column(visible=True) as login_container:
        gr.Markdown("## Welcome — Log In or Register")

        username_input = gr.Textbox(label="Username")
        password_input = gr.Textbox(label="Password", type="password")
        message = gr.Markdown("")

        with gr.Row():
            login_button = gr.Button("Log In", variant="primary")
            register_button = gr.Button("Register")

    logged_in_state = gr.State(False)
    current_user_state = gr.State("")

    def do_login(username, password):
        if check_login(username, password):
            return gr.update(visible=False), gr.update(visible=True), True, "", username
        else:
            return gr.update(visible=True), gr.update(visible=False), False, "❌ Invalid username or password.", ""

    def do_register(username, password):
        success, msg = register_user(username, password)
        icon = "✅" if success else "❌"
        return f"{icon} {msg}"

    register_button.click(
        fn=do_register,
        inputs=[username_input, password_input],
        outputs=[message],
    )

    return login_container, logged_in_state, login_button, username_input, password_input, message, do_login, current_user_state