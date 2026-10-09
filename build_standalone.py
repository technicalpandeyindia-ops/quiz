import json
from pathlib import Path

BASE = Path(r"C:\Users\rokihics\.gemini\antigravity\scratch\pyq-quiz-app")
with open(BASE / "templates" / "index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Let's write app.py cleanly
app_code = f'''import os
import re
import json
import uuid
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pypdf
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

# EMBEDDED SINGLE-PAGE APPLICATION FRONTEND (Self-contained, works everywhere)
EMBEDDED_HTML_PAGE = {json.dumps(html)}

app = FastAPI(title="PYQ Quiz Master", description="Instant Quiz Platform from PYQ PDFs with Topic Detection")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

for directory in [UPLOAD_DIR, DATA_DIR, STATIC_DIR, TEMPLATES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

DB_FILE = DATA_DIR / "quizzes.json"

def load_db() -> Dict[str, Any]:
    if DB_FILE.exists():
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {{}}
    return {{}}

def save_db(data: Dict[str, Any]):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_text_from_pdf(pdf_path: Path) -> str:
    full_text = []
    if pdfplumber:
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    text = page.extract_text(layout=True) or page.extract_text() or ""
                    if text.strip():
                        full_text.append(f"--- PAGE {{page_idx + 1}} ---\\n" + text)
            if full_text:
                return "\\n".join(full_text)
        except Exception as e:
            print(f"pdfplumber extraction failed: {{e}}, falling back to pypdf")

    try:
        reader = pypdf.PdfReader(str(pdf_path))
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                full_text.append(f"--- PAGE {{page_idx + 1}} ---\\n" + text)
        return "\\n".join(full_text)
    except Exception as e:
        print(f"pypdf extraction failed: {{e}}")
        return ""

def parse_pyq_document(raw_text: str, filename: str) -> Dict[str, Any]:
    lines = raw_text.splitlines()
    
    global_answer_key: Dict[int, str] = {{}}
    answer_key_patterns = [
        r"(?:(?:Q\\.?|Question\\s*)?(\\d+)[\\.\\s\\:\\-\\)]+\\s*(?:\\(?([A-Da-d1-4])\\)?))",
        r"(\\d+)\\s*[-–=:]\\s*\\(?([A-Da-d1-4])\\)?",
    ]
    
    ans_key_section = re.search(r"(?:ANSWER\\s*KEYS?|ANSWERS|SOLUTIONS?|KEY SHEET)\\s*[\\:\\n](.*)", raw_text, re.IGNORECASE | re.DOTALL)
    if ans_key_section:
        key_text = ans_key_section.group(1)
        for pat in answer_key_patterns:
            matches = re.findall(pat, key_text)
            for q_num, ans_val in matches:
                try:
                    q_int = int(q_num)
                    global_answer_key[q_int] = ans_val.upper()
                except ValueError:
                    continue

    topic_header_re = re.compile(
        r"^(?:(?:PART|SECTION|UNIT|MODULE|CHAPTER|TOPIC|SUBJECT)[\\s\\:\\-\\–]+([A-Z0-9\\.\\s\\-\\–&]+)|"
        r"(PHYSICS|CHEMISTRY|MATHEMATICS|BIOLOGY|GENERAL KNOWLEDGE|REASONING|APTITUDE|ENGLISH|POLITY|HISTORY|GEOGRAPHY|ECONOMICS|COMPUTER SCIENCE|DATA STRUCTURES|ALGORITHMS|ELECTRICAL|MECHANICAL|CIVIL))(?:\\s*[\\:\\-\\–]|\\s*$)",
        re.IGNORECASE
    )

    q_start_re = re.compile(
        r"^(?:Q(?:uestion)?\\.?\\s*(\\d+)[\\.\\:\\-\\)\\s]|(?:(\\d+)[\\.\\)]\\s+)|(?:\\[(\\d+)\\]\\s+))",
        re.IGNORECASE
    )

    inline_ans_re = re.compile(r"(?:Ans(?:wer)?|Correct(?:\\s*Option)?|Key)[\\s\\:\\.\\-\\–=]+\\(?\\s*([A-Da-d1-4])\\s*\\)?", re.IGNORECASE)
    explanation_re = re.compile(r"(?:Explanation|Solution|Hint|Details?)[\\s\\:\\.\\-\\–]+(.*)", re.IGNORECASE | re.DOTALL)

    current_topic = "General / Miscellaneous"
    questions = []
    current_q: Optional[Dict[str, Any]] = None
    q_counter = 0

    def finalize_question(q_obj):
        if not q_obj:
            return
        raw_q_text = q_obj.get("raw_body", "").strip()
        if not raw_q_text:
            return

        ans_match = inline_ans_re.search(raw_q_text)
        detected_ans = ""
        if ans_match:
            raw_val = ans_match.group(1).upper()
            val_map = {{"1": "A", "2": "B", "3": "C", "4": "D"}}
            detected_ans = val_map.get(raw_val, raw_val)
        elif q_obj.get("number") in global_answer_key:
            detected_ans = global_answer_key[q_obj["number"]]

        exp_match = explanation_re.search(raw_q_text)
        explanation = exp_match.group(1).strip() if exp_match else ""

        cleaned_body = inline_ans_re.sub("", raw_q_text)
        cleaned_body = explanation_re.sub("", cleaned_body).strip()

        options = []
        option_matches = list(re.finditer(r"(?:[\\(\\[\\{{]?([A-Da-d1-4])[\\)\\]\\}}][\\.\\s\\:\\-\\–]*|\\b([A-Da-d])[\\.\\:]\\s+)(.*?)(?=(?:[\\(\\[\\{{]?[A-Da-d1-4][\\)\\]\\}}][\\.\\s\\:\\-\\–]*|\\b[A-Da-d][\\.\\:]\\s+)|$)", cleaned_body, re.DOTALL))
        
        q_title = cleaned_body
        if option_matches and len(option_matches) >= 2:
            first_opt_idx = option_matches[0].start()
            q_title = cleaned_body[:first_opt_idx].strip()
            
            letter_map = {{"1": "A", "2": "B", "3": "C", "4": "D"}}
            seen_keys = set()
            for m in option_matches:
                key = (m.group(1) or m.group(2)).upper()
                key = letter_map.get(key, key)
                text = m.group(3).strip()
                text = re.sub(r"\\s+", " ", text)
                if key in ["A", "B", "C", "D"] and key not in seen_keys and text:
                    seen_keys.add(key)
                    options.append({{"key": key, "text": text}})
        
        if len(options) < 2:
            sub_lines = [l.strip() for l in cleaned_body.splitlines() if l.strip()]
            q_title = sub_lines[0] if sub_lines else "Question"
            opt_labels = ["A", "B", "C", "D"]
            candidate_opts = []
            for sl in sub_lines[1:]:
                for lbl in opt_labels:
                    if sl.lower().startswith(f"({{lbl.lower()}})") or sl.lower().startswith(f"{{lbl.lower()}}."):
                        candidate_opts.append({{"key": lbl, "text": re.sub(r"^[(\[]?[A-Da-d][)\]\.\:]\s*", "", sl).strip()}})
                        break
            if len(candidate_opts) >= 2:
                options = candidate_opts

        if len(options) < 2:
            options = [
                {{"key": "A", "text": "Option A (See PDF text)"}},
                {{"key": "B", "text": "Option B (See PDF text)"}},
                {{"key": "C", "text": "Option C (See PDF text)"}},
                {{"key": "D", "text": "Option D (See PDF text)"}}
            ]

        if not detected_ans:
            detected_ans = "A"

        questions.append({{
            "id": f"q_{{len(questions) + 1}}",
            "original_num": q_obj.get("number", len(questions) + 1),
            "topic": q_obj.get("topic", "General"),
            "question": q_title,
            "options": options,
            "correct_answer": detected_ans,
            "explanation": explanation or f"Extracted from original PYQ sheet ({{filename}})"
        }})

    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line or cleaned_line.startswith("--- PAGE"):
            continue

        top_match = topic_header_re.search(cleaned_line)
        if top_match and len(cleaned_line) < 80:
            potential_topic = (top_match.group(1) or top_match.group(2) or "").strip()
            if len(potential_topic) >= 3:
                current_topic = potential_topic.title()
                continue

        q_match = q_start_re.match(cleaned_line)
        if q_match:
            finalize_question(current_q)
            q_num_str = q_match.group(1) or q_match.group(2) or q_match.group(3) or str(q_counter + 1)
            try:
                q_num = int(q_num_str)
            except ValueError:
                q_num = q_counter + 1
            q_counter += 1
            
            start_len = len(q_match.group(0))
            rest_of_line = cleaned_line[start_len:].strip()
            
            current_q = {{
                "number": q_num,
                "topic": current_topic,
                "raw_body": rest_of_line
            }}
        else:
            if current_q:
                current_q["raw_body"] += " " + cleaned_line

    finalize_question(current_q)

    topic_counts = {{}}
    for q in questions:
        t = q["topic"]
        topic_counts[t] = topic_counts.get(t, 0) + 1

    topics_summary = [{{"name": t, "count": c}} for t, c in topic_counts.items()]

    return {{
        "title": Path(filename).stem.replace("_", " ").replace("-", " ").title(),
        "filename": filename,
        "total_questions": len(questions),
        "topics": topics_summary,
        "questions": questions
    }}

# ======================= API ROUTES =======================

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
@app.api_route("/index.html", methods=["GET", "HEAD"], response_class=HTMLResponse)
@app.api_route("/home", methods=["GET", "HEAD"], response_class=HTMLResponse)
@app.api_route("/quiz", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def serve_home():
    for candidate in [TEMPLATES_DIR / "index.html", BASE_DIR / "index.html"]:
        if candidate.exists():
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    return HTMLResponse(content=f.read())
            except Exception:
                pass
    return HTMLResponse(content=EMBEDDED_HTML_PAGE)

@app.get("/health")
@app.get("/healthz")
async def health_check():
    return JSONResponse({{"status": "ok", "app": "PYQ Quiz Master"}})

@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_id = str(uuid.uuid4())[:8]
    safe_filename = f"{{file_id}}_{{file.filename}}"
    saved_pdf_path = UPLOAD_DIR / safe_filename

    with open(saved_pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    raw_text = extract_text_from_pdf(saved_pdf_path)
    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract readable text from PDF. Ensure it contains text and is not an image-only scan.")

    parsed_quiz = parse_pyq_document(raw_text, file.filename)
    if parsed_quiz["total_questions"] == 0:
        raise HTTPException(
            status_code=422,
            detail="No formatted questions detected. Please ensure your PDF has numbered questions (e.g. 1., Q1., Question 1) and options (A, B, C, D)."
        )

    quiz_id = f"quiz_{{file_id}}"
    parsed_quiz["id"] = quiz_id
    parsed_quiz["created_at"] = str(Path(saved_pdf_path).stat().st_ctime)

    db = load_db()
    db[quiz_id] = parsed_quiz
    save_db(db)

    return JSONResponse({{
        "status": "success",
        "quiz_id": quiz_id,
        "title": parsed_quiz["title"],
        "total_questions": parsed_quiz["total_questions"],
        "topics": parsed_quiz["topics"]
    }})

@app.get("/api/quizzes")
async def get_all_quizzes():
    db = load_db()
    summary = []
    for q_id, q_data in db.items():
        summary.append({{
            "id": q_id,
            "title": q_data.get("title", "Untitled Quiz"),
            "filename": q_data.get("filename", ""),
            "total_questions": q_data.get("total_questions", 0),
            "topics": q_data.get("topics", [])
        }})
    return JSONResponse(summary)

@app.get("/api/quiz/{{quiz_id}}")
async def get_quiz(quiz_id: str, topic: Optional[str] = None):
    db = load_db()
    quiz = db.get(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    questions = quiz["questions"]
    if topic and topic.lower() != "all":
        questions = [q for q in questions if q["topic"].lower() == topic.lower()]

    client_questions = []
    for q in questions:
        client_questions.append({{
            "id": q["id"],
            "original_num": q.get("original_num"),
            "topic": q["topic"],
            "question": q["question"],
            "options": q["options"]
        }})

    return JSONResponse({{
        "id": quiz_id,
        "title": quiz["title"],
        "selected_topic": topic or "All Topics",
        "total_questions": len(client_questions),
        "topics": quiz["topics"],
        "questions": client_questions
    }})

@app.post("/api/quiz/{{quiz_id}}/submit")
async def submit_quiz(quiz_id: str, payload: Dict[str, Any]):
    db = load_db()
    quiz = db.get(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    user_answers: Dict[str, str] = payload.get("answers", {{}})
    time_taken: int = payload.get("time_taken_seconds", 0)

    all_questions_map = {{q["id"]: q for q in quiz["questions"]}}

    correct_count = 0
    wrong_count = 0
    unattempted_count = 0
    detailed_review = []
    topic_performance = {{}}

    for q_id, q_data in all_questions_map.items():
        user_choice = user_answers.get(q_id, "").upper().strip()
        correct_ans = q_data.get("correct_answer", "").upper().strip()
        is_correct = (user_choice == correct_ans) and (user_choice != "")
        is_unattempted = (user_choice == "")

        if is_unattempted:
            unattempted_count += 1
            status = "unattempted"
        elif is_correct:
            correct_count += 1
            status = "correct"
        else:
            wrong_count += 1
            status = "wrong"

        t_name = q_data.get("topic", "General")
        if t_name not in topic_performance:
            topic_performance[t_name] = {{"total": 0, "correct": 0, "wrong": 0, "unattempted": 0}}
        topic_performance[t_name]["total"] += 1
        topic_performance[t_name][status] += 1

        detailed_review.append({{
            "id": q_id,
            "original_num": q_data.get("original_num"),
            "topic": t_name,
            "question": q_data["question"],
            "options": q_data["options"],
            "user_choice": user_choice,
            "correct_answer": correct_ans,
            "is_correct": is_correct,
            "status": status,
            "explanation": q_data.get("explanation", "")
        }})

    total_submitted_eval = len(detailed_review)
    percentage = round((correct_count / total_submitted_eval * 100), 2) if total_submitted_eval > 0 else 0

    return JSONResponse({{
        "quiz_id": quiz_id,
        "title": quiz["title"],
        "total_questions": total_submitted_eval,
        "score": correct_count,
        "wrong": wrong_count,
        "unattempted": unattempted_count,
        "percentage": percentage,
        "time_taken_seconds": time_taken,
        "topic_performance": topic_performance,
        "review": detailed_review
    }})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting PYQ Quiz Server on port {{port}}")
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=True)
'''

with open(BASE / "app.py", "w", encoding="utf-8") as f:
    f.write(app_code)

print("Written complete self-contained app.py")
