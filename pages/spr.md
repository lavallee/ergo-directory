# NJ School Performance Reports

Reporter's notebook for the SPR dataset: where it comes from, how we fetch it,
how it joins to our enrollment warehouse, and every oddity worth knowing before
you trust a number. Companion to the Fall Enrollment ledger
(`soma-student-population/SOURCES.md`).

```toml ergo
[dataset]
ergo = "0.4"
slug = "spr"
title = "NJ School Performance Reports"
publisher = "NJ Dept. of Education, Office of Performance Reports"
subject = "https://www.nj.gov/education/spr/"
source_url = "https://www.nj.gov/education/spr/"
pitfall = "NJ publishes two 4-yr graduation rates — State and Federal — but only State is populated across years (27,115 of 27,201 trend rows; Federal in just 5,423, effectively one year); plotting Federal as a trend, or comparing states on it, is the classic misread."
status = "live"
confidence = "A"
updated = "2026-07-10"
implementation = "https://github.com/lavallee/njschooldata"

[dataset.coverage]
years = "2015-16 → 2024-25 (trend tabs post-COVID only — see spr/trend-tabs-post-covid-only)"
grain = "school year × entity × student group"
entities = "every NJ public school, district, and the state"

[dataset.access]
keys = ["county_code", "district_code", "school_code", "school_year"]
```

## Where this data now comes from

njschooldata no longer downloads or parses this source. Aquifer owns the
acquisition, the schema-era parsers, and the immutable release; the issues below
that describe parsing or source format are recorded against the producer's own
registry and are monitored here rather than handled here. The consumer adapter
installs an exact offline pin, and the issues still marked as handled are the
ones this repo genuinely handles.

Rollback is no longer "re-run the local builder" — the local builder is gone.
Roll the pin back to a retained release and re-run the adapter.

## What it is

New Jersey's official annual "report card" for every public school and
district. ESSA-mandated accountability data: state assessments (NJSLA
ELA/Math/Science, NJGPA), student growth, graduation & dropout, chronic
absenteeism, discipline / HIB, college & career readiness (PSAT/SAT/ACT,
AP/IB/dual enrollment, CTE), staffing (experience, ratios, retention), and
ESSA accountability status.

This is the authoritative source for the academic-outcome modules we're
adding to school/district profiles (graduation first, then assessment +
absenteeism).

Contact: `reportcard@doe.nj.gov`. Granularity: school, district, and state —
every NJ public entity. Disaggregated by `StudentGroup` (all students +
race/ethnicity, ELL, econ-disadvantaged, disability, etc. — 17 categories
total; full list under Validation).

Logged as "acquisition in progress" through 2026-06; the builder now loads
five tables (`grad_rate`, `assessment`, `assessment_grade`, `absenteeism`,
`growth`) into the shared warehouse — see Builder.

## Access

The **landing page** is `https://www.nj.gov/education/spr/download/`, but
it's a JS app: a year `<select>` plus `script/download.js?v=11` that builds
the real file links. The files themselves live under a **different host
path** — `sprreports`, not `spr` (`spr/url-host-split`):

```
https://www.nj.gov/education/sprreports/download/DataFiles/<YEAR>/<file>
```

`<YEAR>` is hyphenated four-digit, e.g. `2024-2025`. Files (from
`download.js`):

| File | What |
|---|---|
| `Database_SchoolDetail.xlsx` | **school-level**, every report tab in one workbook |
| `Database_DistrictStateDetail.xlsx` | **district + state** level, same tabs |
| `Database_SchoolLayout.xlsx` / `Database_DistrictLayout.xlsx` | **data dictionary** — one sheet per tab (Field / Type / Description) |
| `…/Documents/<YEAR>/ReferenceGuide.pdf`, `DataPrivacyRules.pdf`, `FAQs.pdf` | prose docs |

