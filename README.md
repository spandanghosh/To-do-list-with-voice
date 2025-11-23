# Conversational Voice Task Manager

A voice-first, AI-powered task manager enabling natural, conversational control over your to-do list.
It integrates real-time speech recognition and LLM-driven intent parsing to let users create, manage, and organize tasks effortlessly using plain English—through both voice and text.

---

## ✨ Features

* **Voice & Text-Based Task Management**
  Add, update, delete, search, and sort tasks using natural language.

* **Real-Time Speech Recognition (Deepgram)**
  Low-latency, accurate transcription optimized for conversational workflows.

* **Intent Parsing with phi-2 (HuggingFace)**
  Extracts CRUD operations, dates, priorities, and filters with high accuracy.

* **Friendly, Responsive UI**
  Built with React/Next.js, with real-time updates and modular components.

* **Cloud-Ready Deployment**
  Backend deployable on Render/Heroku; frontend deployable on Vercel.

---

## 🧠 Tech Stack

* **Backend:** FastAPI, Deepgram API, HuggingFace Inference API
* **Frontend:** Next.js + React
* **Other Tools:** Axios, dateparser, react-speech-recognition

---

## 🚀 Quickstart

### Backend (FastAPI)

#### 1. Install dependencies

```bash
pip install fastapi uvicorn requests dateparser python-multipart
```

#### 2. Set environment variables

```bash
export DEEPGRAM_API_KEY=your_deepgram_api_key
export HUGGINGFACE_TOKEN=your_huggingface_token
```

#### 3. Run the backend

```bash
uvicorn main:app --reload
```

Backend runs on:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

### Frontend (Next.js)

#### 1. Install dependencies

```bash
npm install axios react-speech-recognition
```

#### 2. Start development server

```bash
npm run dev
```

Or deploy via **Vercel**.

#### 3. Environment variable

Create `.env.local`:

```
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

---

## 🌐 Deployment Guide

### Backend

* Recommended: **Render** or **Heroku**
* Note: Render may show cold-start delays (1–2 minutes at times)
* Keep the service warm using periodic pings for smoother performance
* Use separate environment variables for production keys

### Frontend

* Deploy on **Vercel**
* Set `NEXT_PUBLIC_API_BASE` to your backend’s live URL

---

## 🎤 Example Voice Commands

* “Add high priority code review for Monday”
* “Delete the third task”
* “Search for tasks about admin”
* “Sort tasks by priority”
* “Reschedule team sync to Friday”
* “Update task debug to high priority”
* “Show upcoming urgent tasks”

---

## 🧪 Evaluation Checklist

| Capability                   | Status |
| ---------------------------- | ------ |
| Real-time speech recognition | ✔      |
| LLM intent parsing           | ✔      |
| CRUD + scheduling + sorting  | ✔      |
| Modular, documented code     | ✔      |
| Cloud deployment             | ✔      |
| Comprehensive README         | ✔      |

---

## 🔍 Technology Rationale

**Deepgram**

* Fast, accurate STT
* Works well for conversational latency (<2s)
* Simple and reliable DevEx

**phi-2 on HuggingFace**

* Open-source and instruction-tuned
* Works well for lightweight intent extraction
* Cost-free inference for prototypes

---

## 🔐 Notes on Security & Keys

* All API keys are stored outside the codebase
* Rotate keys periodically
* Backend endpoints are modular and easily extendable

---

## 🎬 Demo Video

[![Watch the demo video](https://img.youtube.com/vi/L0FDSvidHlM/0.jpg)](https://www.youtube.com/watch?v=L0FDSvidHlM)

---

## 📚 References

* [https://developers.deepgram.com/reference/deepgram-api-overview](https://developers.deepgram.com/reference/deepgram-api-overview)
* [https://developers.deepgram.com](https://developers.deepgram.com)
* [https://deepgram.com/product/speech-to-text](https://deepgram.com/product/speech-to-text)
* [https://www.youtube.com/watch?v=L0FDSvidHlM](https://www.youtube.com/watch?v=L0FDSvidHlM)

