# Grok Security Bots

A set of Grok bots that track new CVEs, zero-days and security papers, so a team knows what to patch first. Duplicates are removed automatically.

## Structure

- `dedup.py` - Python dedup script (80% threshold, standard library only)
- `prompts.md` - Full prompts for the three main bots and the dedup bot
- `tests/` - Unit tests for `dedup.py`

## Three main bots

1. **CVE Bot**: Finds CVEs from the last 24 hours with CVSS 7+. A 3-line summary with patch status and the fix. Exploited or public-PoC issues come first, because they need patching first.
2. **Zero-day Bot**: Scans 48 hours of posts on X for zero-days in named products, with any mitigation. Prioritizes sources over 500 followers with a track record. Rates trust 1-5.
3. **Paper Bot**: Take a link or PDF, summarize in English up to 300 words, keep technical terms as-is.

## Dedup bot

- Group same-day records from all three bots.
- Titles with a CVE ID: the same ID is a duplicate, different IDs never are.
- Other titles: normalize (lowercase, no punctuation, no stopwords), then compare word overlap. Word order does not matter.
- 80% threshold: keep the higher-trust record. On a tie, keep the one with longer content.
- Label as 'duplicate' instead of deleting.

## Schedule

Stagger the runs so the dedup bot always sees complete input.

- **6:00 AM** - CVE Bot, Zero-day Bot, and Paper Bot run simultaneously. They are independent of each other.
- **6:30 AM** - Dedup bot runs, thirty minutes later, to ensure the three main bots have finished.
- If your Automations platform supports result-based triggers instead of fixed times, prefer that: the dedup bot fires only when all three main bots return successfully.

Failure handling for the dedup bot:

- If one bot fails or returns empty, the dedup bot still processes whatever input it has.
- It writes a log entry in the label field: "bot X returned no data" for the missing source.
- You still get a morning report instead of silence.

Output goes into a Notion database with three fields: date, bot, content.

## Try it

```bash
python3 dedup.py
python3 -m unittest discover -s tests -v
```

## Notes

- 80% is a starting balance point. Adjust after a week based on feel.
- Don't filter too aggressively: two different issues with similar titles can get wrongly marked. Different CVE IDs are always kept apart.
- All bot prompts force English output so the English stopwords in dedup.py stay effective. If any bot starts returning Vietnamese titles, dedup accuracy drops.

## License

[MIT](LICENSE)