`.zip` (zipped xlsx) and `.accdb` (Access) variants also exist **for older
years only**. The JS flags `isNewYearFormat = year >= "2024-2025"`: from
2024-25 on, **only the `.xlsx`** is offered — no zip, no Access, no
Reference Guide PDF (`spr/new-format-2024-25-xlsx-only`).

### Year coverage

Dropdown offers **2015-16 → 2024-25** (the JS pre-provisions
2025-26…2029-30).
- `2016-17 →` : full two-file (school + district/state) format.
- `2015-16` : special two-column layout.
- `2011-12 … 2014-15` : **legacy** — the page redirects to the archive
  (`https://nj.gov/education/schoolperformance/archive/`); not in this URL
  scheme.

### File sizes (2024-2025) — these are *large*

| File | Bytes | ~ |
|---|---|---|
| `Database_SchoolDetail.xlsx` | 346,029,712 | **330 MB** |
| `Database_DistrictStateDetail.xlsx` | 119,164,900 | **114 MB** |
| `Database_SchoolLayout.xlsx` | 214,014 | 209 KB |

One monolithic workbook packs **~80 report tabs**. Loading the whole thing
with openpyxl in default mode is heavy (`spr/monolithic-workbook-size`) — the
builder uses `read_only=True` and pulls only the sheet(s) it needs. (Contrast
Fall Enrollment: small per-year zips.)

Raw files are cached locally and are re-fetchable. Aquifer now owns governed
2024-25 edition captures, selected-tab manifests, literal suppression states,
immutable releases, and exact offline pins for chronic absence, graduation,
assessment headline, assessment by test, and student growth.
This repo's `tools/build_aquifer_spr.py` and
`tools/build_aquifer_spr_graduation.py`, and
`tools/build_aquifer_spr_assessment.py`, and
`tools/build_aquifer_spr_assessment_by_test.py`, and
`tools/build_aquifer_spr_growth.py` replace only `absenteeism`, `grad_rate`,
`assessment`, `assessment_grade`, and `growth`, respectively. The local legacy
builder remains the documented rollback producer for all migrated tables
during their notice periods.

## Structure

Every tab repeats the same identity columns, then its own metrics:

```
CountyCode(Numeric) CountyName DistrictCode(Numeric) DistrictName
SchoolCode(Numeric) SchoolName SchoolYear StudentGroup  + <metrics>
```

Header is on **row 4**; data starts **row 5** (rows 1–3 are title/note).

## Joins

The layout types the code columns "Numeric," but the **actual data cells are
zero-padded TEXT** — `CountyCode`="13", `DistrictCode`="4900"
(`spr/layout-types-lie`) — i.e. they match our warehouse's TEXT keys
verbatim (county 2-wide, district 4-wide; school width to confirm from the
school file, expected 3). `SchoolYear` is `"2020-21"`, also matching the
warehouse format, though the layout's declared type for it disagrees tab to
tab (`spr/schoolyear-typing-inconsistent`). So SPR joins to `enrollment`
directly on `(district_code, school_code, school_year)` with no coercion.
Confirmed against the 2024-25 District/State file.

## Tabs we use

Confirmed columns from the 2024-25 School layout.

### Graduation — `GraduationRateTrends` (the one for `mod_graduation`)

Multi-year (**2020-21 … 2024-25** — five years), and carries school **+**
district **+** state in each row, so the trajectory line *and* its context
line come from one tab:

```
… SchoolYear StudentGroup 4YrCohort
4YrGraduationRate{State,Federal}_{School,District,State}
5Yr… 6Yr…  (same shape for 5- and 6-year cohorts)
```

