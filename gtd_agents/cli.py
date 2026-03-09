"""GTD Agents CLI — capture, clarify, organize, review, engage."""

import click
from datetime import datetime

from .models import (
    get_db, Item, Project, add_item, get_items, get_item, update_item,
    add_project, get_projects, get_project,
)

CONTEXTS = ["@home", "@computer", "@errands", "@calls", "@office", "@anywhere"]
ENERGY_LEVELS = ["low", "medium", "high"]
ITEM_TYPES = ["inbox", "action", "project", "waiting", "someday", "reference", "trash"]


@click.group()
def cli():
    """GTD powered by agents. Capture thoughts, let agents clarify and organize."""
    pass


# ── Capture ──────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("text", nargs=-1, required=True)
def capture(text):
    """Capture a raw thought into the inbox."""
    raw = " ".join(text)
    conn = get_db()
    item = add_item(conn, Item(raw_text=raw))
    click.echo(f"Captured: {item.id} — {raw}")
    conn.close()


# ── Inbox ────────────────────────────────────────────────────────────────────

@cli.command()
def inbox():
    """Show unprocessed inbox items."""
    conn = get_db()
    items = get_items(conn, type="inbox")
    conn.close()

    if not items:
        click.echo("Inbox is empty. Nice!")
        return

    click.echo(f"Inbox: {len(items)} item(s)\n")
    for it in items:
        age = _age(it["created_at"])
        click.echo(f"  {it['id']}  {it['raw_text']}  ({age})")


# ── Actions ──────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("context", required=False)
def actions(context):
    """Show next actions, optionally filtered by @context."""
    if context and not context.startswith("@"):
        context = f"@{context}"

    conn = get_db()
    items = get_items(conn, type="action", context=context)
    conn.close()

    if not items:
        click.echo("No actions." + (f" (filter: {context})" if context else ""))
        return

    click.echo(f"Actions: {len(items)}\n")
    for it in items:
        ctx = f" {it['context']}" if it['context'] else ""
        energy = f" [{it['energy']}]" if it['energy'] else ""
        time = f" ~{it['time_est']}m" if it['time_est'] else ""
        deadline = f" ⚠ {it['deadline']}" if it['deadline'] else ""
        click.echo(f"  {it['id']}{ctx}{energy}{time}{deadline}  {it['raw_text']}")


# ── Next ─────────────────────────────────────────────────────────────────────

@cli.command("next")
@click.argument("context", required=False)
@click.option("--energy", type=click.Choice(ENERGY_LEVELS), help="Filter by energy level")
@click.option("--time", "time_avail", type=int, help="Available minutes")
def next_action(context, energy, time_avail):
    """Pick the best next action based on context/energy/time."""
    if context and not context.startswith("@"):
        context = f"@{context}"

    conn = get_db()
    items = get_items(conn, type="action", context=context)
    conn.close()

    # Filter by energy and time
    if energy:
        items = [i for i in items if i["energy"] == energy]
    if time_avail:
        items = [i for i in items if i["time_est"] is None or i["time_est"] <= time_avail]

    if not items:
        click.echo("Nothing matches. Try broader filters or check your inbox.")
        return

    # Prioritize: deadline items first, then by creation date
    def sort_key(it):
        has_deadline = 0 if it["deadline"] else 1
        return (has_deadline, it["created_at"])

    items.sort(key=sort_key)
    it = items[0]

    ctx = f" {it['context']}" if it['context'] else ""
    click.echo(f"→ {it['id']}{ctx}  {it['raw_text']}")
    if it["deadline"]:
        click.echo(f"  ⚠ Deadline: {it['deadline']}")


# ── Clarify (manual for Phase 1) ────────────────────────────────────────────

@cli.command()
@click.argument("item_id")
@click.option("--type", "item_type", type=click.Choice(ITEM_TYPES[1:]), required=True,
              help="What type of item is this?")
