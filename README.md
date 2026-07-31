# ergo-directory

An index of published [ergo](https://github.com/lavallee/ergo) data pages, so
an agent or a person can ask one place: **does anyone document this dataset?**

This is the default directory. It is not the only one, and it is not meant to
be — running your own is a JSON file in a git repo, and consumers mix as many
as they like.

## What is in here

- [`directory.json`](directory.json) — the index. Every entry points at
  wherever its page actually lives.
- [`pages/`](pages) — the pages this directory is the **home** of.

An entry is one of two kinds:

| | canonical page lives | corrections go to |
|---|---|---|
| **indexed** | the publisher's own repository | that repository |
| **hosted** | here, in `pages/` | here |

Hosting exists because of a case an index alone cannot serve. Most datasets'
publishers will never write a page. The projects that do are very often
private — a data team's repository holds more than its documentation — and a
public bundle served from a private repository is **published but
unpatchable**: anyone can read the page, nobody can fix it, and no one else
can ever improve it.

A page nobody can patch is a document, not a commons. So the default runs
this way: **a page is canonical here unless its author can accept corrections
publicly.** A public repository that takes pull requests keeps its own page
and we index it. Everyone else contributes the page itself.

**Entries are pointers** — subject, bundle URL, `contribute`, and a few
cached facts for browsing. The rule that matters:

> **One home per page.** Exactly one place accepts corrections to a page, and
> it is the place that serves its bytes.

So corrections to a page go where its `contribute` says, which is almost
always its own repository and not here. `check.py` enforces it: an entry
naming this repository while its bundle is served elsewhere is an error.

That is what stops a directory becoming a fork of every page in it. It also
means we *can* host a page that has no other home — most datasets have none —
without breaking anything, because a hosted page's `contribute` really is this
repository. See CONTRIBUTING.

## Several pages will document the same dataset. That is correct.

The obvious worry is eight competing ACS pages. It isn't a problem to solve.

A newsroom's ACS page, a housing nonprofit's, and a state agency's will
legitimately disagree — about which issues are `core`, about which practices
apply, about what the one-line `pitfall` is — because their *questions* differ.
An ergo `[practice]` is by definition a decision that reasonable teams make
differently. Collapsing them into one "canonical" page destroys the thing
that makes them worth having.

So this directory **clusters; it never decides.** There is deliberately:

- no precedence or ranking between entries,
- no shadowing of one directory by another,
- no merging on read,
- no deduplication across directories.

Every match comes back, attributed. The human chooses.

## Clustering: `subject`

Pages declare a `subject` — one URL naming what the page is *about*. It is
distinct from `source_urls`, which say where a project gets its bytes: two
projects reading the same census product through a mirror and an API share a
subject. It is explicitly a **best guess**; nobody assigns these.

To compare two subjects, normalize both (ergo SPEC §10): fold the scheme to
`https`, lowercase the host, drop a leading `www.`, a trailing slash, a
trailing `index.`/`default.` page of any common extension, and the fragment.
**Keep the query string** — for some publishers the query carries the dataset
identity, and dropping it would fuse distinct sources.

- Equal normalized subjects → one cluster.
- Same host, one path a prefix of the other → a **candidate**, reported for a
  human to judge, never merged.

`python3 check.py` validates the file and prints both.

Entries with `"subject_declared": false` predate ergo's `subject` field; the
subject shown is this directory's best guess from the page's source URL. A
publisher can replace a guess with a claim by declaring `subject` on the page
and sending a PR here.

## Adding your pages

1. Serve a bundle: `python3 tools/ergo.py publish <pages-dir> --dir <out> --base-url <url>`
2. Generate your entries:

   ```
   python3 tools/ergo.py directory <pages-dir> \
       --bundle https://your.site/data/ergo/ --entries-only
   ```

3. Paste them into `directory.json`, run `python3 check.py`, open a PR.

Set `subject` on your pages first — a page without one cannot be clustered,
and ergo's validator warns about it.

## Using it

Add it to your project's `ergo-sources.toml`:

```toml
[[source]]
name = "default"
url = "https://raw.githubusercontent.com/lavallee/ergo-directory/main/directory.json"
```

Consumers query every configured source and return every hit, tagged with
which directory it came from. Lookup order, cheapest first: pages in your own
repo → the publisher's own bundle → directories.

## Running your own

Copy `directory.json`, keep `"ergo_directory": "1"`, put it anywhere with a
stable URL, and add it to your `ergo-sources.toml`. That's the whole
mechanism. A newsroom directory of the twenty datasets its desk actually uses
is a perfectly good directory, and probably more useful to that desk than
this one.

## Directory file format

```json
{
  "ergo_directory": "1",
  "name": "…",
  "updated": "YYYY-MM-DD",
  "entries": [
    {
      "subject": "https://www.example.gov/programs/thing",   // required
      "bundle": "https://publisher.example/data/ergo/",       // required
      "subject_normalized": "https://example.gov/programs/thing",
      "subject_declared": true,
      "slug": "thing", "title": "…", "publisher": "…", "updated": "YYYY-MM-DD",
      "years": "…",
      "recognizes": {
        "domains": ["example.gov"],
        "filenames": ["thing_*.csv"],
        "columns": ["GEO_ID", "NAME"]
      }
    }
  ]
}
```

`recognizes` is optional and answers the harder question: an agent holding a
file with no provenance — renamed, re-exported, emailed as an attachment —
can match on publisher domain, filename pattern, or **column fingerprint**.
Report a signature match with its basis ("matched 14 of 16 column names");
never assert identity from one silently.

Everything except `subject` and `bundle` is a cache for browsing. **The
bundle wins on any disagreement.**

## License

MIT. The indexed pages belong to their publishers.