- ⚠️ **Use the State calculation for the trajectory** (`spr/grad-state-vs-federal`):
  NJ publishes two 4-yr rates — State and Federal — but only the State rate
  is populated across all five years; the Federal rate appears only for the
  most recent year (2024-25).
  - `mod_graduation` plots `4YrGraduationRate**State**_{School|District}`
    over the five years, with `…State_State` as the statewide context line.
  - Headline the latest-year **Federal** 4-yr ACGR too where present, and
    note in the caption that NJ's State calc runs higher than the federal
    ACGR. Don't draw Federal as a trend — it has one point.
  - To extend earlier than 2020-21, pull older years' files (each carries ~5
    years of State rates). 5 years is enough for the proof-of-shape.
  - The local `grad_rate` compatibility table intentionally exposes the
    existing 4-year State/Federal and 5-year State columns. Aquifer's canonical
    pinned release additionally retains all 4/5/6-year State/Federal values at
    entity, district-context, and state-context grain with exact cohort and
    suppression literals.
- `FederalGraduationRates` (single year, Federal only) is redundant given the
  Trends tab's latest-year Federal columns.
- `GraduationCohortProfile` (graduated / continuing / non-continuing /
  persisting) is a richer follow-on, not yet loaded into the builder. Its
  `NonContinuing_District` and `Persisting_District` columns are typed
  **Text** while siblings are Numeric — a suppression tell
  (`spr/cohort-profile-text-suppression-tell`).

### Chronic absenteeism — `ChronicAbsenteeismTrends` → `mod_absenteeism` ✅ built

Years **2021-22 … 2024-25** (four); `ChronicAbsenteeismRate_{School,District,State}`
by StudentGroup. The "Alphanumeric" typing we flagged is real: cells are
`"8.1%"` strings, with prose suppression and `">90%"` extreme-capping mixed
in (`spr/rate-prose-suppression`). Loaded into the `absenteeism` table (rate
+ district/statewide context); applies to **all grade levels**, not
HS-gated. SOMSD: 12.6→15.6→11.2→8.1% vs NJ ~18→14%.

### Assessment — NJSLA ELA + Math → `mod_assessment` ✅ built (stacked-area, dual-lens)

Three tabs feed this, all **2021-22 → 2024-25** (`spr/trend-tabs-post-covid-only`):
- **`ELA`/`MathParticipationPerformance`** → table `assessment`: the
  official school-wide `MetExceededExpectations` NJ publishes (+
  participation), per entity·year·subject. Drives the headline % in each
  subject's lede.
- **`ELA`/`MathPerformanceByTest`** → table `assessment_grade`: per
  entity·year·subject·**grade-test**, the full **Level 1–5** distribution +
  mean scaled score + proficiency (numeric *and* raw string, so capped
  `<10%`/`>90%` show honestly). The honest grain — NJ never publishes a
  school-wide 1–5 distribution, only per test.
- **`StudentGrowthTrends`** → table `growth`: median **Student Growth
  Percentile** (1–99, 50 = typical) for ELA + Math with NJ's
  Low/Typical/High label, at school/district/state. The
  demographic-independent "is it good?" signal.

The module: **growth lead** (an SGP scale) → the exact NJDOE-published
school-wide All Students record → per subject, stacked-area 1–5 distributions
in two lenses. **Lens A** is "by grade, year to year" (a panel per grade).
**Lens B** lines up aggregate grade results along diagonals of the grade × year
matrix. It approximates a class path, but the rows are not linked student
records: enrollment and the tested population can change between years. All
panels are interactive (hover → level breakdown); single column on mobile.

