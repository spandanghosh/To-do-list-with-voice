import React, { useEffect, useState } from "react";
import axios from "axios";
import VoiceCommand from "../components/VoiceCommand";
import TaskList from "../components/TaskList";
import styles from '../styles/Home.module.css'; // Import your custom styles

export default function HomePage() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Fetch tasks from backend
  const fetchTasks = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await axios.get("http://127.0.0.1:8000/tasks");
      setTasks(res.data);
    } catch (err) {
      setError("Failed to fetch tasks. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchTasks();
  }, []);

  // Refresh after command
  const handleCommandResult = (result) => {
    fetchTasks();
  };

  return (
    <div className={styles.main}>
      <h1 className={styles.title}>Voice-First To-Do List</h1>
      <VoiceCommand onSuccess={handleCommandResult} />
      <div>
        <h2>Current Tasks</h2>
        {loading ? (
          <p>Loading tasks...</p>
        ) : (
          <ul className={styles.tasksList}>
            <TaskList tasks={tasks} />
          </ul>
        )}
        {error && <p style={{color: 'red'}}>{error}</p>}
        <button onClick={fetchTasks} className={styles.button} style={{marginTop: "12px"}}>
          Refresh Tasks
        </button>
      </div>
    </div>
  );
}
