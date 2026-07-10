from flask import Flask, render_template, request, redirect, url_for
import google.generativeai as genai
from dotenv import load_dotenv
import os
import PyPDF2
from database import db, Resume
from sqlalchemy import desc

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///skillbridge.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------
# Dummy Login
# -----------------------------

USER_EMAIL = "admin@skillbridge.com"
USER_PASSWORD = "123456"

# -----------------------------
# Home
# -----------------------------

@app.route("/")
def home():
    return render_template("index.html")

# -----------------------------
# Login
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        if email == USER_EMAIL and password == USER_PASSWORD:
            return redirect(url_for("dashboard"))

        else:
            return render_template(
                "login.html",
                error="Invalid Email or Password"
            )

    return render_template("login.html")

# -----------------------------
# Dashboard
# -----------------------------

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# -----------------------------
# Resume Upload Page
# -----------------------------
@app.route("/roadmap", methods=["GET", "POST"])
def roadmap():

    if request.method == "POST":

        career = request.form.get("career")

        prompt = f"""
You are an expert career mentor.

Create a complete roadmap for becoming a {career}.

Include:

1. Skills

2. Technologies

3. Best Projects

4. Free Courses

5. Certifications

6. Interview Preparation

7. Timeline

8. Salary in India

9. Companies Hiring

10. Final Tips

"""

        response = model.generate_content(prompt)

        return render_template(
            "roadmap_result.html",
            roadmap=response.text
        )

    return render_template("roadmap.html")
@app.route("/resume")
def resume():
    return render_template("resume.html")

# -----------------------------
# Resume Analysis
# -----------------------------
@app.route("/chat", methods=["GET", "POST"])
def chat():

    if request.method == "POST":

        question = request.form.get("question")

        prompt = f"""
You are an expert career mentor.

Answer the following question in detail.

Question:

{question}

Provide practical, beginner-friendly guidance.
"""

        response = model.generate_content(prompt)

        return render_template(
            "chat_result.html",
            answer=response.text
        )

    return render_template("chatbot.html")

@app.route("/interview", methods=["GET", "POST"])
def interview():

    if request.method == "POST":

        role = request.form.get("role")

        prompt = f"""
You are an expert interviewer.

Generate:

1. 10 HR Questions
2. 10 Technical Questions
3. 5 Coding Questions
4. 5 Interview Tips

for a {role}.
"""

        response = model.generate_content(prompt)

        return render_template(
            "interview_result.html",
            questions=response.text
        )

    return render_template("interview.html")

@app.route("/skill-gap", methods=["GET", "POST"])
def skill_gap():

    if request.method == "POST":

        dream_job = request.form.get("dream_job")
        skills = request.form.get("skills")

        prompt = f"""
You are an expert AI Career Coach.

Dream Job:
{dream_job}

Current Skills:
{skills}

Generate:

1. Skill Match (%)
2. Missing Skills
3. Best Projects
4. Best Free Courses
5. Certifications
6. 6-Month Roadmap
7. Interview Tips
8. Salary Range in India
"""

        response = model.generate_content(prompt)

        return render_template(
            "skill_result.html",
            report=response.text
        )

    return render_template("skill_gap.html")

@app.route("/resume", methods=["POST"])
def resume_analysis():

    file = request.files["resume"]

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    file.save(filepath)

    text = ""

    with open(filepath, "rb") as pdf_file:

        reader = PyPDF2.PdfReader(pdf_file)

        for page in reader.pages:
            extracted = page.extract_text()

            if extracted:
                text += extracted

    prompt = f"""
You are an expert Resume Reviewer.

Analyze this resume.

Give output in this format.

Resume Score /100

Strengths

Weaknesses

Missing Skills

Projects to Build

Career Suggestions

Courses Recommended

Interview Preparation Tips

Resume:

{text}
"""

    response = model.generate_content(prompt)

    new_resume = Resume(
        filename=file.filename,
        result=response.text
    )

    db.session.add(new_resume)
    db.session.commit()

    return render_template(
        "result.html",
        result=response.text
    )


# -----------------------------
# Gemini Test
# -----------------------------
@app.route("/history")
def history():

    reports = Resume.query.order_by(desc(Resume.id)).all()

    return render_template(
        "history.html",
        reports=reports
    )
@app.route("/logout")
def logout():
    return redirect(url_for("login"))


@app.route("/test-ai")
def test_ai():

    response = model.generate_content(
        "Give 5 skills required to become an AI Engineer."
    )

    return response.text

# -----------------------------
# Run
# -----------------------------
with app.app_context():
    db.create_all()
if __name__ == "__main__":
    app.run(debug=True)