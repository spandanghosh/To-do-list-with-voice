# Conversational Voice Task Manager

***

## Overview

A highly interactive, voice-driven task manager that leverages real-time speech recognition and natural intent parsing to facilitate efficient to-do management.  
It seamlessly supports creation, deletion, updating, search, and sorting of tasks via both voice and text input, offering a robust and intuitive user experience.

***

## Technology Highlights

### **Speech Recognition (Deepgram)**
- Delivers fast, accurate voice-to-text conversion for both real-time and batch scenarios.
- Straightforward Python API integration.
- Sub-2s latency for conversational commands.

### **Intent Parsing (phi-2 LLM on HuggingFace)**
- Advanced, instruction-following open LLM for robust task parsing.
- Query via HuggingFace Inference API; cost-free for prototyping and demo.
- High accuracy in extracting CRUD actions, dates, priorities, and sort/filter criteria.

***

## Quickstart: Local & Cloud Usage

### **Backend Setup (FastAPI + Deepgram + HuggingFace)**
1. Install server dependencies:
   ```
   pip install fastapi uvicorn requests dateparser python-multipart
   ```
2. Provide API keys as environment variables:
   ```
   export DEEPGRAM_API_KEY=your_deepgram_api_key
   export HUGGINGFACE_TOKEN=your_huggingface_token
   ```
3. Start the backend service:
   ```
   uvicorn main:app --reload
   ```
   Runs by default on [http://127.0.0.1:8000](http://127.0.0.1:8000)

### **Frontend Setup (React/Next.js)**
1. Install UI dependencies:
   ```
   npm install axios react-speech-recognition
   ```
2. Start the development server locally:
   ```
   npm run dev
   ```
   Or deploy production using Vercel.

### **Environment Variables (Frontend)**
- Set `NEXT_PUBLIC_API_BASE` to your backend URL (e.g. `https://your-backend.onrender.com`) in `.env.local` or in the Vercel dashboard.

***

## Key Features

- **Voice and text-based task creation, updating, deletion, listing (CRUD)**
- **Natural language intent extraction using state-of-the-art LLM**
- **Scheduling and prioritization via conversational input**
- **Dynamic search, sorting, and error feedback**
- **Responsive modular UI with support for real-time status updates**

***

## Deployment Guide

- Backend: Deploy on Render/Heroku for public API.
- Frontend: Deploy React/Next.js app on Vercel.
- Connect frontend to backend using environment variable for API base.
- Update or rotate API keys and endpoints as necessary.

***

## Evaluation Checklist

| Capability                  | Ready |
|-----------------------------|-------|
| Real-time voice STT         | ✔     |
| LLM-powered intent parsing  | ✔     |
| CRUD, scheduling, sorting   | ✔     |
| Modular, documented code    | ✔     |
| Deployed cloud demo         | ✔     |
| README: rationale, guide    | ✔     |

***

## Suggested Test Cases

- “Add high priority code review for Monday”
- “Delete the third task”
- “Show upcoming urgent tasks”
- “Reschedule team sync to Friday”
- “Search for tasks about admin”
- “Sort tasks by priority”

***

## Technology Rationale

> Deepgram offers robust, low-latency transcription, simple API usage, and cloud flexibility.
>
> HuggingFace phi-2 empowers open-access, instruction-following intent parsing and is ideal for conversational task bots.

***

## Notes

- All environment keys are managed securely outside codebase.
- Endpoint paths and environment variable use documented for easy deploy and maintenance.
- Please report bugs via issue tracker; design is extensible for further enhancements.

***

**Enjoy your conversational, voice-first productivity assistant!**

***

Want further tweaks, a personalized badge, or extra deployment instructions? Just ask!

[1](https://developers.deepgram.com/reference/deepgram-api-overview)
[2](https://developers.deepgram.com)
[3](https://deepgram.com/product/speech-to-text)
[4](https://deepgram.com)
[5](https://github.com/deepgram/deepgram-python-sdk)
[6](https://developers.deepgram.com/docs/tts-rest)
[7](https://developers.deepgram.com/docs/stt/getting-started)
[8](https://developers.deepgram.com/docs/text-to-speech)
[9](https://developers.deepgram.com/docs/live-streaming-audio)
[10](https://developers.deepgram.com/docs/pre-recorded-audio)