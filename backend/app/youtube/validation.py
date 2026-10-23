from src.preprocessing.text import preprocess


def supported_comments(comments):
    """Do not truncate evidence or let one unsupported comment abort a scan."""
    accepted = []
    for comment in comments:
        text = comment.get('text')
        if isinstance(text, str) and text.strip() and len(text) <= 8000 and preprocess(text):
            accepted.append(comment)
    return accepted, len(comments) - len(accepted)
