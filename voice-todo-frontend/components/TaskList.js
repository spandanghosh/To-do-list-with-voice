import React, { useState } from "react";
import styles from '../styles/Home.module.css';

export default function TaskList({ tasks, onSortChange }) {
  const [sort, setSort] = useState("");

  function handleSort(e) {
    setSort(e.target.value);
    if (onSortChange) onSortChange(e.target.value); // Notify parent!
  }

  if (!tasks || tasks.length === 0) {
    return <p>No tasks found.</p>;
  }
  return (
    <div>
      <div style={{ marginBottom: 10 }}>
        <label htmlFor="sort">Sort by: </label>
        <select id="sort" className={styles.input} value={sort} onChange={handleSort}>
          <option value="">Default (by Index)</option>
          <option value="priority">Priority</option>
          <option value="scheduled">Scheduled</option>
        </select>
      </div>
      <table className={styles.table}>
        <thead>
          <tr className={styles.tr}>
            <th className={styles.th}>Index</th>
            <th className={styles.th}>Title</th>
            <th className={styles.th}>Scheduled</th>
            <th className={styles.th}>Priority</th>
            <th className={styles.th}>Created</th>
            <th className={styles.th}>Updated</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task, i) => (
            <tr key={task.id} className={styles.tr}>
              <td className={styles.td}>{i + 1}</td>
              <td className={styles.td} style={{ fontWeight: 600 }}>{task.title}</td>
              <td className={styles.td}>{task.scheduled ? `${task.scheduled}.` : ""}</td>
              <td className={styles.td}>
                {typeof task.priority === "number" && (
                  <span style={{
                    backgroundColor: task.priority === 3 ? '#e11d48'
                      : task.priority === 2 ? '#f59e42'
                      : '#38bdf8',
                    color: '#fff'
                  }}>
                    {task.priority}.
                  </span>
                )}
              </td>
              <td className={styles.td}>
            {task.created ? new Date(task.created).toLocaleString() : ""}
            </td>
            <td className={styles.td}>
            {task.updated ? new Date(task.updated).toLocaleString() : ""}
            </td>

            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
