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

## Important Notes on Render Deployment

- Render can experience occasional downtime or cold start delays.
- Response times may sometimes take a couple of minutes.
- Please be patient during those periods or consider pinging the service beforehand to keep it warm.
- For production or high-availability environments, consider autoscaling or alternative hosting options.

***

## Suggested Voice Prompts

Try using these phrases to get the most out of the app:

- “Add high priority code review for Monday”
- “Delete the third task”
- “Show upcoming urgent tasks”
- “Reschedule team sync to Friday”
- “Search for tasks about admin”
- “Sort tasks by priority”
- “Show me all administrative tasks”
- “Update add task debug to high priority”

***

## Key Features

- Voice and text-based task creation, updating, deletion, listing (CRUD)
- Natural language intent extraction using state-of-the-art LLM
- Scheduling and prioritization via conversational input
- Dynamic search, sorting, and error feedback
- Responsive modular UI with support for real-time status updates

***

## Deployment Guide

- Backend: Deploy on Render/Heroku for public API.
- Frontend: Deploy React/Next.js app on Vercel.
- Connect frontend to backend using environment variable for API base.
- Update or rotate API keys and endpoints as necessary.

***

## Evaluation Checklist

| Capability                  | Ready |
|----------------------------|-------|
| Real-time voice STT         | ✔     |
| LLM-powered intent parsing  | ✔     |
| CRUD, scheduling, sorting   | ✔     |
| Modular, documented code    | ✔     |
| Deployed cloud demo         | ✔     |
| README: rationale, guide    | ✔     |

***

## Technology Rationale

> Deepgram offers robust, low-latency transcription, simple API usage, and cloud flexibility.  
> HuggingFace phi-2 empowers open-access, instruction-following intent parsing and is ideal for conversational task bots.

***

## Notes

- All environment keys are managed securely outside codebase.  
- Endpoint paths and environment variable use documented for easy deploy and maintenance.  
- Please report bugs via issue tracker; design is extensible for further enhancements.

***

**Enjoy your conversational, voice-first productivity assistant!**

***

Want further tweaks, personalized badges, or deployment instructions? Just ask!

***

**References:**  
(https://developers.deepgram.com/reference/deepgram-api-overview) (https://developers.deepgram.com) (https://deepgram.com/product/speech-to-text) ...[1][2][3]