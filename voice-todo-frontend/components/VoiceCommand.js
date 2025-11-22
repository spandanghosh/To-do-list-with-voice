import React, { useState } from "react";
import axios from "axios";
import SpeechRecognition, { useSpeechRecognition } from "react-speech-recognition";

export default function VoiceCommand({ onSuccess }) {
  const [isSending, setIsSending] = useState(false);
  const { transcript, listening, resetTranscript } = useSpeechRecognition();

  const handleSend = async () => {
    setIsSending(true);

    try {
      // Send transcript to backend (you can change this to send audio file if you want)
      const res = await axios.post("http://127.0.0.1:8000/voice-command/text", { command: transcript });
      onSuccess(res.data.result);
      resetTranscript();
    } catch (err) {
      alert("Request failed.");
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div>
      <button onClick={() => SpeechRecognition.startListening({ continuous: false })} disabled={listening}>
        🎤 Start Speaking
      </button>
      <button onClick={SpeechRecognition.stopListening} disabled={!listening}>
        🛑 Stop
      </button>
      <p>Transcript: {transcript}</p>
      <button onClick={handleSend} disabled={!transcript || isSending}>Send Command</button>
    </div>
  );
}
