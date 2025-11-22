import React, { useState } from "react";
import axios from "axios";
import styles from '../styles/Home.module.css';
import SpeechRecognition, { useSpeechRecognition } from "react-speech-recognition";

export default function VoiceCommand({ onSuccess }) {
  const [isSending, setIsSending] = useState(false);
  const [response, setResponse] = useState(null);
  const { transcript, listening, resetTranscript } = useSpeechRecognition();

  const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000").replace(/\/$/, '');

  const handleSend = async () => {
    setIsSending(true);
    setResponse(null);
    try {
      const res = await axios.post(`${API_BASE}/voice-command/text`, { command: transcript });
      setResponse(res.data.result);
      onSuccess(res.data.result);
      resetTranscript();
    } catch (err) {
      setResponse({ status: "error: request failed" });
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div>
      <button 
        className={styles.button}
        onClick={() => SpeechRecognition.startListening({ continuous: false })} 
        disabled={listening}
      >
        🎤 Start Speaking
      </button>
      <button 
        className={styles.button}
        onClick={SpeechRecognition.stopListening} 
        disabled={!listening}
      >
        🛑 Stop
      </button>
      <p>Transcript: {transcript}</p>
      <button 
        className={styles.button}
        onClick={handleSend} 
        disabled={!transcript || isSending}
      >
        Send Command
      </button>
      {response && (
        <div style={{ marginTop: "1em" }}>
          <span className={styles.status}><strong>Status:</strong> {response.status}</span>
          {response.title && <> <br /><strong>Task:</strong> {response.title}</>}
          {response.scheduled && <> <br /><strong>Scheduled:</strong> {response.scheduled}</>}
          {response.priority && <> <br /><strong>Priority:</strong> {response.priority}</>}
          {response.id && <> <br /><strong>ID:</strong> {response.id}</>}
        </div>
      )}
    </div>
  );
}
