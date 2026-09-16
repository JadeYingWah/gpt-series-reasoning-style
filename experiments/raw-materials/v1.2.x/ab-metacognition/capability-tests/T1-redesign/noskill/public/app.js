// ===== State =====
let todos = [];
let currentFilter = 'all';
let currentSort = 'created_desc';

// ===== DOM Elements =====
const form = document.getElementById('todo-form');
const todoList = document.getElementById('todo-list');
const emptyState = document.getElementById('empty-state');
const filterBtns = document.querySelectorAll('.filter-btn');
const sortSelect = document.getElementById('sort');
const editModal = document.getElementById('edit-modal');
const editForm = document.getElementById('edit-form');
const cancelEditBtn = document.getElementById('cancel-edit');

// ===== API Helpers =====
async function api(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

// ===== Load Todos =====
async function loadTodos() {
  try {
    todos = await api('/api/todos');
    render();
  } catch (err) {
    console.error('Failed to load todos:', err);
  }
}

// ===== Render =====
function render() {
  // Update counts
  document.getElementById('count-all').textContent = todos.length;
  document.getElementById('count-active').textContent = todos.filter(t => !t.completed).length;
  document.getElementById('count-completed').textContent = todos.filter(t => t.completed).length;

  // Filter
  let filtered = todos;
  if (currentFilter === 'active') {
    filtered = todos.filter(t => !t.completed);
  } else if (currentFilter === 'completed') {
    filtered = todos.filter(t => t.completed);
  }

  // Sort
  const priorityOrder = { high: 3, medium: 2, low: 1 };
  filtered = [...filtered].sort((a, b) => {
    switch (currentSort) {
      case 'created_asc':
        return new Date(a.created_at) - new Date(b.created_at);
      case 'due_asc':
        if (!a.due_date && !b.due_date) return 0;
        if (!a.due_date) return 1;
        if (!b.due_date) return -1;
        return new Date(a.due_date) - new Date(b.due_date);
      case 'priority_desc':
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      case 'created_desc':
      default:
        return new Date(b.created_at) - new Date(a.created_at);
    }
  });

  // Render list
  todoList.innerHTML = '';
  if (filtered.length === 0) {
    emptyState.style.display = 'block';
    emptyState.querySelector('p').textContent =
      currentFilter === 'all' ? '暂无待办事项，添加一个开始吧！' :
      currentFilter === 'active' ? '没有未完成的任务，太棒了！' :
      '还没有已完成的任务。';
    return;
  }
  emptyState.style.display = 'none';

  filtered.forEach(todo => {
    todoList.appendChild(createTodoElement(todo));
  });
}

function createTodoElement(todo) {
  const item = document.createElement('div');
  item.className = `todo-item priority-${todo.priority}${todo.completed ? ' completed' : ''}`;
  item.dataset.id = todo.id;

  // Checkbox
  const checkbox = document.createElement('input');
  checkbox.type = 'checkbox';
  checkbox.className = 'todo-checkbox';
  checkbox.checked = !!todo.completed;
  checkbox.addEventListener('change', () => toggleTodo(todo.id, checkbox.checked));

  // Content
  const content = document.createElement('div');
  content.className = 'todo-content';

  const title = document.createElement('div');
  title.className = 'todo-title';
  title.textContent = todo.title;
  content.appendChild(title);

  if (todo.description) {
    const desc = document.createElement('div');
    desc.className = 'todo-description';
    desc.textContent = todo.description;
    content.appendChild(desc);
  }

  // Meta
  const meta = document.createElement('div');
  meta.className = 'todo-meta';

  const priorityLabels = { high: '高优先级', medium: '中优先级', low: '低优先级' };
  const priorityBadge = document.createElement('span');
  priorityBadge.className = `badge badge-priority-${todo.priority}`;
  priorityBadge.textContent = priorityLabels[todo.priority];
  meta.appendChild(priorityBadge);

  if (todo.due_date) {
    const dueBadge = document.createElement('span');
    const isOverdue = !todo.completed && new Date(todo.due_date) < new Date(new Date().toDateString());
    dueBadge.className = `badge badge-due${isOverdue ? ' overdue' : ''}`;
    dueBadge.textContent = `📅 ${todo.due_date}${isOverdue ? ' (已逾期)' : ''}`;
    meta.appendChild(dueBadge);
  }

  content.appendChild(meta);

  // Actions
  const actions = document.createElement('div');
  actions.className = 'todo-actions';

  const editBtn = document.createElement('button');
  editBtn.className = 'icon-btn';
  editBtn.title = '编辑';
  editBtn.textContent = '✏️';
  editBtn.addEventListener('click', () => openEditModal(todo));

  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'icon-btn';
  deleteBtn.title = '删除';
  deleteBtn.textContent = '🗑️';
  deleteBtn.addEventListener('click', () => deleteTodo(todo.id));

  actions.appendChild(editBtn);
  actions.appendChild(deleteBtn);

  item.appendChild(checkbox);
  item.appendChild(content);
  item.appendChild(actions);

  return item;
}

// ===== CRUD Operations =====
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const title = document.getElementById('title').value.trim();
  if (!title) return;

  const data = {
    title,
    description: document.getElementById('description').value.trim(),
    priority: document.getElementById('priority').value,
    due_date: document.getElementById('due_date').value || null,
  };

  try {
    await api('/api/todos', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    form.reset();
    document.getElementById('priority').value = 'medium';
    loadTodos();
  } catch (err) {
    alert('添加失败: ' + err.message);
  }
});

async function toggleTodo(id, completed) {
  try {
    await api(`/api/todos/${id}/toggle`, {
      method: 'PATCH',
      body: JSON.stringify({ completed }),
    });
    loadTodos();
  } catch (err) {
    alert('操作失败: ' + err.message);
    loadTodos();
  }
}

async function deleteTodo(id) {
  if (!confirm('确定要删除这个待办事项吗？')) return;
  try {
    await api(`/api/todos/${id}`, { method: 'DELETE' });
    loadTodos();
  } catch (err) {
    alert('删除失败: ' + err.message);
  }
}

// ===== Edit Modal =====
function openEditModal(todo) {
  document.getElementById('edit-id').value = todo.id;
  document.getElementById('edit-title').value = todo.title;
  document.getElementById('edit-description').value = todo.description || '';
  document.getElementById('edit-priority').value = todo.priority;
  document.getElementById('edit-due_date').value = todo.due_date || '';
  editModal.style.display = 'flex';
}

function closeEditModal() {
  editModal.style.display = 'none';
}

cancelEditBtn.addEventListener('click', closeEditModal);
editModal.addEventListener('click', (e) => {
  if (e.target === editModal) closeEditModal();
});

editForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = document.getElementById('edit-id').value;
  const data = {
    title: document.getElementById('edit-title').value.trim(),
    description: document.getElementById('edit-description').value.trim(),
    priority: document.getElementById('edit-priority').value,
    due_date: document.getElementById('edit-due_date').value || null,
  };

  try {
    await api(`/api/todos/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    closeEditModal();
    loadTodos();
  } catch (err) {
    alert('保存失败: ' + err.message);
  }
});

// ===== Filter & Sort =====
filterBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    filterBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentFilter = btn.dataset.filter;
    render();
  });
});

sortSelect.addEventListener('change', (e) => {
  currentSort = e.target.value;
  render();
});

// ===== Init =====
loadTodos();
