import React, { useEffect, useState } from "react";
import axios from "axios";
import VoiceCommand from "../components/VoiceCommand";
import TaskList from "../components/TaskList";
import styles from '../styles/Home.module.css';

export default function HomePage() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("");

  // Fetch with sorting support
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
  const fetchTasks = async (searchQuery = "", sortQuery = "") => {
    setLoading(true);
    setError("");
    let url = `${API_BASE}/tasks`;
    let params = [];
    if (searchQuery) params.push(`search=${encodeURIComponent(searchQuery)}`);
    if (sortQuery) params.push(`sort=${sortQuery}`);
    if (params.length) url += "?" + params.join("&");
    try {
      const res = await axios.get(url);
      setTasks(res.data);
    } catch (err) {
      setError("Failed to fetch tasks. Ensure backend is running.");
      setTasks([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks("", sort);
    // eslint-disable-next-line
  }, [sort]);

  const handleCommandResult = (result) => {
    if (Array.isArray(result)) {
      setTasks(result);
      setError(result.length === 0 ? "No tasks match your query." : "");
    } else if (result && result.status) {
      fetchTasks(search, sort);
      if (result.status === "unknown command or missing info") {
        setError("Could not understand command. Try rephrasing or be more specific.");
      } else {
        setError("");
      }
    } else {
      fetchTasks(search, sort);
    }
  };

  return (
    <div className={styles.main}>
      <h1 className={styles.title}>Voice-First To-Do List</h1>
      <VoiceCommand onSuccess={handleCommandResult} />
      <div>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          className={styles.input}
          placeholder="Search tasks"
        />
        <button onClick={() => fetchTasks(search, sort)} className={styles.button}>
          Search
        </button>
        {loading ? (
          <p>Loading tasks...</p>
        ) : (
          <TaskList tasks={tasks} onSortChange={newSort => setSort(newSort)} />
        )}
        {error && <p className={styles.status}>{error}</p>}
        <button onClick={() => fetchTasks("", sort)} className={styles.button} style={{ marginTop: "12px" }}>
          Refresh Tasks
        </button>
      </div>
    </div>
  );
}
