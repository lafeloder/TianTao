'use client';

import { useEffect, useMemo, useState } from 'react';
import type { Paper, Vacancy, School, WatchMeta, CoverageSource } from '@/types/watchlists';
import s from './Watchlists.module.css';

const journals = ['JF', 'JFE', 'RFS', 'RF', 'JFQA'];
const journalNames: Record<string, string> = { JF: 'Journal of Finance', JFE: 'Journal of Financial Economics', RFS: 'Review of Financial Studies', RF: 'Review of Finance', JFQA: 'Journal of Financial and Quantitative Analysis' };
const fmt = (date: string) => /^\d{4}-\d{2}-\d{2}$/.test(date || '') ? new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(date + 'T00:00:00Z')) : 'Not stated';
const recent = (date: string, end: string) => date >= new Date(new Date(end + 'T00:00:00Z').getTime() - 7 * 86400000).toISOString().slice(0, 10);
const external = { target: '_blank', rel: 'noopener noreferrer' };


function Coverage({ sources }: { sources: CoverageSource[] }) {
  if (!sources.length) return null;
  return <section className={s.coverage}><h2>Reference coverage</h2><p>Same-scope records are accounted for before deduplication, including historical or changed-status records.</p><div className={s.tableWrap}><table className={s.table}><thead><tr><th>Reference</th><th>Scanned</th><th>In scope</th><th>Accounted for</th><th>Missing</th><th>Checked</th></tr></thead><tbody>{sources.map(r => <tr key={r.name}><td><a className={s.link} href={r.url} {...external}>{r.name} ↗</a></td><td>{r.total_scanned}</td><td>{r.in_scope}</td><td>{r.matched} / {r.in_scope}</td><td>{r.missing}</td><td>{fmt(r.checked_on)}<br/>{r.status}</td></tr>)}</tbody></table></div>{sources.map(r => r.note && <p key={r.name}>{r.name}: {r.note}</p>)}</section>;
}
function Pager({ total, page, change }: { total: number; page: number; change: (n: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / 25));
  return <nav className={s.pager} aria-label="Results pagination"><button disabled={page <= 1} onClick={() => change(page - 1)}>← Previous</button><span>Page {page} / {pages} · 25 per page</span><button disabled={page >= pages} onClick={() => change(page + 1)}>Next →</button></nav>;
}

function Header({ kind, meta, count }: { kind: 'papers' | 'jobs'; meta: WatchMeta; count: number }) {
  const refs = meta.benchmark_sources?.[kind === 'papers' ? 'papers' : 'jobs'] || [];
  const total = refs.reduce((n,r) => n + r.in_scope, 0);
  const matched = refs.reduce((n,r) => n + r.matched, 0);
  return <>
    <p className={s.eyebrow}>Research watch · Tian Tao</p>
    <h1 className={s.title}>{kind === 'papers' ? 'Top 5 Finance R&R' : 'European Postdocs'}</h1>
    <p className={s.intro}>{kind === 'papers'
      ? 'Financial working-paper status reports from author pages and reference indexes. Finance top five and extended journals are available as separate views.'
      : 'European postdoctoral opportunities in banking, corporate finance, labor and economics. Official advertisements, OpenPostdoc and Econ Job Market are combined; FT school membership is a filter.'}</p>
    <div className={s.update}><span className={s.dot}/><span>Last updated: {fmt(meta.last_run)}</span><span>·</span><span>Updated weekly · Mondays</span><a className={s.link} href={`/TianTao/watchlists/${kind === 'papers' ? 'rr' : 'postdocs'}.json`} download>Download data</a></div>
    <div className={s.stats}>
      <div className={s.stat}><strong>{count}</strong><span>{kind === 'papers' ? 'Revision-stage paper reports' : 'Current or uncertain opportunities'}</span></div>
      <div className={s.stat}><strong>{kind === 'papers' ? meta.articles.toLocaleString('en-GB') : (meta.job_counts?.historical || 0)}</strong><span>{kind === 'papers' ? 'Indexed five-year publications' : 'Historical opportunities retained'}</span></div>
      <div className={s.stat}><strong>{matched} / {total}</strong><span>{kind === 'papers' ? 'Reference rows accounted for' : 'Reference rows accounted for'}</span></div>
    </div>
    <Coverage sources={refs}/>
  </>;
}

