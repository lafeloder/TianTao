# Weekly research watchlists

The navigation entries follow the existing `Other` route (currently labelled
`CV`). `Top5RR` and `EuropePostdocs` are static Next.js routes using the original
site layout and theme. Existing About, Research, CV and Data pages are retained.

## Scope

- Finance journals: JF, JFE, RFS, RF, JFQA; all reference-list extended journals
  are retained under the extended scope. This is an explicit monitoring
  definition, not a claim of a universal top-five ranking.
- Author eligibility: at least one retrievable journal article first published
  in the rolling five-year window in those journals. The first edition covers
  2021-10-12 through 2026-10-12.
- Schools: ranks 1–50 in the FT European Business School Rankings 2025,
  including ties. Revisit membership when the next annual ranking is published.
  This is unrelated to the FT50 journal list.
- Jobs: European postdoctoral roles requiring a PhD in banking, corporate
  finance, labor or general economics. Related fields are described explicitly.
  SAFE and RFBerlin are optional additional institutes, not ranked-school claims.

## Data and evidence

`content/watchlists/` holds the authoritative data; the four public JSON exports
live in `public/watchlists/`. The large publication and author metadata files
are deterministic gzip JSON files to avoid repetitive multi-megabyte commits.
Use `bootstrap.load()` or Python's `gzip` module to inspect them.

- `corpus.json.gz`: DOI-level Crossref metadata and per-journal completion.
- `author-universe.json.gz`: ORCID identities where available, otherwise
  provisional names and affiliations. Normalized name groups are not definitive
  unique people: namesakes, name variants and duplicate affiliations need care.
- `homepages.json`: publication-level approved author/source identities.
- `rr.json`: R&R, reject-and-resubmit and changed decision statuses kept separately. `first_seen` is our
  discovery date, not a decision date; `source_updated` is a source's own update
  label, not a guaranteed decision date.
- `postdocs.json`: official evidence, deadlines, uncertainties and application
  links. A missing deadline is not interpreted as confirmed open recruitment.
- `schools.json`: 50-school universe, configured recruitment feeds and their
  actual fetch outcomes. Some feeds are blocked, outdated or dynamic.
- `review-queue.json`: newly discovered pages, papers and vacancies awaiting
  evidence checks. Discoveries are not automatically public endorsements.
- `run-report.json`, `meta.json` and `history/`: source outcomes, current
  coverage and dated snapshots. Fetch failures do not change verification dates.

The expanded edition includes the complete Chen Yang paper-status reference,
all matching European records in OpenPostdoc and EJM public pagination, and
additional primary-source records. `coverage-manifest.json` preserves every
reference identifier; validation fails if a reference record disappears. The complete retrievable publication universe is indexed; the
homepages of every author have not yet been identified or checked. A successful
HTML feed fetch does not prove exhaustive vacancy coverage. Public LinkedIn
access may be blocked, and no signed-in or complete LinkedIn coverage is claimed.

## Updates

`watchlists-weekly.yml` runs Mondays at 06:15 UTC, with manual dispatch available.
It refreshes the bibliography, rechecks approved pages and current adverts,
checks the configured school feeds, queries new ORCID identities, then imports
complete public reference pagination through `benchmarks.py`. It retains dated
cached snapshots when a provider is blocked or pagination is incomplete, saves
review candidates, validates coverage, commits changes and calls the deployment
workflow. The bot's commit does not need to trigger another push workflow.

The separately scheduled ChatGPT task reviews new evidence, expands homepage
coverage and adds verified entries. It is authorized to update this repository
and publish the two requested pages, while keeping existing personal content.

Optional GitHub Actions secrets:

- `CROSSREF_MAILTO`: contact email for Crossref's polite API pool.
- `BRAVE_SEARCH_API_KEY`: accelerates discovery of author pages lacking ORCID.
  No paid service or API key is required for the known-source crawler.

```bash
python -m pip install -r scripts/watchlists/requirements.txt
python -m unittest discover -s scripts/watchlists -p 'test_*.py'
python scripts/watchlists/bootstrap.py
python scripts/watchlists/refresh.py
python scripts/watchlists/validate.py
npm ci --no-audit --no-fund
npm run build
```

Approve a new author page only after matching the person to an eligible DOI and
publication on that page or an official profile. To promote a paper, verify its
title and complete author list, strict R&R wording, target journal, source URL
and whether any newer source says accepted or published. For vacancies verify
the employer/unit, European location, PhD requirement, relevant field and
closing date; a LinkedIn discovery needs official confirmation when available.

After approved edits, run `refresh.py` to update the public exports and metadata,
then validate and build before committing. Keep failed or ambiguous evidence
visible in the coverage report. Never convert an inaccessible source into an
empty-success result.

## Reference coverage contract

The expanded edition reconciled all 76 Chen Yang reference rows (75 unique
papers), all 36 matching European OpenPostdoc IDs from 3,230 worldwide board
and archive records, and all 44 matching EJM IDs from the six status and five
positions pages. Records are deduplicated without losing provider identifiers.

Coverage means every same-scope fetched reference record is accounted for; it
does not mean every source is current or that every five-year author homepage
has been searched. The publication universe remains a separate expansion task.
Explicit changes such as JF forthcoming supersede an older R&R report.
An author page without a current decision retains the original report under a
reference-only label. Closed/filled searches remain in the historical job view.

When an official website is blocked, use a coauthor/CV/institution page for
papers, and an employer-written EJM advert, official department recruitment
page, public recruitment PDF, public LinkedIn or a second board for jobs. Never
let a generic fetch or listing-page deadline silently remove or misdate records.
The source snapshots and public-page screening logic are factual metadata;
full job adverts and paper abstracts are not republished.
