from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import requests
import os
import re
import dateparser

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
            priority INTEGER
        )
        """
    )
    conn.close()

init_db()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

def speech_to_text(audio_bytes):
    response = requests.post(
        "https://api.deepgram.com/v1/listen",
        headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"},
        files={"audio": ("audio.wav", audio_bytes)},
    )
    response.raise_for_status()
    result = response.json()
    return result["results"]["channels"][0]["alternatives"][0]["transcript"]

def find_title(text: str) -> str:
    # Attempt to extract task title using common speech patterns
    patterns = [
        r"(?:task to do|work on|about) (.+)",  # e.g. "task to do buy milk"
        r"(?:create|make|add|set up|put) (?:a )?task (?:for )?(?:to )?(.*)",  # e.g. "make a task buy milk"
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(1).strip()
    # fallback: return whole text
    return text.strip()

def find_date(text: str):
    date = dateparser.parse(text, settings={"PREFER_DATES_FROM": "future"})
    return date.isoformat() if date else None

def handle_task_command(command: dict):
    action = command.get("action")
    title = command.get("title")
    scheduled = command.get("scheduled")
    
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    
    if action == "create" and title:
        cursor.execute(
            "INSERT INTO tasks (title, scheduled) VALUES (?, ?)",
            (title, scheduled),
        )
        conn.commit()
        result = {"status": "created", "title": title}
        
    elif action == "show":
        rows = cursor.execute("SELECT * FROM tasks").fetchall()
        result = [
            {"id": r[0], "title": r[1], "scheduled": r[2], "priority": r[3]} for r in rows
        ]
        
    elif action == "delete" and title:
        cursor.execute("DELETE FROM tasks WHERE title LIKE ?", (f"%{title}%",))
        conn.commit()
        result = {"status": "deleted", "title": title}
        
    elif action == "update" and title and scheduled:
        cursor.execute(
            "UPDATE tasks SET scheduled=? WHERE title LIKE ?", (scheduled, f"%{title}%")
        )
        conn.commit()
        result = {"status": "updated", "title": title, "scheduled": scheduled}
    
    else:
        result = {"status": "unknown command or missing info"}
        
    conn.close()
    return result

def parse_command(text):
    text_l = text.lower()
    if "show" in text_l:
        return {"action": "show"}

    if "delete" in text_l:
        return {"action": "delete", "title": find_title(text)}

    if "create" in text_l or "make" in text_l or "add" in text_l:
        return {"action": "create", "title": find_title(text)}

    if "push" in text_l or "schedule" in text_l or "move" in text_l:
        return {
            "action": "update",
            "title": find_title(text),
            "scheduled": find_date(text),
        }

    return {"action": None}

@app.post("/voice-command")
async def voice_command(audio: UploadFile):
    audio_bytes = await audio.read()
    transcript = speech_to_text(audio_bytes)
    command = parse_command(transcript)
    result = handle_task_command(command)
    return {"transcript": transcript, "result": result}

@app.get("/tasks")
def get_tasks():
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "scheduled": r[2], "priority": r[3]} for r in rows]
