"""
Gantt chart parser for converting Mermaid gantt text to Python objects.
"""

from typing import Optional, Union

from mermaid import GanttChart, GanttSection, GanttTask, DateRange, TaskStatus
from mermaid.base import LineEnding

from mermaid_to_python_converters.mtp_common import (
    try_parse_directive,
    try_parse_section,
    is_declaration,
    dayjs_to_strptime,
    is_date,
    is_duration,
    is_task_ref,
)


_GANTT_STATUS_KEYWORDS = {'done', 'active', 'crit', 'milestone', 'vert'}


def _extract_gantt_task_statuses(parts: list) -> tuple:
    """
    First pass: extract status keywords from front of parts list.

    Args:
        parts: List of comma-separated task parts (after the colon)

    Returns:
        Tuple of (statuses list, index of first non-status part).
        If all parts are statuses, index equals len(parts).
    """
    statuses = []
    first_non_status = len(parts)
    for i, part in enumerate(parts):
        if not part:
            continue
        if part.lower() in _GANTT_STATUS_KEYWORDS:
            statuses.append(part.lower())
        else:
            first_non_status = i
            break
    return statuses, first_non_status


def _classify_gantt_task_part(
    part: str, task_id: Optional[str], start_date: Optional[str],
    end_date: Optional[str], duration: Optional[str], index: int,
    strptime_format: Optional[str] = None
) -> dict:
    """
    Classify a single comma-separated part as date/duration/task-ref/task-id.

    Args:
        part: The part string to classify
        task_id: Current task_id (or None)
        start_date: Current start_date (or None)
        end_date: Current end_date (or None)
        duration: Current duration (or None)
        index: Position index in the parts list
        strptime_format: Python strptime format for date matching

    Returns:
        Dict with updated values for task_id, start_date, end_date, duration.
    """
    result = {
        'task_id': task_id,
        'start_date': start_date,
        'end_date': end_date,
        'duration': duration,
    }

    if not part:
        return result

    part_lower = part.lower()

    # Skip if it's a status keyword (already extracted)
    if part_lower in _GANTT_STATUS_KEYWORDS:
        return result

    # Duration pattern (e.g., 3d, 24h, 1w)
    if is_duration(part):
        result['duration'] = part
        return result

    # Task reference (after/until)
    if is_task_ref(part):
        if part_lower.startswith('after '):
            result['start_date'] = part_lower
        else:
            result['end_date'] = part_lower
        return result

    # Date/time value (checked against the diagram's dateFormat)
    if is_date(part, strptime_format):
        if result['start_date'] is None:
            result['start_date'] = part
        else:
            result['end_date'] = part
        return result

    # If no task_id yet and early in the list, treat as task ID
    if result['task_id'] is None and index < 4:
        result['task_id'] = part
        return result

    # Unrecognized — treat as date/time value as a last resort
    if result['start_date'] is None:
        result['start_date'] = part
    else:
        result['end_date'] = part

    return result


def _resolve_gantt_start(
    start_date: Optional[str], end_date: Optional[str], duration: Optional[str]
) -> Union[str, DateRange]:
    """
    Determine the start value for a GanttTask from parsed components.

    Returns:
        A string, DateRange, or empty string.
    """
    if (end_date is not None and
            start_date is not None and
            not start_date.startswith('after ')):
        return DateRange(start=start_date, end=end_date)

    if end_date is not None and end_date.startswith('until '):
        return end_date

    if duration is not None and start_date is None:
        return ""

    if start_date is None:
        return ""

    return start_date


def _parse_gantt_task_line(line: str, strptime_format: Optional[str] = None) -> Optional[GanttTask]:
    """
    Parse a full Gantt task line (must contain a colon).

    Args:
        line: A line like 'Task Name :done, des1, 2014-01-06, 2014-01-08'
        strptime_format: Python strptime format for date matching

    Returns:
        A GanttTask, or None if the line isn't a valid task.
    """
    if ':' not in line:
        return None

    parts = line.split(':', 1)
    if len(parts) != 2:
        return None

    task_name = parts[0].strip()
    rest = parts[1].strip()
    task_parts = [p.strip() for p in rest.split(',')]

    # First pass: extract statuses
    statuses, start_index = _extract_gantt_task_statuses(task_parts)

    # Second pass: classify remaining parts
    task_id = None
    start_date = None
    end_date = None
    duration = None

    for i in range(start_index, len(task_parts)):
        result = _classify_gantt_task_part(
            task_parts[i], task_id, start_date, end_date, duration, i,
            strptime_format
        )
        task_id = result['task_id']
        start_date = result['start_date']
        end_date = result['end_date']
        duration = result['duration']

    # Resolve start value
    start_value = _resolve_gantt_start(start_date, end_date, duration)

    return GanttTask(
        name=task_name,
        start=start_value,
        duration=duration,
        statuses=statuses,
        task_id=task_id,
    )


def parse_gantt(text: str, line_ending: LineEnding) -> GanttChart:
    """Parse a Gantt chart using composable sub-functions."""
    diagram = GanttChart(line_ending=line_ending)
    current_section = None
    strptime_format = None

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        # Skip comments (preserved from raw input by python_to_mermaid.py)
        if line.startswith("%%"):
            continue

        if is_declaration(line, "gantt"):
            continue

        title = try_parse_directive(line, "title")
        if title is not None:
            diagram.title = title
            continue

        date_format = try_parse_directive(line, "dateformat")
        if date_format is not None:
            diagram.date_format = date_format
            strptime_format = dayjs_to_strptime(date_format)
            continue

        axis_format = try_parse_directive(line, "axisformat")
        if axis_format is not None:
            diagram.axis_format = axis_format
            continue

        excludes = try_parse_directive(line, "excludes")
        if excludes is not None:
            diagram.set_excludes(excludes)
            continue

        weekend = try_parse_directive(line, "weekend")
        if weekend is not None:
            diagram.weekend = weekend
            continue

        section_name = try_parse_section(line)
        if section_name is not None:
            current_section = GanttSection(name=section_name)
            diagram.add_section(current_section)
            continue

        task = _parse_gantt_task_line(line, strptime_format)
        if task:
            if current_section:
                current_section.add_task(task)
            else:
                diagram.add_task(task)

    return diagram
