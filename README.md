# GTD Agents

GTD (Getting Things Done) powered by Gas Town agents. Keep the core mechanics,
automate the clerical overhead that makes people quit.

## Philosophy

GTD works because of its five stages: Capture, Clarify, Organize, Review, Engage.
GTD fails because stages 2-4 are tedious manual labor. Agents handle those.

**You do:** Capture (brain dump) and Engage (execute).
**Agents do:** Clarify, Organize, Review.

## How It Works

### 1. Capture (You)
Dump raw thoughts however you want:
```bash
gtd capture "call dentist about that thing"
gtd capture "maybe learn rust at some point"
gtd capture "buy groceries - milk eggs bread"
gtd capture "the API timeout bug is back"
```

No formatting required. Stream of consciousness is fine.

### 2. Clarify (Agent)
The **Clarify Agent** processes your inbox:
- Is this actionable? → Next action or project
- Not actionable? → Reference, someday/maybe, or trash
- Multi-step? → Breaks into project with next actions
- Has a deadline? → Flags it
- Delegatable? → Marks as waiting-for

### 3. Organize (Agent)
The **Organize Agent** files clarified items:
- Assigns contexts (@home, @computer, @errands, @calls)
- Groups related items into projects
- Sets dependencies (can't do X until Y)
- Detects duplicates and merges

### 4. Review (Agent)
The **Review Agent** runs automatically:
- **Daily**: Surfaces today's next actions by context
- **Weekly**: Full review — stale items, projects without next actions,
  someday/maybe check-in, completed project cleanup
- Generates a digest you can scan in 2 minutes

### 5. Engage (You)
Ask what to do:
```bash
gtd next                  # What should I do right now?
gtd next @errands         # I'm out running errands
gtd next --energy=low     # I'm tired, give me easy wins
gtd next --time=15m       # I have 15 minutes
```

## Architecture

```
gtd CLI (capture + engage)
  ├── inbox/          Raw captures land here
  ├── agents/
  │   ├── clarify/    Processes inbox → actionable items
  │   ├── organize/   Files items into contexts/projects
  │   └── review/     Runs daily/weekly reviews
  ├── store/
  │   ├── actions/    Next actions (by context)
  │   ├── projects/   Multi-step outcomes
  │   ├── waiting/    Delegated items
  │   ├── someday/    Maybe later
  │   └── reference/  Non-actionable info
  └── config.yaml     Contexts, review schedule, preferences
```

## Tech Stack

- **CLI**: Python (Click)
- **Storage**: SQLite (simple, portable, no server)
- **Agents**: Gas Town polecats for processing
- **LLM**: Claude for clarify/organize intelligence
