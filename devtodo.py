#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta

TODO_FILENAME = ".todo.json"
VERSION = "2.0"

# Priority levels
PRIORITIES = {
    'low': 1,
    'normal': 2,
    'high': 3,
    'urgent': 4
}

PRIORITY_ICONS = {
    1: '🟢',  # low
    2: '🔵',  # normal
    3: '🟠',  # high
    4: '🔴'   # urgent
}

PRIORITY_NAMES = {v: k for k, v in PRIORITIES.items()}

def get_todo_path():
    return Path(os.getcwd()) / TODO_FILENAME

def load_tasks():
    path = get_todo_path()
    if path.exists():
        try:
            with open(path, "r") as f:
                tasks = json.load(f)
                # Migrate old tasks without priority/tags
                for task in tasks:
                    if 'priority' not in task:
                        task['priority'] = 2  # default to normal
                    if 'tags' not in task:
                        task['tags'] = []
                    if 'created' not in task:
                        task['created'] = datetime.now().isoformat()
                return tasks
        except (json.JSONDecodeError, KeyError) as e:
            print(f"❌ Error reading todo file: {e}")
            return []
    return []

def save_tasks(tasks):
    path = get_todo_path()
    try:
        with open(path, "w") as f:
            json.dump(tasks, f, indent=2)
    except Exception as e:
        print(f"❌ Error saving tasks: {e}")

def parse_tags_and_priority(desc):
    """Extract tags and priority from description"""
    original_desc = desc

    # Extract tags (format: #tag1 #tag2)
    tags = re.findall(r'#(\w+)', desc)
    desc = re.sub(r'#\w+\s*', '', desc).strip()

    # Extract priority (format: @high, @urgent, @normal, @low) - changed from ! to avoid shell conflicts
    priority_match = re.search(r'@(\w+)', desc)
    priority = 2  # default normal

    if priority_match:
        priority_str = priority_match.group(1).lower()
        if priority_str in PRIORITIES:
            priority = PRIORITIES[priority_str]
        else:
            print(f"⚠️  Unknown priority '{priority_str}', using 'normal'. Valid: {', '.join(PRIORITIES.keys())}")
        desc = re.sub(r'@\w+\s*', '', desc).strip()

    # Clean up extra whitespace
    desc = ' '.join(desc.split())

    if not desc:
        print(f"❌ Task description cannot be empty after parsing tags/priority from: '{original_desc}'")
        return None, [], priority

    return desc, tags, priority

