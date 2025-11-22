from fastapi import FastAPI, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import requests
import os
import re
import dateparser
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

def find_title(text: str):
    text = text.lower()
    # Remove priority
    text = re.sub(r"priority\s*\d+", "", text)
    # Remove date/time words
    text = re.sub(r"\b(on|for|by|at|tomorrow|today|next|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{4}-\d{2}-\d{2})\b", "", text)
    # Remove "task"
    text = re.sub(r"\btask\b", "", text)
    # Remove double spaces, leading/trailing spaces
    text = re.sub(r"\s+", " ", text).strip()
    for action in ["delete", "add", "create", "make", "show", "push", "schedule", "move", "update", "work on"]:
        if text.startswith(action):
            text = text[len(action):].strip()
    text = re.sub(r"^(the|a|about)\s+", "", text)
    patterns = [
        r"(?:task to do|work on|about|to do|named) (.+?)(?:$|\s| with| for| at| by| on)",
        r"(?:create|make|add|set up|put) (?:a )?task (?:for )?(.*?)(?:$|\s| with| for| at| by| on)",
        r"(?:delete|remove) (?:the )?task (?:about|named)? (.+?)(?:$|\s| with| for| at| by| on)",
        r"(?:update|push|move|schedule) (?:the )?task (?:about|named)? (.+?)(?:$|\s| to| at| by| on)",
        r"(?:show|display) (?:me )?(?:all )?(.+?)(?:$|\s| tasks| task)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip().rstrip(".!?, ")
    return text.strip().rstrip(".!?, ")

def find_date(text: str):
    date = dateparser.parse(text, settings={"PREFER_DATES_FROM": "future"})
    return date.isoformat() if date else None

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
    # First, try LLM intent extraction
    if use_llm and HF_TOKEN:
        raw = query_llm(text)
        if raw:
            try:
                # If output contains fenced code block, extract JSON inside
                if "```" in raw:
                    code_chunks = raw.split("```")
                    json_candidate = ""
                    for chunk in code_chunks:
                        if "{" in chunk:
                            json_candidate = chunk[chunk.find("{"):]
                            break
                    command = json.loads(json_candidate)
                else:
                    command = json.loads(raw)
                return command
            except Exception as e:
                print("LLM could not parse JSON, falling back. Output was:", raw)

    # Fallback: regex
    text_l = text.lower()
    index = extract_index(text_l, total=total_tasks)
    priority = extract_priority(text_l)
    scheduled = find_date(text_l)
    title = find_title(text_l)
    sort_by = find_sort(text_l)

    if re.search(r"(show|display)", text_l):
        return {"action": "show", "title": title if title else None, "sort": sort_by}

    if re.search(r"delete|remove", text_l) and index is not None:
        return {"action": "delete", "index": index}

    elif re.search(r"delete|remove|get rid of", text_l) and title:
        return {"action": "delete", "title": title}

    elif re.search(r"(make|add|create|work on|task to do|put)", text_l) and title:
        return {"action": "create", "title": title, "scheduled": scheduled, "priority": priority}

    elif re.search(r"(push|schedule|move|update|reschedule|change)", text_l) and title and scheduled:
        return {"action": "update_scheduled", "title": title, "scheduled": scheduled}

    elif re.search(r"(push|schedule|move|update|reschedule|change)", text_l) and index is not None and scheduled:
        return {"action": "update_scheduled_index", "index": index, "scheduled": scheduled}

    elif ("priority" in text_l or "prio" in text_l or "index" in text_l) and title and priority is not None:
        return {"action": "update_priority", "title": title, "priority": priority}

    elif ("priority" in text_l or "prio" in text_l or "index" in text_l) and index is not None and priority is not None:
        return {"action": "update_priority_index", "index": index, "priority": priority}

    return {"action": None}

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
        cursor.execute(
            "INSERT INTO tasks (title, scheduled, priority, created, updated) VALUES (?, ?, ?, ?, ?)",
            (title, scheduled, priority, now, now),
        )
        conn.commit()
        result = {"status": "Task created.", "title": title, "scheduled": scheduled, "priority": priority, "created": now}
    elif action == "show":
        rows = cursor.execute("SELECT * FROM tasks").fetchall()
        if title:
            filtered = [
                {"id": r[0], "title": r[1], "scheduled": r[2], "priority": r[3], "created": r[4], "updated": r[5]}
                for r in rows if title in r[1].lower()
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
        cursor.execute("DELETE FROM tasks WHERE title LIKE ?", (f"%{title}%",))
        conn.commit()
        affected = cursor.rowcount
        if affected > 0:
            result = {"status": f"Deleted {affected} task(s) matching '{title}'."}
        else:
            result = {"status": f"No tasks matched '{title}'."}
    elif action == "update_scheduled" and title and scheduled:
        cursor.execute(
            "UPDATE tasks SET scheduled=?, updated=? WHERE title LIKE ?", (scheduled, now, f"%{title}%")
        )
        conn.commit()
        affected = cursor.rowcount
        if affected > 0:
            result = {"status": f"Task(s) matching '{title}' scheduled for {scheduled}.", "updated": now}
        else:
            result = {"status": f"No tasks matched '{title}' to reschedule."}
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
        cursor.execute(
            "UPDATE tasks SET priority=?, updated=? WHERE title LIKE ?", (priority, now, f"%{title}%")
        )
        conn.commit()
        affected = cursor.rowcount
        if affected > 0:
            result = {"status": f"Priority of tasks matching '{title}' updated to {priority}.", "updated": now}
        else:
            result = {"status": f"No tasks matched '{title}' to update priority."}
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
    command_text = cmd.get("command", "")
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
