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

## Contributing the page itself

If your repository is private, a served bundle is *published but unpatchable* —
readable by anyone, fixable by no one. Contribute the page here instead, and it
becomes the canonical copy:

1. `python3 tools/ergo.py publish <pages-dir> --dir <out> --base-url <url>` —
   the public projection, with internal regions and repo-pointing fields
   removed. **Read it before you send it.** The projection strips known
   internal fields; it cannot know that a sentence in your lede names a path
   in your private tree.
2. Open a PR adding `<slug>.md` to `pages/` and an entry to `directory.json`
   whose `bundle` is
   `https://raw.githubusercontent.com/lavallee/ergo-directory/main/pages/`
   and whose `contribute` is this repository's issues.
3. In your own copy, record `[[dataset.derived_from]]` with that URL, today's
   date, and the `hash` — `ergo diverge` prints it.

Afterwards `ergo diverge` keeps the two in step: what the canonical page has
gained since you took it, and what your copy carries that it does not. The
second list is what you owe back. Your private copy stays the working copy;
the public one stays the copy anyone can fix.

`check.py` enforces the rest: a hosted entry must have its file in `pages/`,
must name us in `contribute`, and must not also be indexed somewhere else.

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
