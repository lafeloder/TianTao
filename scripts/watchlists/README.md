# Weekly research watchlists

The navigation entries follow the existing `Other` route (currently labelled
`CV`). `Top5RR` and `EuropePostdocs` are static Next.js routes using the original
site layout and theme. Existing About, Research, CV and Data pages are retained.

## Scope

- Tracked journals: JF, JFE, RFS, RF, JFQA and Management Science (MS).
  The route and page title retain `Top5RR` / `Top 5 Finance R&R` for continuity;
  the chart and filter cover all six. Other reference-list journals remain in
  the extended scope. This is an explicit monitoring definition, not a claim
  of a universal top-five ranking. The data value `source_scope: top5` remains
  the legacy marker for the page's tracked six-journal set.
- Author eligibility: at least one retrievable journal article first published
  in the rolling five-year window in those journals. The current window and
  per-journal article counts are recorded in `meta.json`.
- Conference supplement: paper authors in public 2024–2026 AFA, WFA, EFA,
  SFS North America / Asia-Pacific and Paris December Finance programs, including
  publicly named doctoral presenters. Personal sites are preferred; individual
  institution research profiles are a fallback. Conference-only authors retain
  program evidence with no invented DOI and enter the weekly homepage scan.
  The displayed Finance Top5 publication-author statistic keeps its original
  five-journal denominator. No author-pool or MS-author totals are added to the UI.
- Weekly author membership is now fixed in `author-watchlist.json.gz`, matching
  the two-column author / website workbook delivered on 14 October 2026.
  The Monday workflow uses `refresh.py --fixed-author-list --skip-discovery`;
  it does not rebuild the publication-author universe or ingest new conference
  programs. Previously included conference authors remain eligible. Expand the
  roster only when the user requests it or announces a completed conference.
  Missing URLs stay blank; known institution profiles remain an allowed fallback.
  Explicit external Personal Website links are followed as author sources.
  URL-labelled links are also followed when a surrounding paragraph identifies
  them as a personal website. Author matching preserves Turkish dotless i and
  common accented-name domain spellings without changing saved author IDs.
  Newly linked roster rows seed weekly scans even when they had no earlier
  `homepages.json` entry. Eligibility follows only saved name aliases.
  Saved aliases also count toward publication-author coverage. A valid existing
  publication proof is retained; an earlier MS article does not overwrite a
  previously verified finance-journal eligibility record.
  Research content inside header/navigation wrappers is retained: those tags
  are used as page-layout containers by some personal-site templates.
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
- `homepages.json`: linked personal sites and institution profiles. Each new
  link records its discovery source and, where identity cannot be tied to a
  publication or affiliation on the page, a profile-only identity method.
- `ms-author-ledger.json.gz`: every normalized author name group with a recent
  Management Science publication, including unresolved names, homepage URL,
  identity method, search attempt and scan status. It is an internal audit file,
  not a downloadable spreadsheet.
- `conference-authors.json.gz`, `conference-author-ledger.json.gz`: source
  program evidence, supported name variants, every unresolved author, identified
  personal/institution page, and scan outcomes. Coverage is calculated after
  merging compatible aliases sharing verified individual pages. The EFA 2026
  doctoral tutorial's complete roster and SFS Asia-Pacific 2026 program are not
  publicly available; these source limits remain explicit in the ledger.
- `author-watchlist.json.gz`: fixed author membership, supported name aliases,
  preferred personal / individual institution webpage and known alternatives.
  The Excel is delivered locally and is never copied into `public/`.
- `author-website-audit.json`: URL repairs against the unchanged fixed roster,
  identity evidence, content-readability limits and remaining blank URLs.
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

Publication-author coverage retains the six-journal normalized-name denominator.
The October 14 URL-completion pass uses the unchanged 10,762-row saved watchlist,
with a target above 96% linked personal or individual institution profiles.
`meta.json` reports these measures separately. The displayed Finance Top5 count
retains its five-journal denominator of 4,301. Name-based biography matches keep
their identity caveats. Locating a source-restricted webpage does not count as a
successful R&R scan.

## Updates

`watchlists-weekly.yml` runs Mondays at 06:15 UTC, with manual dispatch available.
It rechecks saved author websites, research tabs and current adverts, checks
the configured school feeds, then imports public vacancy reference pagination
through `benchmarks.py --jobs-only`. Author discovery, bibliography expansion and
conference ingestion remain disabled until requested. It retains dated
cached snapshots when a provider is blocked or pagination is incomplete, saves
review candidates, validates coverage, commits changes and calls the deployment
workflow. The bot's commit does not need to trigger another push workflow.

The separately scheduled review task checks new evidence from the fixed saved
author roster and adds verified entries. Author or conference expansion requires
a user instruction. It is authorized to update this repository
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

Prefer a DOI/publication or institution match for author identity. A precise
personal or official school profile can be linked as profile-only when its
identity evidence is weaker; do not treat it as proof of an R&R decision. To
promote a paper, verify its
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
