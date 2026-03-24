CS211 Placement Test Project
Bellevue College - Computer Science Department
This is a production-grade web application designed to assess student readiness for the CS211 course. Originally conceived in Streamlit, the project was migrated to FastAPI to support containerized cloud deployment and provide a more robust, asynchronous architecture for student assessments.

🚀 Features
Registration: Securely collects Student ID and Name via FastAPI forms.

Multi-Step Assessment: Interactive quiz covering Java fundamentals including Loops, OOP, Collections, and Interfaces.

CS211 Roadmap: A custom logic engine that maps student performance directly to upcoming CS211 chapters (Recursion, Stacks, Trees, etc.) based on a curriculum correlation matrix.

AI Study Recommendations: Utilizes a Multi-Output Decision Tree to identify specific mastery gaps and predict future focus areas.

Cloud Synchronization: Automatically logs results to a Google Sheet via Google Forms API integration for instructor review.

Responsive UI: A clean, mobile-friendly interface built with Bootstrap 5 and Jinja2 templating.

🛠️ Technical Stack
Backend: FastAPI (Python 3.x)

Frontend: Jinja2 Templates, HTML5, Bootstrap 5

Machine Learning: Scikit-learn (Decision Tree Classifier), Pandas

Deployment: Containerized on AWS App Runner with Continuous Deployment from GitHub.

🧠 How It Works: The Assessment & AI Logic
The application evaluates student readiness through a dual-layered analysis:

1. The Grading Engine
The system processes 40 questions across 8 core Java categories. It uses Grouped Passing Logic:

Strict Minimums: Students must meet an absolute minimum score in each category to avoid a "Reject" status.

Mastery Thresholds: To "Pass," students must achieve high-mastery scores in a specific number of categories within each logical group (e.g., Basic Syntax, OOP, and Collections).

Dynamic Status: Outputs a status of Pass, Pass with Review, or Reject.

2. Predictive Recommendations
The project implements a Multi-Output Decision Tree Classifier:

Feature Mapping: Student scores are compared against historical performance data.

CS211 Correlation: If a student passes but has sub-perfect scores, the AI identifies which specific upcoming CS211 chapters (like Ch12 Recursion or Ch17 Binary Trees) will be most challenging based on their current gaps.

💻 Local Setup
Clone the repository.

Create a virtual environment:

Bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
Install dependencies:

Bash
pip install -r requirements.txt
Run the application:

Bash
python3 app.py
Access the app: Open http://localhost:8080 in your browser.

📦 Deployment
This app is configured for high-availability deployment on AWS App Runner. It is linked to the main branch for automatic builds and deployments.

Migration Note: This project was transitioned from Streamlit to FastAPI to overcome deployment limitations and to provide a professional, scalable web architecture suitable for departmental use.