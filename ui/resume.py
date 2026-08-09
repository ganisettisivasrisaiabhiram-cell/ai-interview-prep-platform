import gradio as gr
from pypdf import PdfReader


def extract_text_from_pdf(file_path):
    """Extract all text from a PDF file."""
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def analyze_resume(llm, file):
    """Send resume text to the AI and get feedback."""
    if file is None:
        return "Please upload a resume PDF first."

    resume_text = extract_text_from_pdf(file.name)

    if not resume_text.strip():
        return "Could not read any text from this PDF. Please try a different file."

    prompt = f"""You are a strict, experienced hiring manager reviewing this resume. Be direct and critical — the goal is to help the candidate improve, not to flatter them.

1. *Key Skills Found*: List the skills you can identify.
2. *Flaws & Weaknesses*: Point out specific problems — e.g. vague descriptions, missing metrics/numbers, weak action verbs, formatting issues, missing sections, unclear objective, spelling/grammar issues, or anything that would make a recruiter reject this resume.
3. *Specific Suggestions*: For each flaw you found, give a concrete fix — not generic advice. Show a "before" and "after" example where possible.
4. *Overall Rating*: Rate this resume out of 10 and briefly justify the score.

Resume text:
{resume_text[:3000]}
"""

    messages = [{"role": "user", "content": prompt}]
    response = llm.get_text(messages)
    full_response = "".join(response)
    return full_response

def get_resume_ui(llm):
    """Create the Resume Analysis tab."""
    tab = gr.Tab("Resume Analysis")
    with tab:

        gr.Markdown("## Upload your resume (PDF) to get AI feedback")
        file_input = gr.File(label="Upload Resume (PDF)", file_types=[".pdf"])
        analyze_button = gr.Button("Analyze Resume")
        output = gr.Textbox(label="AI Feedback", lines=15)

        analyze_button.click(
            fn=lambda file: analyze_resume(llm, file),
            inputs=file_input,
            outputs=output,
        )
        return tab