Key design calls (settled through review):
- **Growth is the lead** where it exists; **high schools have no SGP**
  (`spr/hs-no-sgp` — it's grades 4-8 only) so they fall back to a
  proficiency frame and get **no cohort lens** (one grade can't be traced).
- **Per-grade, never school-wide-aggregated** levels
  (`spr/grade-aggregation-bias`) — aggregating across grade-tests is biased
  by suppression and mixes incomparable course populations.
- Math cohort tracking is **grades 3-8 only**
  (`spr/math-cohort-grades-3-8-only` — HS course tests aren't a clean
  grade+1 sequence).
- **Grade-mix nuance** (`spr/grade-mix-context`): a school's headline
  proficiency reflects only its tested grades, but district/state blend all
  grades 3-8 + HS — so a HS's math can sit *below* its district. Real, not a
  bug.
- Pre-COVID NJSLA (2018-19 + the no-spring-2020 gap) needs older-year files
  (deferred — `spr/trend-tabs-post-covid-only`).

## Issues

### Landing page and file host are different paths

```toml ergo
[issue]
id = "url-host-split"
title = "Files live under /education/sprreports/, not the /education/spr/ landing path"
effect = "breaks"
type = "availability"
status = "monitor"
discovered = "2026-06"
detection = "404s when constructing file URLs from the landing-page path instead of the sprreports host"

[issue.scope]
all = true
```

The landing page (`https://www.nj.gov/education/spr/download/`) is a JS app
whose `download.js?v=11` builds the real links:
`https://www.nj.gov/education/sprreports/download/DataFiles/<YEAR>/<file>`,
with hyphenated years (`2024-2025`). Easy to fetch the wrong path if you
build URLs from the landing page itself.

### The layout workbook's "Numeric" typing is misleading

```toml ergo
[issue]
id = "layout-types-lie"
title = "Code columns typed 'Numeric' in the layout are zero-padded TEXT in the data"
effect = "corrupts"
type = "format"
status = "monitor"
discovered = "2026-06"
detection = "CountyCode='13', DistrictCode='4900' — string cells with leading zeros preserved, despite the layout workbook's dictionary calling them Numeric"
misuse = "Coercing codes to integers strips leading zeros and silently breaks the warehouse join."

[issue.scope]
tables = ["grad_rate", "assessment", "assessment_grade", "absenteeism", "growth"]
columns = ["CountyCode", "DistrictCode", "SchoolCode"]
years = "all"
```

Confirmed against the 2024-25 District/State file: the data cells match the
warehouse's TEXT keys verbatim (county 2-wide, district 4-wide; school width
to confirm from the school file, expected 3), so the *correct* behavior is
to trust the data over the data dictionary.

### `SchoolYear`'s declared type disagrees tab to tab

```toml ergo
[issue]
id = "schoolyear-typing-inconsistent"
title = "SchoolYear is declared Numeric in some tabs' layout and Text in others, though the data is always the string \"2020-21\""
effect = "corrupts"
type = "format"
status = "monitor"
discovered = "2026-06"
detection = "layout workbook's Type column for SchoolYear varies by tab; every tab's actual SchoolYear cell reads as the hyphenated string, e.g. '2020-21'"
misuse = "Writing per-tab ingestion code that trusts each tab's declared SchoolYear type parses some tabs as numeric and others as text inconsistently; always treat SchoolYear as a string."

[issue.scope]
tables = ["grad_rate", "assessment", "assessment_grade", "absenteeism", "growth"]
columns = ["SchoolYear"]
years = "all"
```

Same lesson as the code columns (`spr/layout-types-lie`), but for
`SchoolYear`: the layout's per-tab data dictionary is not a reliable source
of column types. The builder's `s()` helper coerces every identity column to
a stripped string regardless of what the layout claims.

### Rate cells are strings, with prose suppression and capped extremes mixed in

```toml ergo
[issue]
id = "rate-prose-suppression"
title = "Rate cells carry % signs, prose suppression sentences, and >90%/<10% privacy caps"
effect = "breaks"
core = true
type = "suppression"
status = "monitor"
discovered = "2026-06"
detection = "value fails float() after stripping a trailing % — includes '>90%', '<10%', and prose sentences"
misuse = "Treating suppression NULLs as zero. Capped extremes also go NULL — fine for All Students (they only hit tiny subgroups), a real loss for small subgroups."

[issue.scope]
tables = ["grad_rate", "assessment", "assessment_grade", "absenteeism"]
columns = ["*Rate*", "*Percent*"]
years = "all"
```

Parse rule (`rate()` in the builder): a value is a number iff it parses
after stripping a trailing `%`; everything else → NULL. Four distinct
suppression sentences observed in the 2024-25 files: "Fewer than 10 students
were in the graduation cohort.", "Fewer than 10 valid scores", "Enrollment
for this group was less than 10 students.", "There is no data available for
this school year." — plus the two extreme caps, `">90%"` and `"<10%"`.

### Two graduation-rate calculations, one populated trend

```toml ergo
[issue]
id = "grad-state-vs-federal"
title = "State and Federal 4-yr graduation rates coexist; only State is populated across years"
effect = "misleads"
type = "measurement"
status = "monitor"
discovered = "2026-06"
detection = "4YrGraduationRateState_District non-empty in 27,115 of 27,201 trend rows; …Federal_District in only 5,423 (≈ one year)"
misuse = "Drawing the Federal rate as a trend line (it has one point), or comparing a State figure against another state's federal ACGR — NJ's State calc runs higher (SOMSD 2024-25: State 93.2% vs Federal 89.4%)."

[issue.scope]
tables = ["grad_rate"]
columns = ["4YrGraduationRate*", "5YrGraduationRate*"]
years = "all"
```

The builder keeps `grad4` (State calc) and `grad4_federal` (latest-year-only
ACGR) as separate columns rather than conflating them. `mod_graduation`
plots the State trajectory and headlines the latest-year Federal figure
separately, with the difference noted in the caption.

### Big monolithic workbooks need streaming, not a full load

```toml ergo
[issue]
id = "monolithic-workbook-size"
title = "The school-level workbook is ~330 MB with ~80 tabs — a full non-streaming load is impractical"
effect = "breaks"
type = "format"
status = "monitor"
discovered = "2026-06"
detection = "Database_SchoolDetail.xlsx is 346,029,712 bytes (330 MB); Database_DistrictStateDetail.xlsx is 119,164,900 bytes (114 MB)"

[issue.scope]
all = true
```

One monolithic workbook per year packs ~80 report tabs. Loading the whole
thing with openpyxl in default mode is heavy; the builder's `read_tab()`
opens with `read_only=True` and pulls only the sheet it needs.

### From 2024-25, only the xlsx is published

```toml ergo
[issue]
id = "new-format-2024-25-xlsx-only"
title = "From 2024-25 on, NJDOE drops the zip, Access, and Reference Guide PDF variants"
effect = "context"
type = "availability"
status = "open"
discovered = "2026-06"
detection = "download.js sets isNewYearFormat = year >= '2024-2025'; for those years only Database_*.xlsx is linked"
misuse = "Expecting a Reference Guide PDF, zip, or Access variant for 2024-25 and later — from 2024-25 on NJDOE publishes .xlsx only."

[issue.scope]
years = "2024-25 →"
```

Earlier years (`2016-17 →`) offer `.zip` (zipped xlsx) and `.accdb` (Access)
alongside the xlsx, plus a Reference Guide PDF, DataPrivacyRules PDF, and
FAQs PDF under `…/Documents/<YEAR>/`. `2015-16` uses a special two-column
layout; `2011-12 … 2014-15` are legacy and redirect to a separate archive,
outside this URL scheme entirely.

### `GraduationCohortProfile`'s Text-typed columns are a suppression tell

```toml ergo
[issue]
id = "cohort-profile-text-suppression-tell"
title = "NonContinuing/Persisting columns on GraduationCohortProfile are typed Text while their siblings are Numeric"
effect = "breaks"
type = "suppression"
status = "open"
discovered = "2026-06"
detection = "NonContinuing_District and Persisting_District are typed Text in the layout workbook; every other GraduationCohortProfile metric column is Numeric"

[issue.scope]
tables = ["GraduationCohortProfile"]
columns = ["NonContinuing_District", "Persisting_District"]
years = "all"
```

`GraduationCohortProfile` (graduated / continuing / non-continuing /
persisting) is a richer follow-on to the Trends tab, not yet loaded into the
builder. The Text typing on two of its columns — while every sibling metric
is Numeric — is the same tell as the rate columns elsewhere: these carry
suppression markers as strings, and will need the same `rate()`-style
handling whenever this tab is built.

### Trend tabs in the current file only go back to COVID

```toml ergo
[issue]
id = "trend-tabs-post-covid-only"
title = "The 2024-25 file's trend tabs start at 2020-21 or 2021-22, not earlier"
effect = "context"
type = "coverage"
status = "open"
discovered = "2026-06"
detection = "GraduationRateTrends carries 2020-21…2024-25 (five years); ELA/MathParticipationPerformance, PerformanceByTest, and StudentGrowthTrends carry 2021-22…2024-25 (four years) in the 2024-25 file"
misuse = "Assuming the current file's trend tabs cover full history — pre-COVID NJSLA (2018-19 and earlier, with the no-spring-2020 testing gap) requires pulling older years' files separately; deferred in this builder."

[issue.scope]
tables = ["grad_rate", "assessment", "assessment_grade", "absenteeism", "growth"]
years = "2024-25 file only shows 2020-21→2024-25 (grad) / 2021-22→2024-25 (assessment, absenteeism, growth)"
```

Each year's workbook carries a rolling window (five years for graduation,
four for assessment/absenteeism/growth), not the full published history. To
extend earlier than 2020-21, pull older years' files — each carries ~5 years
of State graduation rates, so five years is enough for the proof-of-shape
but not for pre-COVID NJSLA.

