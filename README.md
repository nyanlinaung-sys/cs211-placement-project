💻 Java Skills Diagnostic Tool
An interactive web application built with Python and Streamlit designed to evaluate a student's understanding of Java programming concepts.

📂 Project Structure
app.py: The main interface and controller. It manages the user's progress using Streamlit's session state.

logic.py: The backend logic for loading question data from JSON and calculating performance metrics.

questions.json: The project database containing questions, multiple-choice options, correct answers, and educational tips.

images/: Contains question images for quizes

🏗 Technical Architecture
This project follows the Separation of Concerns principle to ensure the code is modular and easy to maintain:

Data-Driven Design: All quiz content is stored in questions.json. This allows for content updates without changing the application code.

State Management: The app uses st.session_state to track the current question index and store user answers. This prevents the quiz from resetting during interaction.

Dynamic Feedback: The system provides a "Study Plan" at the end, mapping missed questions to specific categories and tips stored in the data layer.

🛠 Installation & Setup
1. Prerequisites
Python 3.8 or higher must be installed on your machine.

The json library is used for data handling (built-in to Python).

2. Install Dependencies
This project requires the Streamlit library. Install it using pip:

Bash
pip install streamlit

3. Folder Layout
Ensure your files are organized as follows for the paths to function correctly:

Plaintext
/your-project-folder
├── app.py
├── logic.py
├── questions.json
├── README.md
└── images/
    └── arrayQ1.png

🚀 How to Run the App
Open your terminal or command prompt.

Navigate to the project directory.

Execute the following command:

Bash
streamlit run app.py
The app will launch in your default browser (usually at http://localhost:8501).