const express = require('express');
const path = require('path');
const db = require('./db');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ===== API Routes =====

// GET /api/todos - List all todos
app.get('/api/todos', (req, res) => {
  try {
    const todos = db.getAllTodos();
    res.json(todos);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/todos/:id - Get single todo
app.get('/api/todos/:id', (req, res) => {
  try {
    const todo = db.getTodoById(req.params.id);
    if (!todo) return res.status(404).json({ error: 'Todo not found' });
    res.json(todo);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// POST /api/todos - Create todo
app.post('/api/todos', (req, res) => {
  try {
    const { title, description, priority, due_date } = req.body;
    if (!title || !title.trim()) {
      return res.status(400).json({ error: 'Title is required' });
    }
    const todo = db.createTodo({
      title: title.trim(),
      description: description || '',
      priority: priority || 'medium',
      due_date: due_date || null,
    });
    res.status(201).json(todo);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PUT /api/todos/:id - Update todo
app.put('/api/todos/:id', (req, res) => {
  try {
    const { title, description, priority, due_date, completed } = req.body;
    const todo = db.updateTodo(req.params.id, {
      title,
      description,
      priority,
      due_date,
      completed,
    });
    if (!todo) return res.status(404).json({ error: 'Todo not found' });
    res.json(todo);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// PATCH /api/todos/:id/toggle - Toggle complete status
app.patch('/api/todos/:id/toggle', (req, res) => {
  try {
    const { completed } = req.body;
    const todo = db.toggleTodoComplete(req.params.id, completed);
    if (!todo) return res.status(404).json({ error: 'Todo not found' });
    res.json(todo);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// DELETE /api/todos/:id - Delete todo
app.delete('/api/todos/:id', (req, res) => {
  try {
    const deleted = db.deleteTodo(req.params.id);
    if (!deleted) return res.status(404).json({ error: 'Todo not found' });
    res.json({ message: 'Todo deleted' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`Todo app running at http://localhost:${PORT}`);
});
