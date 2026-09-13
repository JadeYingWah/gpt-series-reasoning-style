const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

// Ensure data directory exists
const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true });
}

const db = new Database(path.join(dataDir, 'todos.db'));

// Enable WAL mode for better concurrent read performance
db.pragma('journal_mode = WAL');

// Create todos table if not exists
db.exec(`
  CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    priority TEXT NOT NULL DEFAULT 'medium' CHECK(priority IN ('low', 'medium', 'high')),
    due_date TEXT,
    completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
  );
`);

// Prepared statements
const stmt = {
  getAll: db.prepare('SELECT * FROM todos ORDER BY completed ASC, created_at DESC'),
  getById: db.prepare('SELECT * FROM todos WHERE id = ?'),
  insert: db.prepare(`
    INSERT INTO todos (title, description, priority, due_date)
    VALUES (?, ?, ?, ?)
  `),
  update: db.prepare(`
    UPDATE todos
    SET title = ?, description = ?, priority = ?, due_date = ?, completed = ?, updated_at = datetime('now')
    WHERE id = ?
  `),
  toggleComplete: db.prepare(`
    UPDATE todos SET completed = ?, updated_at = datetime('now') WHERE id = ?
  `),
  delete: db.prepare('DELETE FROM todos WHERE id = ?'),
};

function getAllTodos() {
  return stmt.getAll.all();
}

function getTodoById(id) {
  return stmt.getById.get(id);
}

function createTodo({ title, description = '', priority = 'medium', due_date = null }) {
  const info = stmt.insert.run(title, description, priority, due_date);
  return getTodoById(info.lastInsertRowid);
}

function updateTodo(id, { title, description, priority, due_date, completed }) {
  const existing = getTodoById(id);
  if (!existing) return null;
  stmt.update.run(
    title ?? existing.title,
    description ?? existing.description,
    priority ?? existing.priority,
    due_date ?? existing.due_date,
    completed ?? existing.completed,
    id
  );
  return getTodoById(id);
}

function toggleTodoComplete(id, completed) {
  const existing = getTodoById(id);
  if (!existing) return null;
  stmt.toggleComplete.run(completed ? 1 : 0, id);
  return getTodoById(id);
}

function deleteTodo(id) {
  const info = stmt.delete.run(id);
  return info.changes > 0;
}

module.exports = {
  getAllTodos,
  getTodoById,
  createTodo,
  updateTodo,
  toggleTodoComplete,
  deleteTodo,
};
