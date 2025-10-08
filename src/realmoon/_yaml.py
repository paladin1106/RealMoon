"""Lightweight YAML loader used when PyYAML is unavailable."""

from __future__ import annotations

from typing import Any, List, Tuple

__all__ = ["safe_load"]


def safe_load(text: str) -> Any:
    lines = _preprocess(text)
    if not lines:
        return {}
    value, index = _parse_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise ValueError("Failed to parse YAML: leftover content")
    return value


def _preprocess(text: str) -> List[Tuple[int, str]]:
    processed: List[Tuple[int, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2 != 0:
            raise ValueError("Indentation must be multiples of two spaces")
        processed.append((indent, line.strip()))
    return processed


def _parse_block(lines: List[Tuple[int, str]], index: int, indent: int):
    if lines[index][1].startswith("- "):
        return _parse_list(lines, index, indent)
    return _parse_mapping(lines, index, indent)


def _parse_list(lines: List[Tuple[int, str]], index: int, indent: int):
    items = []
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError("Invalid indentation in list")
        if not content.startswith("- "):
            break
        item_content = content[2:].strip()
        index += 1
        if item_content:
            items.append(_coerce(item_content))
        else:
            if index >= len(lines):
                raise ValueError("List item expects nested value")
            nested_indent = lines[index][0]
            if nested_indent <= indent:
                raise ValueError("Invalid indentation for nested list item")
            value, index = _parse_block(lines, index, nested_indent)
            items.append(value)
    return items, index


def _parse_mapping(lines: List[Tuple[int, str]], index: int, indent: int):
    mapping = {}
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError("Invalid indentation in mapping")
        if ":" not in content:
            raise ValueError("Expected ':' in mapping entry")
        key, value_part = content.split(":", 1)
        key = key.strip()
        value_part = value_part.strip()
        index += 1
        if value_part:
            mapping[key] = _coerce(value_part)
        else:
            if index >= len(lines):
                mapping[key] = None
                continue
            nested_indent = lines[index][0]
            if nested_indent <= indent:
                mapping[key] = None
                continue
            value, index = _parse_block(lines, index, nested_indent)
            mapping[key] = value
    return mapping, index


def _coerce(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"null", "none"}:
        return None
    if lowered in {"true", "yes"}:
        return True
    if lowered in {"false", "no"}:
        return False
    try:
        if value.startswith("0") and value not in {"0", "0.0"} and not value.startswith("0."):
            raise ValueError
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value
