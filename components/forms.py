"""Defaults shared by editable forms."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: code everything missing.
from datetime import date


def date_value(value, default=None):
    try:
        return date.fromisoformat(value) if value else (default or date.today())
    except (ValueError, TypeError):
        return default or date.today()


def option_index(options, value):
    return options.index(value) if value in options else 0


def number_value(row, key, default):
    return row[key] if row.get(key) is not None else default