function Select({ label, value, change, options }: { label: string; value: string; change: (s: string) => void; options: string[] }) {
  return <label className={s.field}>{label}<select value={value} onChange={e => change(e.target.value)}>{options.map(o => <option key={o} value={o}>{o}</option>)}</select></label>;
}

export function PaperWatch({ items, meta }: { items: Paper[]; meta: WatchMeta }) {
  const [query, setQuery] = useState('');
  const [journal, setJournal] = useState('All journals');
  const [topic, setTopic] = useState('All topics');
  const [sort, setSort] = useState('Latest verified');
  const [newOnly, setNewOnly] = useState(false);
  const [showRecheck, setShowRecheck] = useState(false);
  const [scope, setScope] = useState('All tracked journals');
  const [page, setPage] = useState(1);
  useEffect(() => setPage(1), [query, journal, topic, sort, newOnly, showRecheck, scope]);
  const availableJournals = [...journals, ...new Set(items.map(p => p.journal).filter(j => !journals.includes(j)))];
  const topics = [...new Set(items.flatMap(p => p.topics))].sort();
  const filtered = useMemo(() => items.filter(p =>
    (showRecheck || ['R&R', 'Reject & Resubmit', 'Invited revision'].includes(p.status)) &&
    (scope !== 'Finance top five only' || journals.includes(p.journal)) &&
    (journal === 'All journals' || p.journal === journal) &&
    (topic === 'All topics' || p.topics.includes(topic)) &&
    (!newOnly || recent(p.first_seen, meta.last_run)) &&
    `${p.title} ${p.authors.join(' ')} ${p.journal} ${p.topics.join(' ')}`.toLowerCase().includes(query.toLowerCase())
  ).sort((a, b) => sort === 'Title A–Z' ? a.title.localeCompare(b.title) : b.last_verified.localeCompare(a.last_verified) || a.title.localeCompare(b.title)), [items, journal, topic, newOnly, showRecheck, query, sort, meta.last_run, scope]);
  const effectivePage = Math.min(page, Math.max(1, Math.ceil(filtered.length / 25)));
  const shown = filtered.slice((effectivePage-1)*25, effectivePage*25);
  return <main className={s.page}>
    <Header kind="papers" meta={meta} count={items.filter(p => ['R&R', 'Reject & Resubmit', 'Invited revision'].includes(p.status)).length}/>
    <div className={s.notice}>The complete reference list is retained. Finance top five and extended journals are separated by scope; reject-and-resubmit remains a distinct decision. Accepted or unresolved records are available under “Include other statuses”. Reference coverage is separate from scanning every author in the five-year publication universe.</div>
    <div className={s.filters}>
      <label className={`${s.field} ${s.search}`}>Search<input type="search" placeholder="Paper title, author or topic" value={query} onChange={e => setQuery(e.target.value)}/></label>
      <Select label="Scope" value={scope} change={setScope} options={['All tracked journals', 'Finance top five only']}/>
      <Select label="Journal" value={journal} change={setJournal} options={['All journals', ...availableJournals]}/>
      <Select label="Topic" value={topic} change={setTopic} options={['All topics', ...topics]}/>
      <Select label="Sort" value={sort} change={setSort} options={['Latest verified', 'Title A–Z']}/>
    </div>
    <div className={s.controls}><label className={s.check}><input type="checkbox" checked={newOnly} onChange={e => setNewOnly(e.target.checked)}/>First found this update week</label><label className={s.check}><input type="checkbox" checked={showRecheck} onChange={e => setShowRecheck(e.target.checked)}/>Include accepted / other statuses</label><button className={s.reset} onClick={() => { setQuery(''); setJournal('All journals'); setTopic('All topics'); setSort('Latest verified'); setNewOnly(false); setShowRecheck(false); setScope('All tracked journals'); }}>Reset filters</button></div>
    <p className={s.count} role="status" aria-live="polite">{filtered.length} paper{filtered.length !== 1 ? 's' : ''} · {journals.map(j => `${j} ${filtered.filter(p => p.journal === j).length}`).join(' / ')}</p>
    <div className={s.cards}>{shown.map(p => <article className={s.card} key={p.id}>
      <div className={s.cardTop}><h2 className={s.cardTitle}><a href={p.paper_url || p.evidence_url} {...external}>{p.title}</a></h2><div className={s.badges}><span className={`${s.badge} ${s.journal}`}>{p.journal}</span><span className={`${s.badge} ${p.status === 'R&R' ? s.green : ''}`}>{p.status}</span></div></div>
      <p className={s.authors}>{p.authors.join(' · ')}</p><p className={s.verification}>{p.verification || 'Author-page disclosure'}</p>
      <div className={s.tags}>{p.topics.map(t => <span className={s.tag} key={t}>{t}</span>)}</div>
      <div className={s.cardFoot}><div className={s.links}><a className={s.link} href={p.evidence_url} {...external}>Status source ↗</a>{p.reference_url && <a className={s.link} href={p.reference_url} {...external}>Reference index ↗</a>}{p.paper_url && <a className={s.link} href={p.paper_url} {...external}>Read paper ↗</a>}</div><span>Checked {fmt(p.last_verified || p.reference_checked_on || '')}</span></div>
      <details className={s.evidence}><summary>Evidence and author eligibility</summary><p>Source: {p.source_author}. Status label: “{p.evidence_excerpt}”.{p.source_updated && <> Source lists an update in {p.source_updated}; this is not necessarily the decision date.</>}</p>{p.eligibility ? <p>{p.eligibility_status === 'verified' ? 'Verified eligible author:' : 'Indexed author-name match (identity checking may still be required):'} {p.eligibility.author} appears on an indexed {p.eligibility.journal} publication dated {fmt(p.eligibility.published)}: <a className={s.link} href={`https://doi.org/${p.eligibility.doi}`} {...external}>{p.eligibility.title}</a>.</p> : <p>Five-year publication eligibility remains unconfirmed; the reference record is retained for follow-up.</p>}{p.authors_note && <p>{p.authors_note}</p>}</details>
    </article>)}</div>
    {!filtered.length && <p className={s.empty}>No papers match these filters. Try another journal, topic or author.</p>}
    <Pager total={filtered.length} page={effectivePage} change={setPage}/>
    <section className={s.methods}><h2>Scope and evidence</h2><p>{journals.map(j => `${j}: ${journalNames[j]}`).join('; ')}.</p><p>The author universe starts with all retrievable Crossref journal-article records first published in the rolling five-year window. Editorial matter and corrections are excluded by title. Crossref registration dates are not used as publication dates. Online publication can precede a journal’s issue date.</p><p>{meta.author_identity_records.toLocaleString('en-GB')} provisional identity records form {meta.author_name_groups.toLocaleString('en-GB')} normalized name groups. Namesakes, name variants and affiliation changes require publication-level checking before a homepage is approved. Journal metadata completion does not imply complete author-page coverage.</p><div className={s.tableWrap}><table className={s.table}><caption className="sr-only">Crossref journal retrieval coverage</caption><thead><tr><th>Journal</th><th>Articles</th><th>Metadata retrieval</th><th>Checked</th></tr></thead><tbody>{journals.map(j => <tr key={j}><td>{j}</td><td>{meta.journals[j]?.articles ?? 0}</td><td>{meta.journals[j]?.status ?? 'pending'}</td><td>{meta.journals[j]?.checked_on ? fmt(meta.journals[j].checked_on!) : 'Not checked'}</td></tr>)}</tbody></table></div><p>R&amp;R, Reject &amp; Resubmit, acceptance and publication retain separate status labels. Extended journals preserve the reference baseline and can be filtered out. A source check date is not a decision date. Status changes move records to the appropriate view; blocked sources retain their earlier evidence and trigger alternate-source searches.</p></section>
  </main>;
}