def add_task(desc, priority=None, tags=None):
    parsed_result = parse_tags_and_priority(desc)
    if parsed_result[0] is None:
        return False

    desc, inline_tags, inline_priority = parsed_result

    final_priority = PRIORITIES.get(priority.lower() if priority else None, inline_priority)
    final_tags = tags if tags else inline_tags

    tasks = load_tasks()
    task = {
        "desc": desc,
        "done": False,
        "priority": final_priority,
        "tags": final_tags,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    tasks.append(task)
    save_tasks(tasks)

    priority_name = PRIORITY_NAMES[final_priority]
    tags_str = f" #{' #'.join(final_tags)}" if final_tags else ""
    print(f"✅ Added [{priority_name.upper()}]: {desc}{tags_str}")
    return True

def format_task(task, index, show_created=False):
    status = "✅" if task["done"] else "⏳"
    priority_icon = PRIORITY_ICONS.get(task.get('priority', 2), '🔵')
    priority_name = PRIORITY_NAMES.get(task.get('priority', 2), 'normal')

    tags_str = f" #{' #'.join(task.get('tags', []))}" if task.get('tags') else ""

    created_str = ""
    if show_created and task.get('created'):
        try:
            created = datetime.fromisoformat(task['created'])
            days_ago = (datetime.now() - created).days
            if days_ago == 0:
                created_str = " (today)"
            elif days_ago == 1:
                created_str = " (yesterday)"
            elif days_ago < 7:
                created_str = f" ({days_ago}d ago)"
            else:
                created_str = f" ({created.strftime('%m/%d')})"
        except:
            pass

    return f"{index:2d}. {status} {priority_icon} {task['desc']}{tags_str}{created_str}"

def list_tasks(filter_tags=None, filter_priority=None, sort_by="priority", show_done=False, show_created=False):
    tasks = load_tasks()
    if not tasks:
        print("🎉 Awesome! No pending tasks - you're all caught up!")
        return

    filtered_tasks = tasks

    if not show_done:
        filtered_tasks = [t for t in filtered_tasks if not t.get('done', False)]

    if filter_tags:
        filtered_tasks = [t for t in filtered_tasks
                         if any(tag.lower() in [tag.lower() for tag in t.get('tags', [])] for tag in filter_tags)]

    if filter_priority:
        priority_level = PRIORITIES.get(filter_priority.lower())
        if priority_level:
            filtered_tasks = [t for t in filtered_tasks
                             if t.get('priority', 2) == priority_level]

    if sort_by == "priority":
        filtered_tasks.sort(key=lambda x: (-x.get('priority', 2), x.get('created', '')))
    elif sort_by == "created":
        filtered_tasks.sort(key=lambda x: x.get('created', ''), reverse=True)

    if not filtered_tasks:
        filter_desc = []
        if filter_tags:
            filter_desc.append(f"tags: #{' #'.join(filter_tags)}")
        if filter_priority:
            filter_desc.append(f"priority: {filter_priority}")
        if not show_done:
            filter_desc.append("status: pending")

        filters = f" ({', '.join(filter_desc)})" if filter_desc else ""
        print(f"🔍 No tasks match your filters{filters}")
        print("💡 Try: devtodo ls --done  or  devtodo ls  (to see all pending)")
        return

    total_tasks = len(tasks)
    pending_tasks = len([t for t in tasks if not t.get('done', False)])
    done_tasks = total_tasks - pending_tasks

    if show_done:
        print(f"📋 All Tasks ({total_tasks} total, {pending_tasks} pending, {done_tasks} done):")
    else:
        print(f"📋 Pending Tasks ({pending_tasks} of {total_tasks}):")

    if sort_by == "priority" and not filter_priority:
        current_priority = None
        for task in filtered_tasks:
            task_priority = task.get('priority', 2)
            if task_priority != current_priority:
                priority_name = PRIORITY_NAMES[task_priority]
                if current_priority is not None:
                    print()
                print(f"  {PRIORITY_ICONS[task_priority]} {priority_name.upper()}:")
                current_priority = task_priority

            original_idx = tasks.index(task) + 1
            formatted_task = format_task(task, original_idx, show_created)
            print(f"    {formatted_task}")
    else:
        for task in filtered_tasks:
            original_idx = tasks.index(task) + 1
            formatted_task = format_task(task, original_idx, show_created)
            print(formatted_task)

def mark_done(index):
    tasks = load_tasks()
    if not (1 <= index <= len(tasks)):
        print(f"❌ Invalid task number. Use 1-{len(tasks)}")
        return False

    if tasks[index - 1]["done"]:
        print(f"ℹ️  Task {index} is already completed")
        return True

    tasks[index - 1]["done"] = True
    save_tasks(tasks)
    print(f"✅ Completed task {index}: {tasks[index - 1]['desc']}")
    return True

def mark_undone(index):
    tasks = load_tasks()
    if not (1 <= index <= len(tasks)):
        print(f"❌ Invalid task number. Use 1-{len(tasks)}")
        return False

    if not tasks[index - 1]["done"]:
        print(f"ℹ️  Task {index} is already pending")
        return True

    tasks[index - 1]["done"] = False
    save_tasks(tasks)
    print(f"⏳ Reopened task {index}: {tasks[index - 1]['desc']}")
    return True

def delete_task(index):
    tasks = load_tasks()
    if not (1 <= index <= len(tasks)):
        print(f"❌ Invalid task number. Use 1-{len(tasks)}")
        return False

    removed = tasks.pop(index - 1)
    save_tasks(tasks)
    status = "completed" if removed['done'] else "pending"
    print(f"🗑️  Removed {status} task: {removed['desc']}")
    return True

def update_task(index, desc=None, priority=None, tags=None):
    tasks = load_tasks()
    if not (1 <= index <= len(tasks)):
        print(f"❌ Invalid task number. Use 1-{len(tasks)}")
        return False

    task = tasks[index - 1]
    changes = []

    if desc:
        parsed_result = parse_tags_and_priority(desc)
        if parsed_result[0] is None:
            return False

        new_desc, inline_tags, inline_priority = parsed_result
        old_desc = task['desc']
        task['desc'] = new_desc
        changes.append(f"description: '{old_desc}' → '{new_desc}'")

        if not priority and inline_priority != task.get('priority', 2):
            old_priority = PRIORITY_NAMES.get(task.get('priority', 2), 'normal')
            new_priority = PRIORITY_NAMES[inline_priority]
            task['priority'] = inline_priority
            changes.append(f"priority: {old_priority} → {new_priority}")

        if tags is None and inline_tags != task.get('tags', []):
            old_tags = task.get('tags', [])
            task['tags'] = inline_tags
            old_tags_str = f"#{' #'.join(old_tags)}" if old_tags else "none"
            new_tags_str = f"#{' #'.join(inline_tags)}" if inline_tags else "none"
            changes.append(f"tags: {old_tags_str} → {new_tags_str}")

    if priority:
        priority_level = PRIORITIES.get(priority.lower())
        if priority_level and priority_level != task.get('priority', 2):
            old_priority = PRIORITY_NAMES.get(task.get('priority', 2), 'normal')
            task['priority'] = priority_level
            changes.append(f"priority: {old_priority} → {priority}")

    if tags is not None:
        old_tags = task.get('tags', [])
        if tags != old_tags:
            task['tags'] = tags
            old_tags_str = f"#{' #'.join(old_tags)}" if old_tags else "none"
            new_tags_str = f"#{' #'.join(tags)}" if tags else "none"
            changes.append(f"tags: {old_tags_str} → {new_tags_str}")

    if not changes:
        print(f"ℹ️  No changes made to task {index}")
        return True

    save_tasks(tasks)
    print(f"📝 Updated task {index}:")
    for change in changes:
        print(f"   • {change}")
    return True

def clear_done():
    tasks = load_tasks()
    done_tasks = [t for t in tasks if t["done"]]
    new_tasks = [t for t in tasks if not t["done"]]

    if not done_tasks:
        print("ℹ️  No completed tasks to clear")
        return

    save_tasks(new_tasks)
    print(f"🧹 Cleared {len(done_tasks)} completed tasks")

    if len(done_tasks) <= 5:
        print("   Removed:")
        for task in done_tasks:
            tags_str = f" #{' #'.join(task.get('tags', []))}" if task.get('tags') else ""
            print(f"   • {task['desc']}{tags_str}")

def show_stats():
    tasks = load_tasks()
    if not tasks:
        print("📊 No tasks to analyze yet!")
        print("💡 Start by adding some tasks: devtodo add \"Your first task\"")
        return

    total = len(tasks)
    done = len([t for t in tasks if t['done']])
    pending = total - done
    completion_rate = (done / total * 100) if total > 0 else 0

    print(f"📊 Your Productivity Dashboard:")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"   📋 Total Tasks: {total}")
    print(f"   ✅ Completed: {done} ({completion_rate:.0f}%)")
    print(f"   ⏳ Pending: {pending}")

    if completion_rate >= 80:
        print(f"   🏆 Amazing! You're crushing it!")
    elif completion_rate >= 60:
        print(f"   🎯 Great progress! Keep it up!")
    elif completion_rate >= 40:
        print(f"   💪 You're making good headway!")
    elif completion_rate >= 20:
        print(f"   📈 Getting started - stay focused!")
    else:
        print(f"   🚀 Time to tackle those tasks!")

    if pending == 0 and total > 0:
        print("   🎉 All tasks completed! You're a productivity superstar!")
        return

    if pending > 0:
        priority_counts = {}
        for task in tasks:
            if not task['done']:
                priority = task.get('priority', 2)
                priority_name = PRIORITY_NAMES[priority]
                priority_counts[priority_name] = priority_counts.get(priority_name, 0) + 1

        if priority_counts:
            print(f"\n   🎯 What needs attention:")
            for priority_name in ['urgent', 'high', 'normal', 'low']:
                if priority_name in priority_counts:
                    count = priority_counts[priority_name]
                    icon = PRIORITY_ICONS[PRIORITIES[priority_name]]
                    print(f"      {icon} {priority_name.title()}: {count} task{'s' if count != 1 else ''}")

    tag_counts = {}
    for task in tasks:
        if not task['done']:
            for tag in task.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

    if tag_counts:
        print(f"\n   🏷️  Active categories:")
        for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"      #{tag}: {count} task{'s' if count != 1 else ''}")

    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

