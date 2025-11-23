from fastapi import FastAPI, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import requests
import os
import re
import dateparser
from dateparser.search import search_dates
from datetime import datetime
import json

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = "tasks.db"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            title TEXT,
            scheduled TEXT,
            priority INTEGER,
            created TEXT,
            updated TEXT
        )
        """
    )
    conn.close()
init_db()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
HF_MODEL_ID = "microsoft/phi-2"

def format_title(title):
    return title.strip().capitalize() if title else ""

def speech_to_text(audio_bytes):
    response = requests.post(
        "https://api.deepgram.com/v1/listen",
        headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"},
        files={"audio": ("audio.wav", audio_bytes)},
    )
    response.raise_for_status()
    result = response.json()
    return result["results"]["channels"][0]["alternatives"][0]["transcript"]

def extract_index(text: str, total=None):
    text_l = text.lower()
    match = re.search(r"(\d+)(st|nd|rd|th)?\s+task", text_l)
    if match:
        return int(match.group(1))
    word_numbers = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}
    for word, num in word_numbers.items():
        if f"{word} task" in text_l:
            return num
    if "last task" in text_l and total is not None:
        return total
    if "first task" in text_l:
        return 1
    return None

def extract_priority(text: str):
    text = text.lower()
    match = re.search(r"priority\s*([1-3])", text)
    if match:
        return int(match.group(1))
    if "urgent" in text or "high priority" in text or "top" in text or "important" in text:
        return 3
    elif "medium priority" in text:
        return 2
    elif "low priority" in text or "minor" in text:
        return 1
    return None

def clean_title(raw_title):
    title = raw_title or ""
    # Remove leading action verbs
    title = re.sub(r"^(add|create|make|put|work on|task to do|set up|schedule|show|delete|remove|update|push|move|reschedule|change)\s+", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^(the\s+)?task(\s+to\s+do)?(\s+for)?\s*", "", title, flags=re.IGNORECASE)
    title = re.sub(r"^(the|a|an|about)\s+", "", title, flags=re.IGNORECASE)
    # Remove trailing connecting words and whitespace
    title = re.sub(r"\s*(for|at|on|to)\s*$", "", title, flags=re.IGNORECASE)
    # Collapse whitespace and strip punctuation
    title = re.sub(r"\s+", " ", title).strip(".!?, ")
    # Remove trailing priority phrases from title
    title = re.sub(r"\s*(priority\s*[1-3]|high priority|medium priority|low priority|urgent|important|minor|top)\s*$", "", title, flags=re.IGNORECASE)
    return title.capitalize()

def extract_entities(text):
    title_clean = text
    results = search_dates(text, settings={"PREFER_DATES_FROM": "future"})
    scheduled = None
    title = clean_title(title_clean)
    if results:
        for date_str, date_obj in results:
            if date_obj:
                scheduled = date_obj.isoformat()
                title_clean = re.sub(re.escape(date_str), '', title_clean, flags=re.IGNORECASE).strip()

    # Remove leading action verbs and command phrases
    title_clean = re.sub(
        r"^(add|create|make|put|work on|task to do|set up|schedule|show|delete|remove|update|push|move|reschedule|change)\s+", "", 
        title_clean, flags=re.IGNORECASE
    )
    # Remove phrases like 'the task for', 'task for', 'for', 'about', 'to do'
    title_clean = re.sub(r"^(the\s+)?task(\s+to\s+do)?(\s+for)?\s*", "", title_clean, flags=re.IGNORECASE)
    title_clean = re.sub(r"^(the|a|an|about)\s+", "", title_clean, flags=re.IGNORECASE)
    # Remove trailing 'for', 'about', and extra spaces
    title_clean = re.sub(r"\s+(for|about)\s*$", "", title_clean, flags=re.IGNORECASE)
    title_clean = re.sub(r"\s+", " ", title_clean).strip(".!?, ")

    priority = extract_priority(title_clean)
    index = extract_index(title_clean)
    title = title_clean

    return {
        "title": title,
        "scheduled": scheduled,
        "priority": priority,
        "index": index,
    }

def find_sort(text: str):
    if "priority" in text.lower():
        return "priority"
    if "time" in text.lower() or "date" in text.lower() or "upcoming" in text.lower() or "scheduled" in text.lower():
        return "scheduled"
    return None

def query_llm(text, model_id=HF_MODEL_ID, max_new_tokens=128):
    if not HF_TOKEN:
        return None
    try:
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        prompt = (
            "Extract intent from the following user command as JSON. "
            "Keys: action (create, show, delete, update_scheduled, update_priority), "
            "title (should NOT contain priority or schedule or date/time info), "
            "scheduled (ISO date if exists), priority (int if stated). "
            "For 'title', exclude any reference to priority, schedule, or date/time. "
            "For delete/search/update actions, title should be a clean substring. "
            "If asking for sort, provide field 'sort': 'priority' or 'scheduled'. "
            f"User command: \"{text}\""
        )
        payload = {"inputs": prompt, "parameters": {"max_new_tokens": max_new_tokens}}
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        output = resp.json()
        if isinstance(output, list) and "generated_text" in output[0]:
            return output[0]["generated_text"]
        elif "generated_text" in output:
            return output["generated_text"]
        return str(output)
    except Exception as e:
        print("LLM error:", e)
        return None

def parse_command(text, total_tasks=None, use_llm=True):
    command = None

    # LLM parsing
    if use_llm and HF_TOKEN:
        raw = query_llm(text)
        if raw:
            try:
                if "```" in raw:
                    code_chunks = raw.split("```")
                    json_candidate = ""
                    for chunk in code_chunks:
                        if "{" in chunk:
                            json_candidate = chunk[chunk.find("{"):]
                            break
                    if json_candidate.strip():
                        command = json.loads(json_candidate)
                    else:
                        raise ValueError("No JSON in fenced block")
                else:
                    command = json.loads(raw)
            except Exception as e:
                print("LLM could not parse JSON, falling back. Output was:", raw)

    text_l = text.lower()
    extracted = extract_entities(text)
    print("DEBUG extracted:", extracted)

    # Clean extracted title before use
    extracted['title'] = clean_title(extracted['title'])

    # Fill missing fields from fallback extraction
    if not command or 'action' not in command or command['action'] is None:
        if re.search(r"(show|display)", text_l):
            command = {"action": "show", "title": extracted['title'] if extracted['title'] else None, "sort": find_sort(text_l)}
        elif re.search(r"delete|remove", text_l) and extracted['index'] is not None:
            command = {"action": "delete", "index": extracted['index']}
        elif re.search(r"delete|remove|get rid of", text_l) and extracted['title']:
            command = {"action": "delete", "title": extracted['title']}
        elif re.search(r"(update|set|change|modify|adjust)", text_l) and extracted['title'] and extracted['priority'] is not None:
            command = {"action": "update_priority", "title": extracted['title'], "priority": extracted['priority']}
        elif re.search(r"(make|add|create|work on|task to do|put)", text_l) and extracted['title']:
            command = {"action": "create", "title": extracted['title'], "scheduled": extracted['scheduled'], "priority": extracted['priority']}
        elif re.search(r"(push|schedule|move|update|reschedule|change)", text_l) and extracted['title'] and extracted['scheduled']:
            command = {"action": "update_scheduled", "title": extracted['title'], "scheduled": extracted['scheduled']}
        elif re.search(r"(push|schedule|move|update|reschedule|change)", text_l) and extracted['index'] is not None and extracted['scheduled']:
            command = {"action": "update_scheduled_index", "index": extracted['index'], "scheduled": extracted['scheduled']}
        elif ("priority" in text_l or "prio" in text_l or "index" in text_l) and extracted['index'] is not None and extracted['priority'] is not None:
            command = {"action": "update_priority_index", "index": extracted['index'], "priority": extracted['priority']}
        else:
            command = {"action": None}
    else:
        # LLM worked--merge missing entities from fallback
        if not command.get('title'):
            command['title'] = clean_title(extracted['title'])
        if not command.get('scheduled'):
            command['scheduled'] = extracted['scheduled']
        if command.get('priority') is None:
            command['priority'] = extracted['priority']
        if command.get('index') is None:
            command['index'] = extracted['index']
        if 'sort' not in command:
            command['sort'] = find_sort(text_l)

    print("Parsed command (with extracted entities):", command)
    return command

def handle_task_command(command: dict):
    action = command.get("action")
    title = command.get("title")
    scheduled = command.get("scheduled")
    priority = command.get("priority")
    index = command.get("index")
    sort_by = command.get("sort")
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    now = datetime.now().isoformat(timespec='seconds')
    if action == "delete" and index is not None:
        rows = cursor.execute("SELECT id FROM tasks ORDER BY id").fetchall()
        if 1 <= index <= len(rows):
            task_id = rows[index - 1][0]
            cursor.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            conn.commit()
            affected = cursor.rowcount
            result = {"status": f"Deleted task at index {index}." if affected else f"No task at index {index}."}
        else:
            result = {"status": f"No task at index {index}."}
        conn.close()
        return result
    if action == "create" and title:
        formatted = format_title(title)
        cursor.execute(
            "INSERT INTO tasks (title, scheduled, priority, created, updated) VALUES (?, ?, ?, ?, ?)",
            (formatted, scheduled, priority, now, now),
        )
        conn.commit()
        result = {"status": "Task created.", "title": formatted, "scheduled": scheduled, "priority": priority, "created": now}
    elif action == "show":
        rows = cursor.execute("SELECT * FROM tasks").fetchall()
        STOP_WORDS = {"task", "tasks", "all", "my"}
        if title:
            formatted = format_title(title).lower()
            keywords = [k for k in formatted.split() if k not in STOP_WORDS]
            filtered = [
                task for r in rows for task in [{
                    "id": r[0], "title": r[1], "scheduled": r[2], "priority": r[3], "created": r[4], "updated": r[5]
                }] if all(k in task["title"].lower() for k in keywords)
            ]
        else:
            filtered = [
                {"id": r[0], "title": r[1], "scheduled": r[2], "priority": r[3], "created": r[4], "updated": r[5]}
                for r in rows
            ]
        if sort_by == "priority":
            filtered.sort(key=lambda t: (-(t["priority"] if t["priority"] else 0), t["title"]))
        elif sort_by == "scheduled":
            filtered.sort(key=lambda t: t["scheduled"] if t["scheduled"] else "")
        result = filtered
    elif action == "delete" and title:
        formatted = format_title(title)
        cursor.execute("DELETE FROM tasks WHERE title LIKE ?", (f"%{formatted}%",))
        conn.commit()
        affected = cursor.rowcount
        if affected > 0:
            result = {"status": f"Deleted {affected} task(s) matching '{formatted}'."}
        else:
            result = {"status": f"No tasks matched '{formatted}'."}
    elif action == "update_scheduled" and title and scheduled:
        formatted = format_title(title)
        cursor.execute(
            "UPDATE tasks SET scheduled=?, updated=? WHERE title LIKE ?", (scheduled, now, f"%{formatted}%")
        )
        conn.commit()
        affected = cursor.rowcount
        if affected > 0:
            result = {"status": f"Task(s) matching '{formatted}' scheduled for {scheduled}.", "updated": now}
        else:
            result = {"status": f"No tasks matched '{formatted}' to reschedule."}
    elif action == "update_scheduled_index" and index is not None and scheduled:
        rows = cursor.execute("SELECT id FROM tasks ORDER BY id").fetchall()
        if 1 <= index <= len(rows):
            task_id = rows[index - 1][0]
            cursor.execute("UPDATE tasks SET scheduled=?, updated=? WHERE id=?", (scheduled, now, task_id))
            conn.commit()
            affected = cursor.rowcount
            result = {"status": f"Task at index {index} scheduled for {scheduled}." if affected else f"No task at index {index}."}
        else:
            result = {"status": f"No task at index {index}."}
        conn.close()
        return result
    elif action == "update_priority" and title and priority is not None:
        formatted = format_title(title)
        cursor.execute(
            "UPDATE tasks SET priority=?, updated=? WHERE title LIKE ?", (priority, now, f"%{formatted}%")
        )
        conn.commit()
        affected = cursor.rowcount
        if affected > 0:
            result = {"status": f"Priority of tasks matching '{formatted}' updated to {priority}.", "updated": now}
        else:
            result = {"status": f"No tasks matched '{formatted}' to update priority."}
    elif action == "update_priority_index" and index is not None and priority is not None:
        rows = cursor.execute("SELECT id FROM tasks ORDER BY id").fetchall()
        if 1 <= index <= len(rows):
            task_id = rows[index - 1][0]
            cursor.execute("UPDATE tasks SET priority=?, updated=? WHERE id=?", (priority, now, task_id))
            conn.commit()
            affected = cursor.rowcount
            result = {"status": f"Priority of task at index {index} updated to {priority}." if affected else f"No task at index {index}."}
        else:
            result = {"status": f"No task at index {index}."}
        conn.close()
        return result
    else:
        result = {"status": "Unknown command or missing info."}
    conn.close()
    return result

@app.post("/voice-command")
async def voice_command(audio: UploadFile):
    audio_bytes = await audio.read()
    transcript = speech_to_text(audio_bytes)
    conn = sqlite3.connect(DB)
    total_tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    conn.close()
    command = parse_command(transcript, total_tasks, use_llm=True)
    result = handle_task_command(command)
    return {"transcript": transcript, "result": result}

@app.post("/voice-command/text")
async def voice_command_text(cmd: dict):
    print("[DEBUG] Handler called!")
    command_text = cmd.get("command", "")
    print("[DEBUG] Received:", command_text)
    conn = sqlite3.connect(DB)
    total_tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    conn.close()
    command = parse_command(command_text, total_tasks, use_llm=True)
    result = handle_task_command(command)
    return {"transcript": command_text, "result": result}

@app.get("/tasks")
def get_tasks(search: str = Query(None), sort: str = Query(None)):
    conn = sqlite3.connect(DB)
    if search:
        rows = conn.execute("SELECT * FROM tasks WHERE title LIKE ?", (f"%{search}%",)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM tasks").fetchall()
    tasks = [{"id": r[0], "title": r[1], "scheduled": r[2], "priority": r[3], "created": r[4], "updated": r[5]} for r in rows]
    if sort == "priority":
        tasks.sort(key=lambda t: (-(t["priority"] if t["priority"] else 0), t["title"]))
    elif sort == "scheduled":
        tasks.sort(key=lambda t: t["scheduled"] if t["scheduled"] else "")
    conn.close()
    return tasks
