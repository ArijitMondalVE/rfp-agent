def calculate_confidence(item):

    confidence = 0.5

    text = str(item).lower()

    if len(text) > 20:
        confidence += 0.1

    if "page" in text:
        confidence += 0.1

    if "date" in text:
        confidence += 0.1

    if "%" in text:
        confidence += 0.1

    return round(min(confidence, 0.99), 2)

def add_confidence_scores(results):

    scored = []

    for item in results:

        scored.append({
            "value": item,
            "confidence": calculate_confidence(item)
        })

    return scored