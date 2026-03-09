# GTD Agents — Design

## Core Data Model

### Item (the universal GTD object)
```
id:          unique identifier
raw_text:    original capture text
type:        inbox | action | project | waiting | someday | reference | trash
context:     @home | @computer | @errands | @calls | @office | @anywhere
energy:      low | medium | high
time_est:    minutes (optional)
deadline:    date (optional)
project_id:  parent project (optional)
delegated_to: person (optional, for waiting-for)
status:      active | completed | dropped
created_at:  timestamp
clarified_at: timestamp (null = still in inbox)
next_review:  date
notes:       agent clarification notes
```

### Project (a desired outcome requiring multiple actions)
```
id:          unique identifier
name:        clear outcome statement ("Dentist appointment scheduled")
status:      active | completed | on_hold | dropped
items:       list of action item IDs
next_action: ID of the current next action (always exactly one)
```

## Agent Behaviors

### Clarify Agent
Trigger: New items in inbox (or manual `gtd process`)

For each inbox item:
1. Parse intent from raw text
2. Classify: actionable vs not-actionable
3. If actionable:
   - Single step? → action item
   - Multi-step? → project + first next action
   - Someone else's job? → waiting-for
   - Has a date? → set deadline
4. If not actionable:
   - Useful info? → reference
   - "Maybe someday"? → someday
   - Noise? → trash
5. Suggest context and energy level

Decision: Agent classifies autonomously. You review the daily digest
and can override anything.

### Organize Agent
Trigger: After clarify, or on demand

1. Scan for items that belong to existing projects → link them
2. Detect clusters of related items → suggest new project
3. Check every project has exactly one next action
4. Flag items with no context
5. Merge duplicates

### Review Agent
Trigger: Cron schedule (daily morning, weekly Sunday)

**Daily review:**
- List today's next actions grouped by context
- Flag overdue items
- Show waiting-for items to follow up on
- Quick stats: inbox count, actions count, completed yesterday

**Weekly review:**
- Everything in daily, plus:
- Items with no activity in 2+ weeks → nudge or drop?
- Projects without next actions → stuck
- Someday/maybe check-in: "Still interested in X?"
- Completed projects → archive
- Generate summary digest

## CLI Commands

```bash
# Capture
gtd capture "raw thought"         # Add to inbox
gtd capture -f file.txt           # Bulk capture from file

# Process
gtd inbox                         # Show unprocessed items
gtd process                       # Trigger clarify agent

# Engage
gtd next                          # Smart pick: best action right now
gtd next @context                 # Filter by context
gtd next --energy=low             # Filter by energy
gtd next --time=15m               # Filter by available time
gtd actions                       # All next actions
gtd actions @errands              # By context

# Projects
gtd projects                      # List active projects
gtd project show <id>             # Project details + actions

# Review
gtd review                        # Show daily review
gtd review --weekly               # Full weekly review

# Manage
gtd done <id>                     # Mark complete
gtd drop <id>                     # Mark dropped
gtd defer <id>                    # Move to someday
gtd edit <id>                     # Modify item
gtd waiting <id> "person"         # Mark as waiting-for
```

## Implementation Phases

### Phase 1: Capture + Store
- CLI with `capture`, `inbox`, `actions` commands
- SQLite storage
- Manual clarify (no agent yet)

### Phase 2: Clarify Agent
- LLM-powered inbox processing
- Auto-classify type, context, energy
- Project detection

### Phase 3: Organize Agent
- Project grouping
- Duplicate detection
- Next-action enforcement

### Phase 4: Review Agent
- Daily/weekly review generation
- Stale item detection
- Digest output

### Phase 5: Smart Engage
- Context-aware `gtd next` with LLM ranking
- Time/energy filtering
- Learning from completion patterns
