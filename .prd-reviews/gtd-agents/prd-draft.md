# PRD: GTD Agents — Getting Things Done with AI

## Problem Statement

GTD (Getting Things Done) is a proven productivity methodology, but most people
abandon it because stages 2-4 (Clarify, Organize, Review) are tedious manual
bookkeeping. The methodology works — the maintenance doesn't.

**For:** Anyone who wants GTD's benefits without the clerical overhead.

**Why now:** LLMs can now reliably classify, categorize, and reason about
unstructured text — exactly the skills needed for GTD's middle stages.

## Goals

1. **Zero-friction capture** — brain dump raw thoughts, no formatting required
2. **Automated clarification** — agent classifies each capture: actionable vs not,
   single vs multi-step, context, energy level, time estimate
3. **Automated organization** — agent groups into projects, detects duplicates,
   assigns contexts, enforces "every project has a next action"
4. **Automated review** — daily and weekly reviews run without human effort,
   surfacing stale items, stuck projects, and forgotten commitments
5. **Smart engagement** — suggest the right next action based on current context,
   energy level, and available time
6. **Human retains decisions** — agents suggest, humans approve/override. The
   human stays in the loop for what matters: deciding what to do and doing it

## Non-Goals

- Not a calendar or scheduling tool (no time-blocking, no appointments)
- Not a team/collaboration tool (single-user focus)
- Not a habit tracker or recurring task manager (focus on one-off GTD items)
- Not replacing the "Engage" stage — the human still picks and executes
- No mobile app or web UI in v1 (CLI only)
- No cloud sync in v1 (local SQLite)

## User Stories / Scenarios

### Brain Dump (Capture)
> "I just remembered 5 things I need to do while in the shower. I want to
> dump them all in 30 seconds and trust the system to sort them out."

```bash
gtd capture "call dentist about that filling"
gtd capture "maybe learn rust at some point"
gtd capture "buy groceries - milk eggs bread"
gtd capture "the API timeout bug is back again"
gtd capture "research vacation spots for august"
```

### Morning Start (Engage)
> "It's Monday morning, I'm at my computer with coffee. What should I do first?"

```bash
gtd next @computer --energy=high
# → "Fix the API timeout bug" (deadline approaching, high-energy match)
```

### Errands Mode
> "I'm heading out to run errands. What can I knock out while I'm out?"

```bash
gtd next @errands
# → "Buy groceries - milk eggs bread"
# → "Call dentist about that filling" (can do from car)
```

### Weekly Review (Agent-Driven)
> "Sunday evening. The agent runs the weekly review and shows me a digest."

```bash
gtd review --weekly
# Agent output:
# 📊 Weekly Review
# ✅ Completed: 12 items
# 📥 Inbox: 3 unprocessed (auto-clarifying...)
# ⚠️ Stale: "research vacation spots" — 3 weeks, no action. Keep or drop?
# 🔴 Stuck project: "Home renovation" — no next action defined
# 💤 Someday check-in: "learn rust" — still interested? (y/n/defer)
```

### Delegation Tracking
> "I asked Bob to send me the report. I need to follow up if he doesn't."

```bash
gtd capture "waiting for Bob to send Q3 report"
# Agent auto-classifies as waiting-for, sets follow-up reminder
```

## Constraints

- **CLI-only** for v1 (Python + Click)
- **SQLite** for storage (no server dependency, portable)
- **LLM dependency** for clarify/organize/review agents (Claude API)
- **Single user** — no auth, no multi-tenancy
- **Offline-first** — captures work without network; agent processing needs API
- **Cost-aware** — batch agent operations to minimize API calls

## Open Questions

1. **Agent autonomy level** — should agents auto-process inbox continuously,
   or only when user runs `gtd process`? Or both (configurable)?
2. **Confidence thresholds** — when should the agent ask for human confirmation
   vs. auto-classifying? (e.g., "90% sure this is @errands" → auto-assign)
3. **Review frequency** — daily review at what time? Weekly review on what day?
   Cron-triggered or on-demand?
4. **Project detection** — how aggressively should the agent group items into
   projects? False positives (over-grouping) vs. false negatives (missed links)?
5. **LLM model choice** — use Claude for all agent steps, or smaller/cheaper
   models for simpler classification tasks?
6. **Data portability** — should we support export to standard formats
   (Todoist, Things, OmniFocus) for users who want to migrate?

## Rough Approach

### Architecture
```
gtd CLI (Python/Click)
├── capture.py      — Raw input → inbox table
├── clarify.py      — LLM classifies inbox items
├── organize.py     — LLM groups, deduplicates, enforces structure
├── review.py       — LLM generates daily/weekly digests
├── engage.py       — Smart next-action picker
├── models.py       — SQLite models (Item, Project)
└── config.py       — User preferences, contexts, review schedule
```

### Agent Implementation
Each agent stage is a Python module that:
1. Queries SQLite for items in its scope
2. Builds a prompt with the items + context
3. Calls Claude API for classification/analysis
4. Writes results back to SQLite
5. Logs what it did (transparency)

### Key Design Decisions
- **Batch processing** — clarify processes all inbox items in one API call
  (cheaper than per-item calls, and LLM can see patterns across items)
- **Transparency** — every agent action logged: "Classified 'call dentist'
  as action/@calls/low-energy/5min — reason: phone call, simple scheduling"
- **Override-friendly** — any agent decision can be manually overridden:
  `gtd reclassify <id> --context=@home`
- **Progressive trust** — start with more human confirmation, reduce as
  the system proves reliable (configurable confidence thresholds)
