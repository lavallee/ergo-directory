# Contributing

## Adding your pages

Open a PR adding entries to `directory.json`. Generate them rather than
hand-writing them:

```
python3 tools/ergo.py directory <pages-dir> \
    --bundle https://your.site/data/ergo/ --entries-only
```

Then `python3 check.py` must pass. That's the whole bar.

Requirements per entry:

- **`subject` and `bundle` are required**, both http(s) URLs.
- The bundle must actually resolve — an entry pointing at a 404 is worse than
  no entry.
- Set `subject` on the page itself, not just here. A directory-side guess
  (`"subject_declared": false`) is a stopgap for pages predating the field.
- No page content. Entries carry pointers and a few cached facts for
  browsing; `check.py` rejects `issues`, `practices`, and `pitfall`.

## What does not belong here

- **Corrections to someone else's page.** Send those to that page's own
  repository. This directory indexes bundles and never holds their content,
  which is precisely what stops it becoming a fork of everything in it.
- **A ranking.** Several pages documenting one dataset is expected, not a
  conflict — their questions differ, so their `core` marks and practices
  legitimately differ. Entries are not ordered by quality and nothing here
  will ever declare a winner.
- **Private or paywalled bundles.** If a reader can't fetch it, indexing it
  only wastes their time.

## Duplicate subjects

Expected. `check.py` prints them as clusters, and near-misses (same host,
shared path prefix) as *candidates* for a human — it will not merge them.
If two entries genuinely describe the same dataset under different subject
URLs, the fix is for the publishers to agree on one, not for this directory
to pick.
