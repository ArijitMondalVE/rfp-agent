import re


def calculate_confidence(item):

    score = 0.50

    text = str(item).lower()

    # Long detailed extraction
    if len(text) > 50:
        score += 0.10

    # Contains page citation
    if re.search(r"page\s+\d+", text):
        score += 0.20

    # Contains date
    if re.search(
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\b",
        text,
    ):
        score += 0.10

    # Numeric value
    if re.search(r"\d", text):
        score += 0.05

    # Procurement keywords
    keywords = [
        "shall",
        "must",
        "required",
        "mandatory",
        "insurance",
        "bond",
        "license",
        "deadline",
        "proposal",
        "submission",
    ]

    matches = sum(
        1
        for keyword in keywords
        if keyword in text
    )

    score += min(matches * 0.03, 0.15)

    return round(min(score, 0.99), 2)


def add_confidence_scores(results):

    scored = []

    for item in results:

        scored.append(
            {
                "value": item,
                "confidence": calculate_confidence(item),
            }
        )

    return scored