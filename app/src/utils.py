import re
import unicodedata


def normalize_name(name: str) -> str:
    if not name:
        return ""
    nfkd = unicodedata.normalize("NFKD", name)
    only_ascii = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", only_ascii).strip().lower()
