#!/usr/bin/env python3
"""Validate a directory file and report its subject clusters.

    python3 check.py [directory.json ...]

Stdlib only, Python >= 3.11. Errors exit 1. The clustering rules are ergo
SPEC §10; this file carries its own copy of the normalization so a directory
can be validated without vendoring the whole ergo tool.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ENTRY_REQUIRED = ("subject", "bundle")
ENTRY_KNOWN = {
    "subject", "subject_normalized", "subject_declared", "bundle", "slug",
    "title", "publisher", "updated", "years", "recognizes",
}
RECOGNIZES_KNOWN = {"domains", "filenames", "columns"}
URL = re.compile(r"^https?://\S+$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def normalize_subject(url):
    """SPEC §10. Fold scheme to https, lowercase host, drop www./trailing
    slash/index page/fragment. The query string is KEPT."""
    s = str(url or "").strip()
    if not s:
        return ""
    m = re.match(r"^(https?)://([^/?#]+)([^?#]*)(\?[^#]*)?", s, re.I)
    if not m:
        return s.rstrip("/")
    host, path, query = m.group(2).lower(), m.group(3) or "", m.group(4) or ""
    host = host.removeprefix("www.")
    path = re.sub(r"/(index|default)\.(html?|shtml|php|aspx?|jsp)$", "/", path, flags=re.I)
    return f"https://{host}{path.rstrip('/')}{query}"


def check(path):
    errors, warnings = [], []
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return [f"{path}: unreadable: {e}"], [], {}
    if doc.get("ergo_directory") != "1":
        errors.append(f'{path}: ergo_directory must be "1"')
    if not DATE.match(str(doc.get("updated", ""))):
        warnings.append(f"{path}: updated should be YYYY-MM-DD")
    entries = doc.get("entries")
    if not isinstance(entries, list):
        return errors + [f"{path}: entries must be an array"], warnings, {}

    clusters = defaultdict(list)
    seen = set()
    for i, e in enumerate(entries):
        where = f"{path}: entries[{i}]" + (f" ({e.get('slug')})" if isinstance(e, dict) else "")
        if not isinstance(e, dict):
            errors.append(f"{where}: must be an object")
            continue
        for f in ENTRY_REQUIRED:
            if not str(e.get(f) or "").strip():
                errors.append(f"{where}: missing required field: {f}")
        for f in ("subject", "bundle"):
            if e.get(f) and not URL.match(str(e[f])):
                errors.append(f"{where}: {f} must be an http(s) URL, got {e[f]!r}")
        for k in set(e) - ENTRY_KNOWN:
            warnings.append(f"{where}: unknown key {k!r}")
        # a directory indexes bundles; it must never carry page content
        for banned in ("issues", "practices", "page_content", "bite"):
            if banned in e:
                errors.append(f"{where}: carries {banned!r} — a directory indexes bundles, "
                              f"it does not hold page content (§10)")
        rec = e.get("recognizes")
        if rec is not None:
            if not isinstance(rec, dict):
                errors.append(f"{where}: recognizes must be an object")
            else:
                for k in set(rec) - RECOGNIZES_KNOWN:
                    warnings.append(f"{where}: unknown recognizes key {k!r}")
        if e.get("updated") and not DATE.match(str(e["updated"])):
            warnings.append(f"{where}: updated should be YYYY-MM-DD")

        subject = str(e.get("subject") or "")
        norm = normalize_subject(subject)
        if e.get("subject_normalized") and e["subject_normalized"] != norm:
            errors.append(f"{where}: subject_normalized is stale — expected {norm!r}")
        key = (norm, str(e.get("bundle") or ""), str(e.get("slug") or ""))
        if key in seen:
            errors.append(f"{where}: duplicate entry (same subject, bundle and slug)")
        seen.add(key)
        if norm:
            clusters[norm].append(e)
    return errors, warnings, clusters


def report_clusters(clusters):
    shared = {k: v for k, v in clusters.items() if len(v) > 1}
    if shared:
        print("\nSubjects documented by more than one page — expected, not a conflict:")
        for subject, group in sorted(shared.items()):
            print(f"  {subject}")
            for e in group:
                print(f"      {e.get('slug','?'):24} {e.get('bundle','')}")
    # near-miss candidates: same host, one path a prefix of the other
    keys = sorted(clusters)
    near = []
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            ha, pa = a.split("://")[1].split("/", 1)[0], a
            hb, pb = b.split("://")[1].split("/", 1)[0], b
            if ha == hb and (pa.startswith(pb + "/") or pb.startswith(pa + "/")):
                near.append((a, b))
    if near:
        print("\nCandidate matches for a human to judge — NOT merged automatically:")
        for a, b in near:
            print(f"  {a}\n  {b}\n")


def main(argv):
    paths = argv[1:] or ["directory.json"]
    all_err, all_warn, merged = [], [], defaultdict(list)
    for p in paths:
        e, w, c = check(p)
        all_err += e
        all_warn += w
        for k, v in c.items():
            merged[k] += v
    for m in all_err:
        print(f"error: {m}")
    for m in all_warn:
        print(f"warning: {m}")
    n = sum(len(v) for v in merged.values())
    print(f"{len(paths)} file(s), {n} entr{'y' if n == 1 else 'ies'}, "
          f"{len(merged)} subject(s): {len(all_err)} error(s), {len(all_warn)} warning(s)")
    if not all_err:
        report_clusters(merged)
    return 1 if all_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
