TAG_RETIRED = "Retired"
TAG_MULTI_LEMMA = "multi_lemma"
TAG_FAILED_LEMMA = "Failed to generate lemma"
TAG_UNPROCESSED_SUSPENDED = "Nicht bearbeitetete Karten sind suspendiert"
TAG_USER_SUSPENDED = "Individuelle Karten die ich nicht lernen will sind suspendiert"


def normalize_tag(tag: str) -> str:
    return tag.strip().replace(" ", "_")


def excluded_tags() -> list[str]:
    return [
        normalize_tag(TAG_RETIRED),
        normalize_tag(TAG_MULTI_LEMMA),
        normalize_tag(TAG_FAILED_LEMMA),
        normalize_tag(TAG_UNPROCESSED_SUSPENDED),
        normalize_tag(TAG_USER_SUSPENDED),
    ]
