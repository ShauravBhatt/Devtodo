# DevTodo – A Modern CLI Task Manager 🚀
```

DevTodo is a lightweight, emoji-powered command-line task manager for developers and power users.
It supports priorities, tags, filtering, and productivity stats to keep you organized inside the terminal.
```

```markdown
## ✨ Features
```

```text
📝 Add, update, complete, and remove tasks
🏷️ Organize with tags (#work, #personal)
🔥 Emoji indicators for status and priority
🔍 Filter and sort by tags, priority, or created date
📊 Productivity dashboard with completion rates and categories
💾 Tasks stored locally in .todo.json (portable & versionable)
🎉 Beginner-friendly welcome screen and help guide
```

```markdown
## 📦 Installation
```

```bash
# Clone repository
git clone https://github.com/your-username/devtodo.git
cd devtodo

# Make it executable
chmod +x devtodo.py

# Move to /usr/local/bin for global usage
sudo mv devtodo.py /usr/local/bin/devtodo
```

```markdown
## ⚡ Usage Examples
```

```bash
# Add tasks
devtodo add "Fix login bug @urgent #backend"
devtodo add "Write documentation #work @normal"

# List tasks
devtodo ls
devtodo ls --tag backend
devtodo ls --priority urgent

# Mark complete
devtodo done 1

# Update tasks
devtodo update 2 --priority high --tag docs

# Show productivity stats
devtodo stats

# Clear completed tasks
devtodo clear
```

```markdown
## 📊 Sample Output
```

```text
📋 Pending Tasks (2 of 3):
  🔴 URGENT:
    1. ⏳ 🔴 Fix login bug #backend (today)
  🔵 NORMAL:
    2. ⏳ 🔵 Write documentation #work

✅ Completed task 3: Update dependencies
```

```markdown
## 🛠️ Help
```

```bash
devtodo help
```

```markdown
## 💡 Why DevTodo?
```

```text
Stay focused, organized, and productive.
Manage coding tasks, bug fixes, or personal goals efficiently—all inside your terminal.
```