### Aggregating grade-tests silently biases the number

```toml ergo
[issue]
id = "grade-aggregation-bias"
title = "Summing grade-test proficiency into a school-wide figure is biased by suppression and course-mix — a capped Algebra I once inflated one"
effect = "misleads"
type = "measurement"
status = "monitor"
discovered = "2026-06"
detection = "a capped Algebra I test (values suppressed to '<10%'/'>90%') once inflated a home-grown school-wide aggregate by silently dropping its lowest cohort from the average"
misuse = "Aggregating assessment_grade's per-grade-test Level 1-5 distributions into a school-wide number instead of using NJ's own published school-wide MetExceededExpectations (table assessment) — suppression and incomparable course populations (Algebra I vs II) bias the result."

[issue.scope]
tables = ["assessment_grade"]
columns = ["l1", "l2", "l3", "l4", "l5", "proficiency", "prof_str"]
years = "all"
```

`build_by_test` keeps the per-grade-test grain and never aggregates across
grade-tests; NJ never publishes a school-wide 1-5 distribution, only per
test, and that's the honest grain. The school-wide headline % comes only
from NJ's own published `MetExceededExpectations` (table `assessment`),
never a home-grown recomputation.

### High schools have no Student Growth Percentile

```toml ergo
[issue]
id = "hs-no-sgp"
title = "StudentGrowthTrends has no rows for standalone high schools — SGP only exists for grades 4-8"
effect = "context"
type = "universe"
status = "open"
discovered = "2026-06"
detection = "growth table has zero rows for a standalone high school's own school_code; district/state context columns are still populated"
misuse = "Reading an absent growth row for a high school as missing or bad data — SGP is defined only for grades 4-8 by NJ's own methodology; high schools need a proficiency-only frame with no cohort lens."

[issue.scope]
tables = ["growth"]
entities = "standalone high schools"
years = "all"
```