@click.option("--context", type=click.Choice(CONTEXTS), help="Context tag")
@click.option("--energy", type=click.Choice(ENERGY_LEVELS), help="Energy level needed")
@click.option("--time", "time_est", type=int, help="Estimated minutes")
@click.option("--deadline", help="Deadline (YYYY-MM-DD)")
@click.option("--delegate", help="Person to delegate to (creates waiting-for)")
@click.option("--project", "project_id", help="Assign to project ID")
def clarify(item_id, item_type, context, energy, time_est, deadline, delegate, project_id):
    """Manually clarify an inbox item (agent-powered in Phase 2)."""
    conn = get_db()
    item = get_item(conn, item_id)

    if not item:
        click.echo(f"Item {item_id} not found.")
        conn.close()
        return

    updates = {
        "type": item_type,
        "clarified_at": datetime.utcnow().isoformat(),
    }
    if context:
        updates["context"] = context
    if energy:
        updates["energy"] = energy
    if time_est:
        updates["time_est"] = time_est
    if deadline:
        updates["deadline"] = deadline
    if delegate:
        updates["delegated_to"] = delegate
        updates["type"] = "waiting"
    if project_id:
        updates["project_id"] = project_id

    update_item(conn, item_id, **updates)
    conn.close()
    click.echo(f"Clarified {item_id} → {updates['type']}")


# ── Done / Drop / Defer ─────────────────────────────────────────────────────

@cli.command()
@click.argument("item_id")
def done(item_id):
    """Mark an item as completed."""
    conn = get_db()
    update_item(conn, item_id, status="completed")
    conn.close()
    click.echo(f"Completed: {item_id}")


@cli.command()
@click.argument("item_id")
def drop(item_id):
    """Drop an item (won't do it)."""
    conn = get_db()
    update_item(conn, item_id, status="dropped")
    conn.close()
    click.echo(f"Dropped: {item_id}")


@cli.command()
@click.argument("item_id")
def defer(item_id):
    """Move an item to someday/maybe."""
    conn = get_db()
    update_item(conn, item_id, type="someday")
    conn.close()
    click.echo(f"Deferred: {item_id}")


# ── Projects ─────────────────────────────────────────────────────────────────

@cli.group()
def project():
    """Manage projects (multi-step outcomes)."""
    pass


@project.command("list")
def project_list():
    """List active projects."""
    conn = get_db()
    projects = get_projects(conn)
    conn.close()

    if not projects:
        click.echo("No active projects.")
        return

    for p in projects:
        click.echo(f"  {p['id']}  {p['name']}  [{p['status']}]")


@project.command("show")
@click.argument("project_id")
def project_show(project_id):
    """Show project details and its actions."""
    conn = get_db()
    proj = get_project(conn, project_id)
    if not proj:
        click.echo(f"Project {project_id} not found.")
        conn.close()
        return

    click.echo(f"{proj['id']}  {proj['name']}  [{proj['status']}]")

    items = get_items(conn, type="action")
    project_items = [i for i in items if i["project_id"] == project_id]
    conn.close()

    if project_items:
        click.echo(f"\nActions ({len(project_items)}):")
        for it in project_items:
            marker = "→" if it["id"] == proj["next_action_id"] else " "
            click.echo(f"  {marker} {it['id']}  {it['raw_text']}")
    else:
        click.echo("\n  No actions yet.")


@project.command("create")
@click.argument("name", nargs=-1, required=True)
def project_create(name):
    """Create a new project."""
    proj_name = " ".join(name)
    conn = get_db()
    proj = add_project(conn, Project(name=proj_name))
    conn.close()
    click.echo(f"Project created: {proj.id} — {proj_name}")


# ── Stats ────────────────────────────────────────────────────────────────────

@cli.command()
def stats():
    """Show GTD system statistics."""
    conn = get_db()

    counts = {}
    for row in conn.execute(
        "SELECT type, COUNT(*) as cnt FROM items WHERE status = 'active' GROUP BY type"
    ).fetchall():
        counts[row["type"]] = row["cnt"]

    completed = conn.execute(
        "SELECT COUNT(*) as cnt FROM items WHERE status = 'completed'"
    ).fetchone()["cnt"]

    projects = conn.execute(
        "SELECT COUNT(*) as cnt FROM projects WHERE status = 'active'"
    ).fetchone()["cnt"]

    conn.close()

    click.echo("GTD Stats")
    click.echo(f"  Inbox:      {counts.get('inbox', 0)}")
    click.echo(f"  Actions:    {counts.get('action', 0)}")
    click.echo(f"  Waiting:    {counts.get('waiting', 0)}")
    click.echo(f"  Someday:    {counts.get('someday', 0)}")
    click.echo(f"  Reference:  {counts.get('reference', 0)}")
    click.echo(f"  Projects:   {projects}")
    click.echo(f"  Completed:  {completed}")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _age(iso_str: str) -> str:
    created = datetime.fromisoformat(iso_str)
    delta = datetime.utcnow() - created
    if delta.days > 0:
        return f"{delta.days}d ago"
    hours = delta.seconds // 3600
    if hours > 0:
        return f"{hours}h ago"
    return "just now"
