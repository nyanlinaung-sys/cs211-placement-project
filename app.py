import os
import pandas as pd
import requests
import json
import mysql.connector
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
# Import from logic.py
from logic import load_questions, calculate_results, get_multi_label_prediction, CHAPTER_INSIGHTS

app = FastAPI()

# ROBUST PATHING
base_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# --- SETTINGS FOR AWS DEPLOYMENT ---
CSV_PATH = '/tmp/student_training_data.csv'   # Strictly for ML Training (logic.py needs this)

# SECURITY KEYS
PROFESSOR_KEYS = {
    "Taesik Kim": "pass123",
}

FEATURE_COLS = [
    "Basic: loop/ for-each", "Basic: Method/parameter passing", 
    "Basic: If-else/Boolean zen", "Arrays/ArrayList",
    "Classes", "Inheritance/interfaces", 
    "Java Collections Framework -HashSet", "Java Collections Framework -HashMap"
]

def get_db_connection():
    """Connects to AWS RDS using environment variables"""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

def send_to_google_sheets(sid, name, score, status, professor, session, quarter, year):
    """Sends student data to Google Forms/Sheets"""
    url = "https://docs.google.com/forms/d/e/1FAIpQLSeJjxjL3WoG6NODAhdFS_RVjdHN3KGsIdag9Y71fxsDytyZAQ/formResponse"
    payload = {
        "entry.2042537524": sid, 
        "entry.1764834092": name,
        "entry.1723464832": str(score), 
        "entry.1434025782": status,
        "entry.1068536601": professor,  
        "entry.2117289351": session,    
        "entry.2104050879": quarter,    
        "entry.360230819": year        
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except Exception as e:
        print(f"Sheets Error: {e}")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/quiz", response_class=HTMLResponse)
async def start_quiz(
    request: Request, 
    sid: str = Form(...), 
    name: str = Form(...),
    professor: str = Form(...),
    session: str = Form(...),
    quarter: str = Form(...),
    year: str = Form(...)
):
    # --- BACKEND VALIDATION ---
    sid = sid.strip()
    if not sid.isdigit() or len(sid) != 9:
        return HTMLResponse("<h1>Invalid Student ID. Must be exactly 9 digits.</h1>", status_code=400)
    
    if len(name.strip()) < 2:
        return HTMLResponse("<h1>Please enter a valid Full Name.</h1>", status_code=400)

    questions = load_questions()
    return templates.TemplateResponse("quiz.html", {
        "request": request, 
        "sid": sid, 
        "name": name, 
        "professor": professor,
        "session": session,
        "quarter": quarter,
        "year": year,
        "questions": questions
    })

@app.post("/submit", response_class=HTMLResponse)
async def handle_submit(
    request: Request, 
    sid: str = Form(...), 
    name: str = Form(...),
    professor: str = Form(...),
    session: str = Form(...),
    quarter: str = Form(...),
    year: str = Form(...)
):
    try:
        # Backend double-check for data integrity
        sid = sid.strip()
        if not sid.isdigit() or len(sid) != 9:
            return HTMLResponse("<h1>Data Integrity Error: Invalid SID format.</h1>", status_code=400)

        form_data = await request.form()
        questions = load_questions()
        
        user_answers = []
        for q in questions:
            ans = form_data.get(f"q_{q['id']}")
            user_answers.append(ans if ans else "")
        
        points, feedback, cat_scores, status = calculate_results(user_answers, questions)
        
        send_to_google_sheets(sid, name, points, status, professor, session, quarter, year)
        
        row_data = {cat: cat_scores.get(cat, {'correct': 0})['correct'] * 2 for cat in FEATURE_COLS}
        recommendations = get_multi_label_prediction(row_data)

        detailed_recs = []
        for area in recommendations:
            detailed_recs.append({
                "topic": area,
                "summary": CHAPTER_INSIGHTS.get(area, "This foundational topic is essential for upcoming CS211 chapters.")
            })

        # --- DATABASE LOGIC (Saves Permanently) ---
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assessment_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    sid VARCHAR(50), name VARCHAR(255), professor VARCHAR(255),
                    session VARCHAR(50), quarter VARCHAR(50), year VARCHAR(50),
                    score INT, status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            sql = "INSERT INTO assessment_results (sid, name, professor, session, quarter, year, score, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (sid, name, professor, session, quarter, year, points, status))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as db_e:
            print(f"Database Error: {db_e}")

        # --- TEMP CSV LOGIC (Feeds the AI in logic.py) ---
        training_dict = {cat: row_data[cat] for cat in FEATURE_COLS}
        for cat in FEATURE_COLS:
            training_dict[f"T_{cat}"] = 1 if training_dict[cat] < 8 else 0
        pd.DataFrame([training_dict]).to_csv(CSV_PATH, mode='a', index=False, header=not os.path.exists(CSV_PATH))

        return templates.TemplateResponse("result.html", {
            "request": request, 
            "points": points, 
            "status": status, 
            "cat_scores": cat_scores,
            "recommendations": detailed_recs,
            "feedback": feedback
        })
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        return HTMLResponse(content=f"<html><body><h1>Error: {e}</h1></body></html>", status_code=500)
    
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_submit(
    professor: str = Form(...), 
    key: str = Form(...)
):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/dashboard?prof_f={professor}&key={key}", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    prof_f: str = None, key: str = None,  # type: ignore
    sess_f: str = None, qtr_f: str = None, yr_f: str = None  # type: ignore
):
    if not prof_f or prof_f not in PROFESSOR_KEYS or PROFESSOR_KEYS[prof_f] != key:
        return HTMLResponse(content="<h1>Access Denied</h1>", status_code=403)

    try:
        conn = get_db_connection()
        df = pd.read_sql("SELECT * FROM assessment_results", conn)
        conn.close()
        
        df = df.rename(columns={'name': 'Student_Name', 'score': 'Total_Score', 'professor': 'Professor', 'session': 'Session', 'quarter': 'Quarter', 'year': 'Year'})
    except Exception:
        return templates.TemplateResponse("admin.html", {
            "request": request, "error": "No database data found yet.", "total_students": 0,
            "averages": {cat: 0 for cat in FEATURE_COLS}, "filters": {"sessions": [], "quarters": [], "years": []},
            "selections": {"prof": prof_f, "key": key, "sess": sess_f, "qtr": qtr_f, "yr": yr_f}
        })

    # Data Cleaning for filters
    for col in ['Professor', 'Session', 'Quarter', 'Year']:
        df[col] = df[col].astype(str).str.strip()

    df = df[df['Professor'] == str(prof_f).strip()]

    filters = {
        "sessions": sorted(df['Session'].unique().tolist()),
        "quarters": sorted(df['Quarter'].unique().tolist()),
        "years": sorted(df['Year'].unique().tolist())
    }

    if sess_f: df = df[df['Session'] == str(sess_f).strip()]
    if qtr_f: df = df[df['Quarter'] == str(qtr_f).strip()]
    if yr_f: df = df[df['Year'] == str(yr_f).strip()]

    averages = {cat: 0 for cat in FEATURE_COLS} 
    recent_students = df[['Student_Name', 'Total_Score']].tail(5).to_dict('records') if not df.empty else []

    return templates.TemplateResponse("admin.html", {
        "request": request, "filters": filters, "averages": averages, "recent": recent_students,
        "selections": {"prof": prof_f, "key": key, "sess": sess_f, "qtr": qtr_f, "yr": yr_f},
        "total_students": len(df)
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)