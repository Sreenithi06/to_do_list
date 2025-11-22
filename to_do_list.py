

from flask import Flask, request, redirect, url_for, render_template_string, g
import sqlite3
import os

DATABASE = 'todos.db'
app = Flask(__name__)
app.config['SECRET_KEY'] = 'change-me'

# --- DB helpers ---

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    if not os.path.exists(DATABASE):
        with app.app_context():
            db = get_db()
            db.executescript('''
            CREATE TABLE todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT
                
            );
            ''')
            db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Routes ---

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Todo List</title>
  <style>
    body{font-family: system-ui, -apple-system, Roboto, 'Segoe UI', Arial; max-width:900px;margin:24px auto;color:#111}
    header{display:flex;justify-content:space-between;align-items:center}
    form{margin-top:12px}
    .todo{border:1px solid #eee;padding:12px;border-radius:8px;margin:8px 0;display:flex;justify-content:space-between}
    .meta{font-size:12px;color:#666}
    .done{opacity:0.6;text-decoration:line-through}
    .controls form{display:inline}
    .btn{border:0;background:#1976d2;color:white;padding:6px 10px;border-radius:6px;cursor:pointer}
    .btn.secondary{background:#f0f0f0;color:#111}
    .btn.danger{background:#d32f2f}
    textarea{width:100%;min-height:70px}
  </style>
</head>

<body>
  <header>
    <h1>Todo List</h1>
    <div>
      <strong>{{ todos|length }}</strong> items
    </div>
  </header>

  <section>
    <h3>Add todo</h3>
    <form method="post" action="{{ url_for('add') }}">
      <input name="title" placeholder="Title" required style="width:100%;padding:8px;border-radius:6px;border:1px solid #ddd">
      <div style="height:8px"></div>
      <textarea name="description" placeholder="Optional description"></textarea>
      <div style="height:8px"></div>
      <button class="btn" type="submit">Add</button>
    </form>
  </section>

  <section>
    <h3>Your todos</h3>
    {% for t in todos %}
      <div class="todo">
        <div>
          <div class="title {% if t.done %}done{% endif %}"><strong>{{ t.title }}</strong></div>
          {% if t.description %}<div class="meta">{{ t.description }}</div>{% endif %}
          <div class="meta">Created: {{ t.created_at }}</div>
        </div>
        <div class="controls">
          <form method="post" action="{{ url_for('toggle', todo_id=t.id) }}" style="display:inline">
            <button class="btn secondary" type="submit">{% if t.done %}Undo{% else %}Done{% endif %}</button>
          </form>
          <form method="get" action="{{ url_for('edit', todo_id=t.id) }}" style="display:inline">
            <button class="btn secondary" type="submit">Edit</button>
          </form>
#           <form method="post" action="{{ url_for('delete', todo_id=t.id) }}" style="display:inline" wrapped
           onsubmit="return confirm('Delete this todo?')">
            <button class="btn danger" type="submit">Delete</button>
          </form>
        </div>
      </div>
    {% else %}
      <p>No todos yet — add one above.</p>
    {% endfor %}
  </section>

</body>
</html>
"""

EDIT_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Edit Todo</title>
</head>
<body>
  <h1>Edit</h1>
  <form method="post" action="">
    <input name="title" value="{{ todo.title }}" required style="width:100%;padding:8px;margin-bottom:8px">
    <textarea name="description">{{ todo.description }}</textarea>
    <div style="height:8px"></div>
    <button type="submit">Save</button>
  </form>
  <p><a href="{{ url_for('index') }}">Back</a></p>
</body>
</html>
"""

@app.route('/')
def index():
    db = get_db()
    cur = db.execute('SELECT id, title, description, done, created_at FROM todos ORDER BY created_at DESC')
    todos = cur.fetchall()
    return render_template_string(TEMPLATE, todos=todos)

@app.route('/add', methods=['POST'])
def add():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    if title:
        db = get_db()
        db.execute('INSERT INTO todos (title, description) VALUES (?, ?)', (title, description))
        db.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:todo_id>', methods=['GET', 'POST'])
def edit(todo_id):
    db = get_db()
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        description = request.form.get('description','').strip()
        db.execute('UPDATE todos SET title = ?, description = ? WHERE id = ?', (title, description, todo_id))
        db.commit()
        return redirect(url_for('index'))
    cur = db.execute('SELECT * FROM todos WHERE id = ?', (todo_id,))
    todo = cur.fetchone()
    if not todo:
        return 'Not found', 404
    return render_template_string(EDIT_TEMPLATE, todo=todo)

@app.route('/toggle/<int:todo_id>', methods=['POST'])
def toggle(todo_id):
    db = get_db()
    cur = db.execute('SELECT done FROM todos WHERE id = ?', (todo_id,))
    row = cur.fetchone()
    if row:
        new = 0 if row['done'] else 1
        db.execute('UPDATE todos SET done = ? WHERE id = ?', (new, todo_id))
        db.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete(todo_id):
    db = get_db()
    db.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
    db.commit()
    return redirect(url_for('index'))

if __name__ == "__main__":
    init_db()
    app.run(debug=True, use_reload=False, port=5001)

    

    