export function PostdocWatch({ items, schools, meta, rankingUrl }: { items: Vacancy[]; schools: School[]; meta: WatchMeta; rankingUrl: string }) {
  const [query, setQuery] = useState('');
  const [field, setField] = useState('All fields');
  const [country, setCountry] = useState('All countries');
  const [scope, setScope] = useState('All European institutions');
  const [status, setStatus] = useState('Active & uncertain');
  const [today, setToday] = useState(meta.last_run);
  const [page, setPage] = useState(1);
  useEffect(() => setPage(1), [query, field, country, scope, status]);
  useEffect(() => { setToday(new Date().toLocaleDateString('en-CA', { timeZone: 'Europe/London' })); }, []);
  const effective = items.map(j => ({ ...j, status: j.deadline && j.deadline < today ? 'closed' : j.status }));
  const filtered = effective.filter(j =>
    (scope !== 'FT top 50 only' || j.scope === 'FT Europe top 50') &&
    (field === 'All fields' || j.topics.includes(field)) &&
    (country === 'All countries' || j.country === country) &&
    (status === 'All statuses' || (status === 'Active & uncertain' ? j.status !== 'closed' : j.status === (status === 'Open only' ? 'open' : 'closed'))) &&
    `${j.title} ${j.institution} ${j.city} ${j.fit} ${j.topics.join(' ')}`.toLowerCase().includes(query.toLowerCase())
  ).sort((a, b) => (a.deadline || '9999').localeCompare(b.deadline || '9999') || a.institution.localeCompare(b.institution));
  const effectivePage = Math.min(page, Math.max(1, Math.ceil(filtered.length / 25)));
  const shown = filtered.slice((effectivePage-1)*25, effectivePage*25);
  return <main className={s.page}>
    <Header kind="jobs" meta={meta} count={effective.filter(j => j.status !== 'closed').length}/>
    <div className={s.notice}>School membership follows the <a href={rankingUrl} {...external}>FT European Business School Rankings 2025</a>, ranks 1–50. Public university recruitment pages and public LinkedIn advertisements provide evidence. A listing without a confirmed closing date is labelled “deadline unknown”. All matching European institutions are included by default. FT top 50 is an optional filter. Historical advertisements remain in the closed/all-status views; reviewing applications is not the same as accepting new applications.</div>
    <div className={s.filters}>
      <label className={`${s.field} ${s.search}`}>Search<input type="search" placeholder="Institution, position or keyword" value={query} onChange={e => setQuery(e.target.value)}/></label>
      <Select label="Research field" value={field} change={setField} options={['All fields', ...new Set(items.flatMap(j => j.topics))]}/>
      <Select label="Country" value={country} change={setCountry} options={['All countries', ...new Set(items.map(j => j.country))].sort((a,b) => a === 'All countries' ? -1 : b === 'All countries' ? 1 : a.localeCompare(b))}/>
      <Select label="Scope" value={scope} change={setScope} options={['All European institutions', 'FT top 50 only']}/>
      <Select label="Status" value={status} change={setStatus} options={['Active & uncertain', 'Open only', 'Closed only', 'All statuses']}/>
    </div>
    <div className={s.controls}><span>Sorted by application deadline</span><button className={s.reset} onClick={() => { setQuery(''); setField('All fields'); setCountry('All countries'); setScope('All European institutions'); setStatus('Active & uncertain'); }}>Reset filters</button></div>
    <p className={s.count} role="status" aria-live="polite">{filtered.length} opportunit{filtered.length === 1 ? 'y' : 'ies'} · Dates checked against {fmt(today)}</p>
    <div className={s.cards}>{shown.map(j => <article className={s.card} key={j.id}>
      <div className={s.cardTop}><div><h2 className={s.cardTitle}><a href={j.source_url} {...external}>{j.title}</a></h2><p className={s.authors}>{j.institution} · {j.city}, {j.country}</p></div><div className={s.badges}><span className={`${s.badge} ${j.status === 'open' ? s.green : ''}`}>{j.status}</span><span className={`${s.badge} ${s.journal}`}>{j.rank ? `FT school #${j.rank}` : 'Additional European institution'}</span></div></div>
      <p className={s.verification}>{j.verification || j.source_type}{j.search_status && ` · Recruiter search: ${j.search_status}`}</p><div className={s.tags}>{j.topics.map(t => <span className={s.tag} key={t}>{t}</span>)}</div><p className={s.fit}>{j.fit}</p>
      <dl className={s.jobGrid}><div><dt>Deadline</dt><dd>{fmt(j.deadline)}</dd></div><div><dt>Duration</dt><dd>{j.duration}</dd></div><div><dt>Start</dt><dd>{j.start}</dd></div><div><dt>Salary</dt><dd>{j.salary}</dd></div></dl>
      <p className={s.fit}>{j.notes}</p>
      <div className={s.cardFoot}><div className={s.links}><a className={s.link} href={j.source_url} {...external}>{j.source_type} evidence ↗</a><a className={s.link} href={j.apply_url} {...external}>{j.status === 'closed' ? 'Recruitment page' : j.source_type === 'LinkedIn' ? 'Official careers page' : 'Application details'} ↗</a></div><span>Checked {fmt(j.last_verified)}</span></div>
      {!!j.source_reports?.length && <details className={s.evidence}><summary>Cross-source evidence</summary>{j.source_reports.map((r,i) => <p key={i}><a className={s.link} href={r.url} {...external}>{r.name}</a> · checked {fmt(r.checked_on)}{r.reported_status && ` · reported ${r.reported_status}`}</p>)}</details>}
    </article>)}</div>
    {!filtered.length && <p className={s.empty}>No verified opportunities match these filters. Expand the scope or change the research field.</p>}
    <Pager total={filtered.length} page={effectivePage} change={setPage}/>
    <section className={s.methods}><h2>Screening and coverage</h2><p>Postdoctoral appointments and research fellowships requiring a PhD are eligible. PhD studentships, assistant professor appointments, visiting positions and professional finance jobs are excluded. “General interest” means economics roles open across multiple research areas. Related roles such as corporate network research are explicitly labelled.</p><p>The monitored list contains 50 ranked business schools, including tied ranks. A university-wide feed is filtered for the relevant academic unit; ranking a business school does not automatically rank all departments of its parent university. Additional institutes are outside the main ranking filter.</p><p>{meta.coverage_note} {meta.linkedin_note} Pagination, dynamic recruitment platforms and inaccessible sources may leave gaps. All in-scope reference records are retained after deduplication, including closed searches. Same-scope coverage excludes non-European and unrelated biomedical or engineering jobs; a source misclassification is documented rather than imported to inflate totals.</p><details><summary>View the 50-school monitoring list and feed checks</summary><div className={s.tableWrap}><table className={s.table}><caption className="sr-only">FT European business-school monitoring list</caption><thead><tr><th>FT rank</th><th>School / recruitment source</th><th>Country</th><th>Last feed result</th></tr></thead><tbody>{schools.map(school => <tr key={school.id}><td>{school.rank}</td><td><a className={s.link} href={school.career_url} {...external}>{school.name}</a></td><td>{school.country}</td><td>{school.feed_status}</td></tr>)}</tbody></table></div></details><p>Expired deadlines move listings out of the active view. Conflicting advert details and unconfirmed application status remain visible in the relevant status label. New discoveries require source review before publication.</p></section>
  </main>;
}
