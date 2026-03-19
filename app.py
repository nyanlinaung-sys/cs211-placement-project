import streamlit as st
import pandas as pd
import os
from logic import load_questions, calculate_results, get_multi_label_prediction

# --- CONFIGURATION ---
DEV_MODE = True  # Set to True to pre-select correct answers and show skip button

st.set_page_config(page_title="CS211 Placement Test", page_icon="🧠", layout="wide")

# 1. Initialize Session State
if 'current_q' not in st.session_state:
    st.session_state.current_q = 0 
    st.session_state.answers = []  
    st.session_state.quiz_complete = False

questions = load_questions()
total_questions = len(questions)

st.title("CS211 Placement Test")
st.subheader(f"Department of Computer Science, Bellevue College")

# 2. Quiz Logic
if not st.session_state.quiz_complete:
    q_index = st.session_state.current_q
    q = questions[q_index]

    st.subheader(f"Question {q_index + 1} of {total_questions}")
    progress_val = q_index / total_questions
    st.write(f"**Overall Progress: {int(progress_val * 100)}%**")
    st.progress(progress_val) 

    st.markdown(f"### {q['question']}")
    
    if q.get("image"):
        try:
            st.image(q["image"], caption="Analyze this code snippet", width=400)
        except Exception:
            st.error("Image file not found.")

    # PRE-SELECTION LOGIC
    default_index = None
    if DEV_MODE:
        try:
            default_index = q["options"].index(q["answer"])
        except ValueError:
            default_index = 0

    user_choice = st.radio(
        "Select your answer:", 
        q["options"], 
        index=default_index, 
        key=f"q_{q_index}"
    )
    
    button_label = "Next Question" if q_index < total_questions - 1 else "Finish Quiz"
    
    if st.button(button_label):
        if user_choice is None:
            st.warning("Please select an answer!")
        else:
            st.session_state.answers.append(user_choice)
            if q_index < total_questions - 1:
                st.session_state.current_q += 1
                st.rerun() 
            else:
                st.session_state.quiz_complete = True
                st.rerun()

# 3. Results Page
else:
    # Unpack 4 values: Points (scaled to 10 max), Feedback, Cat Scores, and Passing Status
    # logic.py now handles the complex group requirements
    points, feedback, cat_scores, status = calculate_results(st.session_state.answers, questions) 

    mapping = {
        'Basic: loop/ for-each': 'loops', 
        'Basic: Method/parameter passing': 'methods', 
        'Basic: If-else/Boolean zen': 'logic', 
        'Arrays/ArrayList': 'data_structs',
        'Classes': 'classes', 
        'Inheritance/interfaces': 'inheritance', 
        'Java Collections Framework -HashSet': 'hashset', 
        'Java Collections Framework -HashMap': 'hashmap'
    }   

    # Prepare data for AI (scaled 0-5 for existing model logic)
    row_data = {mapping[cat]: round((data['correct']/data['total'])*5) for cat, data in cat_scores.items() if cat in mapping}

    with st.spinner("AI is determining all necessary study focus areas..."):
        recommended_plans = get_multi_label_prediction(row_data)

    # Log to CSV
    save_data = row_data.copy()
    for col_name in mapping.values():
        is_target = 1 if (col_name in recommended_plans or (col_name in row_data and row_data[col_name] == 0)) else 0
        save_data[f"T_{col_name}"] = is_target

    df_new_result = pd.DataFrame([save_data])
    csv_file = 'student_training_data.csv'
    
    file_exists = os.path.exists(csv_file)
    if file_exists:
        with open(csv_file, 'a+') as f:
            f.seek(0, os.SEEK_END)
            if f.tell() > 0:
                f.seek(f.tell() - 1)
                if f.read(1) != '\n':
                    f.write('\n')
    df_new_result.to_csv(csv_file, mode='a', index=False, header=not file_exists)
    
    # --- UI DISPLAY ---
    # Points are displayed out of the new 80-point maximum
    st.header(f"Final Score: {points} / 80 Points")
    col1, col2 = st.columns([1, 1.2]) 
    
    with col1:
        st.subheader("Results by Category")
        for cat, data in cat_scores.items():
            # Shows "X / Y Correct"
            st.write(f"**{cat}**: {data['correct']} / {data['total']} Correct")
            perc = (data['correct'] / data['total']) if data['total'] > 0 else 0
            st.progress(perc)

    with col2:
        st.subheader("Enrollment Status")

        # Logic-based check from logic.py now accounts for all 3 groups
        if status == "Reject":
            st.error("### ❌ Status: REJECT")
            st.warning("You do not currently meet the requirements for CS211.")
            st.info("Assessment complete. Your results have been recorded for review.")
        else:
            if status == "Pass":
                st.success("### ✅ Status: PASS")
                st.balloons()
            else: # status == "Advice"
                st.warning("### ⚠️ Status: ADVICE")
                st.write("You are eligible for enrollment, but targeted review is recommended.")
            
            st.write("---")
            st.subheader("AI Optimized Study Plan")
            st.write("Focus on these areas to reach 100% mastery for CS211:")

            pretty_names = {
                'loops': 'Iterative Structures (Loops)',
                'methods': 'Method & Parameter Passing',
                'logic': 'Boolean Logic & Zen',
                'data_structs': 'Arrays & ArrayLists',
                'classes': 'Object-Oriented Classes',
                'inheritance': 'Inheritance & Interfaces',
                'hashset': 'Java Collections: HashSet',
                'hashmap': 'Java Collections: HashMap'
            }

            # Only show focus areas for categories that aren't 100% correct
            areas_shown = 0
            for cat, data in cat_scores.items():
                if data['correct'] < data['total']:
                    plan_id = mapping.get(cat)
                    display_title = pretty_names.get(plan_id, cat) # type: ignore
                    
                    with st.container(border=True):
                        st.markdown(f"**Focus Area: {display_title}**")
                        # Fetch tip from JSON questions
                        tip = next((q_obj['tip'] for q_obj in questions if q_obj['category'] == cat), "Review notes.")
                        st.info(f"💡 {tip}")
                    areas_shown += 1
            
            if areas_shown == 0:
                st.info("🌟 Perfect score! You are fully prepared for CS211.")

    if st.button("Restart Quiz"):
        st.session_state.current_q = 0
        st.session_state.answers = []
        st.session_state.quiz_complete = False
        st.rerun()