Median Student Growth Percentile is NJ's demographic-independent "is it
adding value" signal (1-99, 50 = typical, with a Low/Typical/High label),
but it's computed only for grades 4-8. The profile module treats growth as
the lead metric where it exists and falls back to a proficiency frame — with
no cohort lens, since a single grade can't be traced — for high schools.

### Math cohort tracking only works for grades 3-8

```toml ergo
[issue]
id = "math-cohort-grades-3-8-only"
title = "The cohort-diagonal view (a class followed as it moves up) only works for grades 3-8 math"
effect = "context"
type = "coverage"
status = "open"
discovered = "2026-06"
misuse = "Trying to trace a high school math cohort year-over-year the way grades 3-8 are traced — HS course tests (Algebra I/II, Geometry, etc.) aren't a clean grade+1 sequence, so students in 'Algebra I' this year aren't reliably in 'Algebra II' next year."

[issue.scope]
tables = ["assessment_grade"]
rows = "grade_test rows for HS course tests (Algebra I/II, Geometry, etc.)"
years = "all"
```

Lens B of the assessment module ("by class, followed as it moved up,"
cohort diagonals of the grade × year matrix) is offered only for grades 3-8
math. High school course tests don't form a clean sequence, so no cohort
lens is offered for them.

### A school's headline proficiency reflects only its tested grades

