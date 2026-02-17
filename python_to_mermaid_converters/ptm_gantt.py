"""
Gantt chart renderer for converting Python GanttChart objects to Mermaid text.
"""

from typing import List

from mermaid import GanttChart, GanttTask, DateRange

from python_to_mermaid_converters.ptm_common import join_lines, render_config


def render_gantt_task(task: GanttTask) -> str:
    """
    Render a single GanttTask as a Mermaid task line.

    Args:
        task: The GanttTask to render

    Returns:
        Mermaid syntax string for the task (without leading whitespace)
    """
    # Build the task line: TaskName :status1, status2, taskID, start, duration
    parts: List[str] = []

    # Status(es) first (after colon)
    # Use statuses list if available, otherwise fall back to single status
    if task.statuses:
        status_str = ", ".join(task.statuses)
        parts.append(f":{status_str}")
    elif task.status:
        parts.append(f":{task.status.value}")
    else:
        parts.append(":")

    # Task ID (optional)
    if task.task_id:
        parts.append(task.task_id)

    # Start date/duration
    # If start is DateRange, add it (and duration if present)
    if isinstance(task.start, DateRange):
        parts.append(str(task.start))
        if task.duration:
            parts.append(task.duration)
    # If we have a duration, add start (if non-empty) and duration
    elif task.duration:
        if task.start:  # Add start only if non-empty
            parts.append(str(task.start))
        parts.append(task.duration)
    # Otherwise just add start if it's non-empty
    elif task.start:
        parts.append(str(task.start))

    # Join parts, filtering out empty parts (like lone ":")
    filtered_parts = [p for p in parts if p != ":"]

    # If we have no status, the first part should start with ":"
    if not task.statuses and not task.status and filtered_parts:
        return f"{task.name} : {', '.join(filtered_parts)}"
    elif filtered_parts:
        return f"{task.name} {', '.join(filtered_parts)}"
    else:
        return f"{task.name} :"


def render_gantt(chart: GanttChart) -> List[str]:
    """
    Render a GanttChart object as a list of content lines.

    Frontmatter and comments are NOT included — those are preserved
    from the raw input by python_to_mermaid.py.

    Args:
        chart: The GanttChart to render

    Returns:
        List of content lines
    """
    lines: List[str] = []

    # Add directive if present
    if chart.directive:
        lines.append(str(chart.directive))

    # Add diagram type declaration
    lines.append(chart.diagram_type.value)

    # Add title
    if chart.title:
        lines.append(f"    title {chart.title}")

    # Add date format
    if chart.date_format:
        lines.append(f"    dateFormat {chart.date_format}")

    # Add axis format if present
    if chart.axis_format:
        lines.append(f"    axisFormat {chart.axis_format}")

    # Add exclusions if present
    if chart.excludes:
        lines.append(f"    excludes {chart.excludes}")

    # Add weekend override if present
    if chart.weekend:
        lines.append(f"    weekend {chart.weekend}")

    # Add sectionless tasks
    for task in chart.tasks:
        lines.append(f"    {render_gantt_task(task)}")

    # Add sections
    for section in chart.sections:
        lines.append(f"    section {section.name}")
        for item in section.items:
            if isinstance(item, GanttTask):
                lines.append(f"        {render_gantt_task(item)}")

    return lines
