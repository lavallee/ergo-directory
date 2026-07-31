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
- **`contribute`** — one URL where corrections to *your* page are accepted.
  Set it on the page's manifest (ergo 0.5, §4) and regenerate; `check.py`
  warns on an entry without one, because a reader who finds a mistake
  otherwise has nowhere to report it.

## One home per page

Exactly one place accepts corrections to a page, and it is the place that
serves the page's bytes. That is the whole rule, and `check.py` enforces it:
an entry whose `contribute` points at *this* repository while its `bundle` is
served elsewhere is an error, not a warning.

It is the reason this directory can be useful without becoming a fork of
everything in it.

## Pages with no other home

The rule above stops us patching someone else's page. It does not stop us
being the home of a page that has none — and most datasets have none, because
most publishers will never write one and most projects that could are private.

If you have documented a public dataset and cannot serve a bundle yourself,
open an issue before opening a PR. A page hosted here is not structurally
special: its `bundle` and `contribute` are both this repository, because this
really is where it lives. What we will not do is hold a second copy of a page
that already has a home somewhere else.

**When a publisher takes over.** If someone starts serving their own bundle
for a dataset we host, the entry's `bundle` and `contribute` change to theirs
and our copy is deleted — not kept in parallel "for reference". Two copies
with one subject is the condition all of this exists to prevent.

## What does not belong here

- **Corrections to someone else's page.** Send those to that page's own
  repository — its entry's `contribute` says where. This directory indexes
  bundles and does not hold the content of pages it does not host, which is
  precisely what stops it becoming a fork of everything in it.
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