```toml ergo
[issue]
id = "grade-mix-context"
title = "District/state context blends all tested grades; a school's value covers only its own"
effect = "context"
type = "definitional"
status = "open"
discovered = "2026-06"
misuse = "Reading a high school's math proficiency sitting below its district as a deficit — the district figure blends grades 3-8 with HS course tests over different populations."

[issue.scope]
tables = ["assessment", "assessment_grade"]
```

Real, not a bug: comparisons across aggregation levels compare different
grade mixes. Per-grade views (`assessment_grade`) are the honest grain.

## Validation

```toml ergo
[validation]
date = "2026-06"
method = "confirmed from real data — 2024-25 District/State file"
result = "codes are zero-padded TEXT (county 2-wide, district 4-wide) despite the layout's 'Numeric' declaration; join to enrollment is clean on (district_code, school_code, school_year) with no coercion"
```

```toml ergo
[validation]
date = "2026-06"
method = "confirmed from real data — 2024-25 District/State file"
result = "SchoolYear cells read as the string '2020-21' regardless of a tab's declared type, matching the warehouse's SchoolYear format"
```

```toml ergo
[validation]
date = "2026-06"
method = "confirmed from real data — 2024-25 District/State file"
result = "All-students label is 'All Students'. Full StudentGroup set: All Students, White, Black or African American, Hispanic/Latino, Asian Native Hawaiian or Pacific Islander, American Indian or Alaska Native, Two or More Races, Male, Female, Non-Binary/Undesignated Gender, Economically Disadvantaged Students, Multilingual Learners, Students with Disabilities, Migrant Students, Military-Connected Students, Students Experiencing Homelessness, Students in Foster Care"
```

```toml ergo
[validation]
date = "2026-06"
method = "confirmed from real data — 2024-25 District/State file"
result = "suppression is a prose sentence, not a flag; non-numeric metric values are prose suppression plus >90%/<10% extreme-caps; rates carry a literal %; all map to NULL via rate()"
```

```toml ergo
[validation]
date = "2026-06"
method = "confirmed from real data — 2024-25 District/State file"
result = "assessment + absenteeism trend tabs run 2021-22 → 2024-25 (post-COVID only); pre-COVID NJSLA needs older-year files (deferred)"
```

```toml ergo
[validation]
date = "2026-06"
method = "confirmed from real data — 2024-25 District/State file"
result = "assessment district/state context blends all tested grades; a school's value reflects only its own tested grades (grade-mix nuance)"
```

## Provenance

Latest published: 2024-25 (released May 2026); databases downloadable back
to 2011-12 (legacy years via a separate archive — see
`spr/new-format-2024-25-xlsx-only`). Our working copy: 2024-25, fetched 2026-06; record re-pulls here.

## Changelog

```toml ergo
[change]
date = "2026-07-10"
note = "Converted to ergo format: 13 issues registered from the oddities list and tab notes; confirmed-from-real-data log became validation records."
```
