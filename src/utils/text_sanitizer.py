import re


_WHITESPACE_RE = re.compile(r"\s+")


def sanitize_action_text(text: str, *, max_len: int = 140) -> str:
    if text is None:
        return ""

    if not isinstance(text, str):
        text = str(text)

    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    text = _WHITESPACE_RE.sub(" ", text).strip()

    text = "".join(ch for ch in text if ch.isprintable())
    text = text.replace("<", "").replace(">", "")

    if len(text) > max_len:
        text = text[: max_len - 1].rstrip() + "…"

    return text
