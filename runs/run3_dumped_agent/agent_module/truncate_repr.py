

def truncate_repr(value, limit: int = 300) -> str:
    """
    Return repr(value), cut to at most `limit` characters so that large objects
    (datasets, long lists, big strings) do not flood the environment summary
    that is sent to the LLM on every evolve step.
    """
    try:
        text = repr(value)
    except Exception as e:
        text = f"<unrepresentable {type(value).__name__}: {e}>"
    if len(text) > limit:
        size = ""
        try:
            size = f", len={len(value)}"
        except Exception:
            pass
        text = f"{text[:limit]}... <truncated: {type(value).__name__}{size}, {len(text)} chars total>"
    return text
