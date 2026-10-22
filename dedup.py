"""Mark near-duplicate bot records. Standard library only."""

import re

STOPWORDS = {
    "a", "about", "already", "alert", "an", "and", "as", "at", "be", "but",
    "by", "can", "down", "equal", "for", "from", "has", "have", "if", "in",
    "into", "is", "new", "not", "of", "on", "out", "pass", "report", "skip",
    "that", "the", "this", "those", "to", "under", "up", "update", "urgent",
    "via", "when", "will", "with",
    # News filler: says nothing about which issue it is.
    "disclosed", "discovered", "flaw", "newly", "reported", "vulnerability",
}

CVE_ID = re.compile(r"CVE-\d{4}-\d{4,}", re.I)

THRESHOLD = 0.8


def norm(s):
    """Lowercase, strip punctuation, drop stopwords."""
    s = re.sub(r"[^\w\s]", "", s.lower())
    return " ".join(w for w in s.split() if w not in STOPWORDS)


def sim(a, b):
    """Similarity of two titles, from 0.0 to 1.0.

    Titles that name a CVE are compared by CVE ID only: the same ID is a
    duplicate, different IDs never are. Other titles are compared by word
    overlap, so word order does not matter.
    """
    ids_a = {i.upper() for i in CVE_ID.findall(a)}
    ids_b = {i.upper() for i in CVE_ID.findall(b)}
    if ids_a and ids_b:
        return 1.0 if ids_a & ids_b else 0.0
    words_a, words_b = set(norm(a).split()), set(norm(b).split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / min(len(words_a), len(words_b))


def _better(a, b):
    """True if record a should be kept over record b."""
    if a["trust_score"] != b["trust_score"]:
        return a["trust_score"] > b["trust_score"]
    return len(a.get("content", "")) > len(b.get("content", ""))


def _label(record, kept):
    return {**record, "label": "duplicate - similar to: " + kept["title"]}


def dedup(records, threshold=THRESHOLD):
    """Split records into (kept, removed).

    Each record has title, trust_score and content. Records are only compared
    with records of the same date (records without a date share one group).
    Of two similar records, the one with the higher trust_score is kept; on a
    tie, the one with the longer content. Removed records get a label instead
    of being dropped.
    """
    kept, removed = [], []
    for r in records:
        match = None
        for i, k in enumerate(kept):
            if k.get("date") == r.get("date") and sim(r["title"], k["title"]) >= threshold:
                match = i
                break
        if match is None:
            kept.append(r)
        elif _better(r, kept[match]):
            removed.append(_label(kept[match], r))
            kept[match] = r
        else:
            removed.append(_label(r, kept[match]))
    return kept, removed


if __name__ == "__main__":
    records = [
        {"title": "CVE-2026-1001 RCE in OpenSSL", "trust_score": 3, "content": "OpenSSL RCE, CVSS 9.8"},
        {"title": "CVE-2026-1001: OpenSSL RCE flaw", "trust_score": 5, "content": "Critical RCE in OpenSSL, fix in 3.6.2"},
        {"title": "Newly discovered zero-day in Windows Kernel", "trust_score": 4, "content": "Trusted source reports a Windows Kernel zero-day"},
        {"title": "Windows Kernel zero-day disclosed", "trust_score": 2, "content": "Comment on the Windows zero-day news"},
        {"title": "Paper: Detecting malware with machine learning", "trust_score": 5, "content": "ML method for malware detection, F1 score 0.96"},
    ]
    kept, removed = dedup(records)
    print("KEPT:")
    for k in kept:
        print(" -", k["title"], "| trust:", k["trust_score"])
    print("REMOVED (labeled duplicate):")
    for r in removed:
        print(" -", r["title"], "|", r["label"])