def show_welcome_interface():
    print(f"✨ Welcome to DevTodo v{VERSION}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    tasks = load_tasks()
    if tasks:
        print("\n📋 YOUR TASKS:")
        list_tasks()
        print(f"\n💡 TIP: Use 'devtodo done <number>' to mark tasks complete!")
    else:
        print("\n🎯 Ready to get organized? Let's add your first task!")
        print("\n💡 EXAMPLE: devtodo add \"Learn Python programming\"")

    print("\n🚀 GETTING STARTED:")
    print("   devtodo add \"Your task\"           ← Add a simple task")
    print("   devtodo add \"Fix bug @urgent\"    ← Add with priority")
    print("   devtodo add \"Code review #work\"  ← Add with tags")
    print("   devtodo ls                         ← See all tasks")
    print("   devtodo done 1                     ← Complete task #1")

    print("\n⚡ QUICK COMMANDS:")
    print("   add    ls    done    rm    update    stats    clear    help")

    print("\n🏷️  POWER FEATURES:")
    print("   #tag1 #tag2        → Organize with tags")
    print("   @urgent @high      → Set priority levels")
    print("   @normal @low       → Lower priorities")

    print("\n❓ Need help? Try 'devtodo help' for detailed guide")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

def show_help():
    help_text = f""" 
✨ DevTodo v{VERSION} - Your Personal Task Manager

🎯 ESSENTIAL COMMANDS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  add <task>           📝 Create a new task
  ls                   📋 Show your tasks
  done <number>        ✅ Mark task complete
  rm <number>          🗑️  Delete a task
  update <number>      ✏️  Modify a task
  stats                📊 View progress
  clear                🧹 Remove completed tasks
  help                 ❓ Show this guide

🏷️  SMART FEATURES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Priority Levels:     @urgent  @high  @normal  @low
  Tags:               #work #personal #coding #bug

  ✨ Use them anywhere in your task:
     devtodo add "Fix login bug @urgent #backend"
     devtodo add "#personal Buy groceries @low"

🔍 FILTERING & SORTING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  devtodo ls --tag work              Show only #work tasks
  devtodo ls --priority urgent       Show urgent tasks only
  devtodo ls --done                  Include completed tasks
  devtodo ls --created               Show when tasks were made
  devtodo ls --sort created          Sort by creation date

📝 PRACTICAL EXAMPLES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  devtodo add "Review pull request @high #code"
  devtodo add "Team meeting tomorrow #work"
  devtodo add "Call dentist @normal #personal"
  devtodo update 2 --priority urgent
  devtodo ls --tag personal --done

💡 PRO TIPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Use quotes for complex tasks: 'Deploy app @urgent'
  • Tasks are saved in .todo.json in current folder
  • Higher priority tasks show up first
  • Numbers in commands match the list numbers
  • Mix and match tags and priorities freely!

Happy task managing! 🎉
"""
    print(help_text)

def main():
    parser = argparse.ArgumentParser(
        description="DevTodo - Project-based todo CLI with priorities and tags",
        add_help=False
    )
    subparsers = parser.add_subparsers(dest="command")

    help_parser = subparsers.add_parser("help", help="Show detailed help")

    ls_parser = subparsers.add_parser("ls", help="List tasks")
    ls_parser.add_argument("--tag", "-t", action="append", help="Filter by tags")
    ls_parser.add_argument("--priority", "-p", choices=PRIORITIES.keys(), help="Filter by priority")
    ls_parser.add_argument("--sort", choices=["priority", "created"], default="priority", help="Sort order")
    ls_parser.add_argument("--done", action="store_true", help="Include completed tasks")
    ls_parser.add_argument("--created", action="store_true", help="Show creation dates")

    list_parser = subparsers.add_parser("list", help="List tasks (alias for ls)")
    list_parser.add_argument("--tag", "-t", action="append", help="Filter by tags")
    list_parser.add_argument("--priority", "-p", choices=PRIORITIES.keys(), help="Filter by priority")
    list_parser.add_argument("--sort", choices=["priority", "created"], default="priority", help="Sort order")
    list_parser.add_argument("--done", action="store_true", help="Include completed tasks")
    list_parser.add_argument("--created", action="store_true", help="Show creation dates")

    add_parser = subparsers.add_parser("add", help="Add a task")
    add_parser.add_argument("desc", nargs="+", help="Task description (use #tag for tags, @priority for priority)")
    add_parser.add_argument("--priority", "-p", choices=PRIORITIES.keys(), help="Set priority")
    add_parser.add_argument("--tag", "-t", action="append", help="Add tags")

    update_parser = subparsers.add_parser("update", help="Update a task")
    update_parser.add_argument("index", type=int, help="Task number")
    update_parser.add_argument("--desc", "-d", help="New description")
    update_parser.add_argument("--priority", "-p", choices=PRIORITIES.keys(), help="New priority")
    update_parser.add_argument("--tag", "-t", action="append", help="New tags (replaces existing)")

    done_parser = subparsers.add_parser("done", help="Mark task as completed")
    done_parser.add_argument("index", type=int, help="Task number")

    undone_parser = subparsers.add_parser("undone", help="Mark task as pending")
    undone_parser.add_argument("index", type=int, help="Task number")

    rm_parser = subparsers.add_parser("rm", help="Remove a task")
    rm_parser.add_argument("index", type=int, help="Task number")

    subparsers.add_parser("clear", help="Clear all completed tasks")
    subparsers.add_parser("stats", help="Show task statistics")

    if len(sys.argv) == 1:
        show_welcome_interface()
        return

    args = parser.parse_args()

    try:
        if args.command == "add":
            add_task(" ".join(args.desc), args.priority, args.tag)
        elif args.command in ["ls", "list"]:
            list_tasks(args.tag, args.priority, args.sort, args.done, args.created)
        elif args.command == "update":
            update_task(args.index, args.desc, args.priority, args.tag)
        elif args.command == "done":
            mark_done(args.index)
        elif args.command == "undone":
            mark_undone(args.index)
        elif args.command == "rm":
            delete_task(args.index)
        elif args.command == "clear":
            clear_done()
        elif args.command == "stats":
            show_stats()
        elif args.command == "help":
            show_help()
        else:
            show_help()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
