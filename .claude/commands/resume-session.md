---
description: Resume a Claude Code session with an interactive picker showing labels
---

## Your Task

**Display** an interactive menu of recent sessions with their labels, then **resume** the selected session.

This command provides a better alternative to `claude --resume` by showing your custom labels.

## How It Works

1. Parse recent sessions from `~/.claude/history.jsonl`
2. Load labels from `~/.claude/session-labels.json`
3. Display an interactive menu using `fzf` (fuzzy finder)
4. Resume the selected session

## Commands to Execute

### Step 1: Check dependencies

Check if `fzf` is installed (needed for interactive picker):

```bash
if command -v fzf >/dev/null 2>&1; then echo "fzf is installed"; else echo "ERROR: fzf is required but not installed. Install with: sudo apt install fzf"; exit 1; fi
```

### Step 2: Create the picker script

Use the Write tool to create `/tmp/resume-claude-session.sh` with the following content:

```bash
#!/bin/bash

# Create a temporary file for session list
SESSIONS_FILE="/tmp/claude-sessions-$$.txt"

# Get last 20 unique sessions with details
cat ~/.claude/history.jsonl | jq -r '.sessionId' | sort | uniq | tail -20 | tac | while read session_id; do
  # Skip null sessions
  if [ "$session_id" = "null" ]; then
    continue
  fi

  # Get session details
  FIRST_TS=$(cat ~/.claude/history.jsonl | jq -r "select(.sessionId==\"$session_id\") | .timestamp" | head -1)
  LAST_TS=$(cat ~/.claude/history.jsonl | jq -r "select(.sessionId==\"$session_id\") | .timestamp" | tail -1)
  PROJECT=$(cat ~/.claude/history.jsonl | jq -r "select(.sessionId==\"$session_id\") | .project" | head -1)
  FIRST_MSG=$(cat ~/.claude/history.jsonl | jq -r "select(.sessionId==\"$session_id\") | .display" | grep -v "^/StartOfTheDay" | grep -v "^$" | head -1 | cut -c1-40)

  # Get label if exists
  LABEL=""
  if [ -f ~/.claude/session-labels.json ]; then
    LABEL=$(jq -r --arg sid "$session_id" '.[$sid].label // ""' ~/.claude/session-labels.json 2>/dev/null)
  fi

  # Convert timestamp to relative time
  LAST_DATE=$(date -d "@$((LAST_TS/1000))" "+%Y-%m-%d %H:%M" 2>/dev/null || date -r "$((LAST_TS/1000))" "+%Y-%m-%d %H:%M" 2>/dev/null)

  # Use label if available, otherwise first message
  DISPLAY_NAME="$LABEL"
  if [ -z "$DISPLAY_NAME" ]; then
    DISPLAY_NAME="$FIRST_MSG"
  fi

  # Get project basename
  PROJECT_NAME=$(basename "$PROJECT")

  # Format: [Label/Message] · [Project] · [Date] · [SessionID]
  echo "$DISPLAY_NAME · $PROJECT_NAME · $LAST_DATE · $session_id"
done > "$SESSIONS_FILE"

# Check if we have any sessions
if [ ! -s "$SESSIONS_FILE" ]; then
  echo "No sessions found in ~/.claude/history.jsonl"
  rm -f "$SESSIONS_FILE"
  exit 1
fi

# Show picker with fzf
echo "Select a session to resume (Ctrl+C to cancel):"
echo ""

SELECTION=$(cat "$SESSIONS_FILE" | fzf \
  --height=20 \
  --border \
  --header="Recent Claude Code Sessions (with labels)" \
  --preview='echo {}' \
  --preview-window=hidden \
  --prompt="Resume session: " \
  --pointer="→" \
  --color="header:italic:underline,prompt:blue,pointer:green")

# Clean up temp file
rm -f "$SESSIONS_FILE"

# If user cancelled, exit
if [ -z "$SELECTION" ]; then
  echo "Cancelled"
  exit 0
fi

# Extract session ID (last field after final ·)
SESSION_ID=$(echo "$SELECTION" | awk -F' · ' '{print $NF}')

echo ""
echo "Resuming session: $SESSION_ID"
echo "Selection: $SELECTION"
echo ""

# Resume the session
exec claude --resume "$SESSION_ID"
```

### Step 3: Make it executable and run

```bash
chmod +x /tmp/resume-claude-session.sh && /tmp/resume-claude-session.sh
```

## What The User Sees

The picker will display sessions like:

```
Recent Claude Code Sessions (with labels)

→ Testing plugins in the transplant-gcp · transplant-gcp · 2025-11-17 20:20 · bbace15c-c275-4f21-8501-7796ec5bbe92
  Netlify MCP integration work · transplant-gcp · 2025-11-11 21:24 · dbff96f6-6782-4c06-aa71-9db466e2ba0b
  Testing developer-utilities plugin · Code · 2025-11-15 16:31 · fccea55b-62b9-447d-ac21-76c04e32aece
  what's next?... · transplant-gcp · 2025-11-09 00:58 · ed3b556e-85b4-4e23-95a8-b0353ab3359a
```

**Features:**
- ✅ Shows custom labels (if set)
- ✅ Shows first message (if no label)
- ✅ Shows project name
- ✅ Shows last activity date
- ✅ Fuzzy search (type to filter)
- ✅ Arrow keys to select
- ✅ Enter to resume

## Usage

Instead of running `claude --resume`, run:

```
/resume-session
```

This will:
1. Show an interactive picker
2. Let you search/filter by label or project
3. Resume the selected session

## Installing fzf

If fzf is not installed:

**Ubuntu/Debian:**
```bash
sudo apt install fzf
```

**macOS:**
```bash
brew install fzf
```

**Other:**
```bash
git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
~/.fzf/install
```

## Related Commands

- `/list-sessions` - View all sessions (non-interactive)
- `/label-session` - Add labels to sessions
- `claude --resume` - Built-in resume (no labels)

## Notes

- Uses `fzf` for interactive selection
- Labels take priority over first message
- Shows project name and date for context
- Directly resumes the selected session
- Ctrl+C to cancel

## Troubleshooting

**"fzf: command not found"**
- Install fzf using the instructions above

**"No sessions found"**
- Check `~/.claude/history.jsonl` exists
- Ensure you have at least one previous session

**Picker doesn't show labels**
- Labels are optional
- Use `/label-session` to add labels to sessions
- Sessions without labels show their first message instead
