import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dedup import dedup, norm  # noqa: E402


def rec(title, trust, content="x", date=None):
    r = {"title": title, "trust_score": trust, "content": content}
    if date:
        r["date"] = date
    return r


class DedupTest(unittest.TestCase):
    def test_norm_drops_punctuation_and_stopwords(self):
        self.assertEqual(norm("CVE-2026-1001: RCE flaw in the OpenSSL!"), "cve20261001 rce openssl")

    def test_keeps_higher_trust_even_when_it_comes_second(self):
        kept, removed = dedup([rec("CVE-2026-1001 RCE in OpenSSL", 3), rec("CVE-2026-1001: OpenSSL RCE", 5)])
        self.assertEqual([k["trust_score"] for k in kept], [5])
        self.assertEqual(removed[0]["trust_score"], 3)
        self.assertTrue(removed[0]["label"].startswith("duplicate - similar to: "))

    def test_tie_keeps_longer_content(self):
        kept, removed = dedup([rec("Windows Kernel zero-day", 4, "short"), rec("Windows Kernel zero-day!", 4, "much longer text")])
        self.assertEqual(kept[0]["content"], "much longer text")
        self.assertEqual(removed[0]["content"], "short")

    def test_different_records_are_both_kept(self):
        kept, removed = dedup([rec("CVE-2026-1001 RCE in OpenSSL", 5), rec("Paper: malware detection with ML", 5)])
        self.assertEqual(len(kept), 2)
        self.assertEqual(removed, [])

    def test_word_order_does_not_matter(self):
        kept, removed = dedup([rec("Newly discovered zero-day in Windows Kernel", 4), rec("Windows Kernel zero-day disclosed", 2)])
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(removed), 1)

    def test_different_cve_ids_are_never_duplicates(self):
        kept, removed = dedup([rec("CVE-2026-1001 RCE in OpenSSL", 5), rec("CVE-2026-1002 RCE in OpenSSL", 5)])
        self.assertEqual(len(kept), 2)
        self.assertEqual(removed, [])

    def test_only_same_date_is_compared(self):
        kept, removed = dedup([rec("CVE-2026-1001 RCE in OpenSSL", 5, date="2026-10-21"), rec("CVE-2026-1001 RCE in OpenSSL", 3, date="2026-10-22")])
        self.assertEqual(len(kept), 2)
        self.assertEqual(removed, [])


if __name__ == "__main__":
    unittest.main()
