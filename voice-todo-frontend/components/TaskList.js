export default function TaskList({ tasks }) {
  return (
    <div>
      <h2>Current Tasks</h2>
      <ul>
        {tasks.map(task => (
          <li key={task.id}>
            {task.title}
            {task.scheduled && <span> (Scheduled: {task.scheduled})</span>}
            {task.priority && <span> [Priority: {task.priority}]</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
