def stale_grounded_lessons(lessons, current_fingerprint):
    stale_keys = []

    for key, lesson in lessons.items():
        grounding = lesson.get("grounding")

        if grounding is None:
            continue

        if grounding.get("document_fingerprint") != current_fingerprint:
            stale_keys.append(key)

    return stale_keys

def remove_stale_grounded_lessons(
    lessons,
    current_fingerprint,
    *dependent,
):
    stale_keys = stale_grounded_lessons(
        lessons,
        current_fingerprint,
    )

    for key in stale_keys:
        lessons.pop(key, None)

        for collection in dependent:
            collection.pop(key, None)

    return stale_keys