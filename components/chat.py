"""Presentation helpers for the live chat inbox and escaped message bubbles."""
# AI-generated: OpenAI Codex, 19.11.2026. Prompt: make conversations async and organize chats like WhatsApp.
from datetime import datetime, timezone
from html import escape
from zoneinfo import ZoneInfo

CHAT_TIMEZONE = ZoneInfo("Europe/Zurich")

CHAT_STYLES = """
<style>
.wg-chat-header {display:flex;align-items:center;gap:14px;padding:8px 0 18px}
.wg-chat-avatar {display:grid;place-items:center;background:#dceee6;color:#185943;
 width:48px;height:48px;border-radius:50%;font-weight:700;flex-shrink:0}
.wg-chat-title {font-size:1.15rem;font-weight:650;overflow-wrap:anywhere}
.wg-chat-meta {font-size:.8rem;color:#64776f;margin-top:3px}
.wg-chat-history {padding:12px;background:#edf3ef;border-radius:12px;min-height:390px}
.wg-chat-row {display:flex;margin:8px 0;justify-content:flex-start}
.wg-chat-row.own {justify-content:flex-end}
.wg-chat-bubble {max-width:85%;padding:10px 13px;background:#fff;color:#1f3028;
 border-radius:3px 14px 14px 14px;box-shadow:0 1px 2px #18392915;overflow-wrap:anywhere}
.own .wg-chat-bubble {background:#d9f4d0;border-radius:14px 3px 14px 14px}
.wg-chat-sender {font-size:.76rem;font-weight:650;color:#256b53;margin-bottom:4px}
.wg-chat-text {white-space:pre-wrap;line-height:1.5}
.wg-chat-time {font-size:.68rem;text-align:right;color:#62746b;margin-top:4px}
.wg-chat-date {text-align:center;margin:16px 0;font-size:.72rem;color:#53695c}
.wg-chat-date span {background:#fff9;padding:5px 12px;border-radius:8px}
.wg-chat-empty {text-align:center;color:#64776f;padding:110px 12px}
@media (max-width:640px) {.wg-chat-bubble {max-width:94%}}
</style>
"""


def local_chat_datetime(value: str) -> datetime:
    """SQLite timestamps are UTC; display dates and times in St. Gallen time."""
    timestamp = datetime.fromisoformat(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(CHAT_TIMEZONE)


def conversation_title(conversation: dict, user_id: int) -> str:
    return (conversation["wg_title"] if conversation["seeker_id"] == user_id else conversation["seeker_name"]) or "Conversation"


def conversation_header_html(title: str, subtitle: str) -> str:
    initials = "".join(word[0] for word in title.split()[:2]).upper() or "WG"
    return (
        f'<div class="wg-chat-header"><div class="wg-chat-avatar">{escape(initials)}</div>'
        f'<div><div class="wg-chat-title">{escape(title)}</div>'
        f'<div class="wg-chat-meta">{escape(subtitle)}</div></div></div>'
    )


def message_history_html(messages: list[dict], user_id: int) -> str:
    parts = ['<div class="wg-chat-history" role="log" aria-label="Conversation messages">']
    if not messages:
        parts.append('<div class="wg-chat-empty">Your conversation starts here.<br>Say hello and arrange a viewing.</div>')
    previous_date = None
    today = datetime.now(CHAT_TIMEZONE).date()
    for message in messages:
        timestamp = local_chat_datetime(message["created_at"])
        if timestamp.date() != previous_date:
            label = "Today" if timestamp.date() == today else timestamp.strftime("%d %b %Y")
            parts.append(f'<div class="wg-chat-date"><span>{label}</span></div>')
            previous_date = timestamp.date()
        own = message["sender_id"] == user_id
        sender = "You" if own else message["sender_name"] or "Flatmate"
        parts.append(
            f'<div class="wg-chat-row{" own" if own else ""}"><div class="wg-chat-bubble">'
            f'<div class="wg-chat-sender">{escape(sender)}</div>'
            f'<div class="wg-chat-text">{escape(message["text"])}</div>'
            f'<div class="wg-chat-time">{timestamp:%H:%M}</div></div></div>'
        )
    parts.append("</div>")
    return "".join(parts)
