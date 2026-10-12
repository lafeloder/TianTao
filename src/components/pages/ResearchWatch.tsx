'use client';

import { useEffect, useMemo, useState } from 'react';
import type { Paper, Vacancy, School, WatchMeta } from '@/types/watchlists';
import s from './Watchlists.module.css';

const journals = ['JF', 'JFE', 'RFS', 'RF', 'JFQA'];
const journalNames: Record<string, string> = { JF: 'Journal of Finance', JFE: 'Journal of Financial Economics', RFS: 'Review of Financial Studies', RF: 'Review of Finance', JFQA: 'Journal of Financial and Quantitative Analysis' };
const fmt = (date: string) => date ? new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(date + 'T00:00:00Z')) : 'Not stated';
const recent = (date: string, end: string) => date >= new Date(new Date(end + 'T00:00:00Z').getTime() - 7 * 86400000).toISOString().slice(0, 10);
const external = { target: '_blank', rel: 'noopener noreferrer' };

function Header({ kind, meta, count }: { kind: 'papers' | 'jobs'; meta: WatchMeta; count: number }) {
  return <>
    <p className={s.eyebrow}>Research watch · Tian Tao</p>
    <h1 className={s.title}>{kind === 'papers' ? 'Top 5 Finance R&R' : 'European Postdocs'}</h1>
    <p className={s.intro}>{kind === 'papers'
      ? 'Working papers with publicly disclosed revise-and-resubmit decisions at five leading finance journals. Tracked through author research pages.'
      : 'Postdoctoral opportunities in banking, corporate finance, labor economics and general economics. Built around Europe’s top 50 business schools in the FT ranking.'}</p>
    <div className={s.update}><span className={s.dot}/><span>Last updated: {fmt(meta.last_run)}</span><span>·</span><span>Updated weekly · Mondays</span><a className={s.link} href={`/TianTao/watchlists/${kind === 'papers' ? 'rr' : 'postdocs'}.json`} download>Download data</a></div>
    <div className={s.stats}>
      <div className={s.stat}><strong>{count}</strong><span>{kind === 'papers' ? 'Publicly disclosed R&Rs' : 'Open FT top-50 opportunities'}</span></div>
      <div className={s.stat}><strong>{kind === 'papers' ? meta.articles.toLocaleString('en-GB') : meta.schools}</strong><span>{kind === 'papers' ? 'Indexed five-year publications' : 'Schools in the monitored universe'}</span></div>
      <div className={s.stat}><strong>{kind === 'papers' ? `${meta.approved_homepages} / ${meta.author_name_groups.toLocaleString('en-GB')}` : `${meta.feeds_fetched} / ${meta.schools}`}</strong><span>{kind === 'papers' ? 'Approved homepages / author name groups' : 'Career feeds fetched in the last run'}</span></div>
    </div>
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
  const topics = [...new Set(items.flatMap(p => p.topics))].sort();
  const filtered = useMemo(() => items.filter(p =>
    (showRecheck || p.status === 'R&R') &&
    (journal === 'All journals' || p.journal === journal) &&
    (topic === 'All topics' || p.topics.includes(topic)) &&
    (!newOnly || recent(p.first_seen, meta.last_run)) &&
    `${p.title} ${p.authors.join(' ')} ${p.journal} ${p.topics.join(' ')}`.toLowerCase().includes(query.toLowerCase())
  ).sort((a, b) => sort === 'Title A–Z' ? a.title.localeCompare(b.title) : b.last_verified.localeCompare(a.last_verified) || a.title.localeCompare(b.title)), [items, journal, topic, newOnly, showRecheck, query, sort, meta.last_run]);
  return <main className={s.page}>
    <Header kind="papers" meta={meta} count={items.filter(p => p.status === 'R&R').length}/>
    <div className={s.notice}><strong>Coverage is still being expanded.</strong> The bibliography covers {fmt(meta.publication_window_start)}–{fmt(meta.publication_window_end)}. Homepage coverage currently reaches {meta.approved_homepages} author name groups; this list does not represent all R&Rs at these journals. Decisions are author disclosures, and the check date is separate from the decision date.</div>
    <div className={s.filters}>
      <label className={`${s.field} ${s.search}`}>Search<input type="search" placeholder="Paper title, author or topic" value={query} onChange={e => setQuery(e.target.value)}/></label>
      <Select label="Journal" value={journal} change={setJournal} options={['All journals', ...journals]}/>
      <Select label="Topic" value={topic} change={setTopic} options={['All topics', ...topics]}/>
      <Select label="Sort" value={sort} change={setSort} options={['Latest verified', 'Title A–Z']}/>
    </div>
    <div className={s.controls}><label className={s.check}><input type="checkbox" checked={newOnly} onChange={e => setNewOnly(e.target.checked)}/>First found this update week</label><label className={s.check}><input type="checkbox" checked={showRecheck} onChange={e => setShowRecheck(e.target.checked)}/>Include entries needing recheck</label><button className={s.reset} onClick={() => { setQuery(''); setJournal('All journals'); setTopic('All topics'); setSort('Latest verified'); setNewOnly(false); setShowRecheck(false); }}>Reset filters</button></div>
    <p className={s.count} role="status" aria-live="polite">{filtered.length} paper{filtered.length !== 1 ? 's' : ''} · {journals.map(j => `${j} ${filtered.filter(p => p.journal === j).length}`).join(' / ')}</p>
    <div className={s.cards}>{filtered.map(p => <article className={s.card} key={p.id}>
      <div className={s.cardTop}><h2 className={s.cardTitle}><a href={p.paper_url || p.evidence_url} {...external}>{p.title}</a></h2><div className={s.badges}><span className={`${s.badge} ${s.journal}`}>{p.journal}</span><span className={`${s.badge} ${p.status === 'R&R' ? s.green : ''}`}>{p.status}</span></div></div>
      <p className={s.authors}>{p.authors.join(' · ')}</p>
      <div className={s.tags}>{p.topics.map(t => <span className={s.tag} key={t}>{t}</span>)}</div>
      <div className={s.cardFoot}><div className={s.links}><a className={s.link} href={p.evidence_url} {...external}>Author’s status page ↗</a>{p.paper_url && <a className={s.link} href={p.paper_url} {...external}>Read paper ↗</a>}</div><span>Verified {fmt(p.last_verified)}</span></div>
      <details className={s.evidence}><summary>Evidence and author eligibility</summary><p>Source: {p.source_author}. Status label: “{p.evidence_excerpt}”.{p.source_updated && <> Source lists an update in {p.source_updated}; this is not necessarily the decision date.</>}</p>{p.eligibility ? <p>{p.eligibility.author} appears on an indexed {p.eligibility.journal} publication dated {fmt(p.eligibility.published)}: <a className={s.link} href={`https://doi.org/${p.eligibility.doi}`} {...external}>{p.eligibility.title}</a>.</p> : <p>Publication-level author eligibility is awaiting verification.</p>}</details>
    </article>)}</div>
    {!filtered.length && <p className={s.empty}>No papers match these filters. Try another journal, topic or author.</p>}
    <section className={s.methods}><h2>Scope and evidence</h2><p>{journals.map(j => `${j}: ${journalNames[j]}`).join('; ')}.</p><p>The author universe starts with all retrievable Crossref journal-article records first published in the rolling five-year window. Editorial matter and corrections are excluded by title. Crossref registration dates are not used as publication dates. Online publication can precede a journal’s issue date.</p><p>{meta.author_identity_records.toLocaleString('en-GB')} provisional identity records form {meta.author_name_groups.toLocaleString('en-GB')} normalized name groups. Namesakes, name variants and affiliation changes require publication-level checking before a homepage is approved. Journal metadata completion does not imply complete author-page coverage.</p><div className={s.tableWrap}><table className={s.table}><caption className="sr-only">Crossref journal retrieval coverage</caption><thead><tr><th>Journal</th><th>Articles</th><th>Metadata retrieval</th><th>Checked</th></tr></thead><tbody>{journals.map(j => <tr key={j}><td>{j}</td><td>{meta.journals[j]?.articles ?? 0}</td><td>{meta.journals[j]?.status ?? 'pending'}</td><td>{meta.journals[j]?.checked_on ? fmt(meta.journals[j].checked_on!) : 'Not checked'}</td></tr>)}</tbody></table></div><p>Only explicit revise-and-resubmit or R&amp;R wording qualifies. Reject-and-resubmit, invitations under dual submission, acceptance and forthcoming papers are excluded. New automated discoveries enter an evidence review queue before public display. Missing status wording prompts rechecking; a fetch failure preserves the last successful verification date.</p></section>
  </main>;
}

export function PostdocWatch({ items, schools, meta, rankingUrl }: { items: Vacancy[]; schools: School[]; meta: WatchMeta; rankingUrl: string }) {
  const [query, setQuery] = useState('');
  const [field, setField] = useState('All fields');
  const [country, setCountry] = useState('All countries');
  const [scope, setScope] = useState('FT top 50 only');
  const [status, setStatus] = useState('Active & uncertain');
  const [today, setToday] = useState(meta.last_run);
  useEffect(() => { setToday(new Date().toLocaleDateString('en-CA', { timeZone: 'Europe/London' })); }, []);
  const effective = items.map(j => ({ ...j, status: j.deadline && j.deadline < today ? 'closed' : j.status }));
  const filtered = effective.filter(j =>
    (scope !== 'FT top 50 only' || j.scope === 'FT Europe top 50') &&
    (field === 'All fields' || j.topics.includes(field)) &&
    (country === 'All countries' || j.country === country) &&
    (status === 'All statuses' || (status === 'Active & uncertain' ? j.status !== 'closed' : j.status === (status === 'Open only' ? 'open' : 'closed'))) &&
    `${j.title} ${j.institution} ${j.city} ${j.fit} ${j.topics.join(' ')}`.toLowerCase().includes(query.toLowerCase())
  ).sort((a, b) => (a.deadline || '9999').localeCompare(b.deadline || '9999') || a.institution.localeCompare(b.institution));
  return <main className={s.page}>
    <Header kind="jobs" meta={meta} count={effective.filter(j => j.scope === 'FT Europe top 50' && j.status === 'open').length}/>
    <div className={s.notice}>School membership follows the <a href={rankingUrl} {...external}>FT European Business School Rankings 2025</a>, ranks 1–50. Public university recruitment pages and public LinkedIn advertisements provide evidence. A listing without a confirmed closing date is labelled “deadline unknown”. Additional European institutes can be shown with the scope filter.</div>
    <div className={s.filters}>
      <label className={`${s.field} ${s.search}`}>Search<input type="search" placeholder="Institution, position or keyword" value={query} onChange={e => setQuery(e.target.value)}/></label>
      <Select label="Research field" value={field} change={setField} options={['All fields', 'Banking', 'Corporate finance', 'Labor', 'General interest']}/>
      <Select label="Country" value={country} change={setCountry} options={['All countries', ...new Set(items.map(j => j.country))].sort((a,b) => a === 'All countries' ? -1 : b === 'All countries' ? 1 : a.localeCompare(b))}/>
      <Select label="Scope" value={scope} change={setScope} options={['FT top 50 only', 'Include additional institutes']}/>
      <Select label="Status" value={status} change={setStatus} options={['Active & uncertain', 'Open only', 'Closed only', 'All statuses']}/>
    </div>
    <div className={s.controls}><span>Sorted by application deadline</span><button className={s.reset} onClick={() => { setQuery(''); setField('All fields'); setCountry('All countries'); setScope('FT top 50 only'); setStatus('Active & uncertain'); }}>Reset filters</button></div>
    <p className={s.count} role="status" aria-live="polite">{filtered.length} opportunit{filtered.length === 1 ? 'y' : 'ies'} · Dates checked against {fmt(today)}</p>
    <div className={s.cards}>{filtered.map(j => <article className={s.card} key={j.id}>
      <div className={s.cardTop}><div><h2 className={s.cardTitle}><a href={j.source_url} {...external}>{j.title}</a></h2><p className={s.authors}>{j.institution} · {j.city}, {j.country}</p></div><div className={s.badges}><span className={`${s.badge} ${j.status === 'open' ? s.green : ''}`}>{j.status}</span><span className={`${s.badge} ${s.journal}`}>{j.rank ? `FT Europe #${j.rank}` : 'Additional institute'}</span></div></div>
      <div className={s.tags}>{j.topics.map(t => <span className={s.tag} key={t}>{t}</span>)}</div><p className={s.fit}>{j.fit}</p>
      <dl className={s.jobGrid}><div><dt>Deadline</dt><dd>{fmt(j.deadline)}</dd></div><div><dt>Duration</dt><dd>{j.duration}</dd></div><div><dt>Start</dt><dd>{j.start}</dd></div><div><dt>Salary</dt><dd>{j.salary}</dd></div></dl>
      <p className={s.fit}>{j.notes}</p>
      <div className={s.cardFoot}><div className={s.links}><a className={s.link} href={j.source_url} {...external}>{j.source_type} evidence ↗</a><a className={s.link} href={j.apply_url} {...external}>{j.status === 'closed' ? 'Recruitment page' : j.source_type === 'LinkedIn' ? 'Official careers page' : 'Application details'} ↗</a></div><span>Verified {fmt(j.last_verified)}</span></div>
    </article>)}</div>
    {!filtered.length && <p className={s.empty}>No verified opportunities match these filters. Expand the scope or change the research field.</p>}
    <section className={s.methods}><h2>Screening and coverage</h2><p>Postdoctoral appointments and research fellowships requiring a PhD are eligible. PhD studentships, assistant professor appointments, visiting positions and professional finance jobs are excluded. “General interest” means economics roles open across multiple research areas. Related roles such as corporate network research are explicitly labelled.</p><p>The monitored list contains 50 ranked business schools, including tied ranks. A university-wide feed is filtered for the relevant academic unit; ranking a business school does not automatically rank all departments of its parent university. Additional institutes are outside the main ranking filter.</p><p>{meta.coverage_note} {meta.linkedin_note} Pagination, dynamic recruitment platforms and inaccessible sources may leave gaps. The first edition contains a small verified shortlist, rather than a complete census of vacancies at all 50 schools.</p><details><summary>View the 50-school monitoring list and feed checks</summary><div className={s.tableWrap}><table className={s.table}><caption className="sr-only">FT European business-school monitoring list</caption><thead><tr><th>FT rank</th><th>School / recruitment source</th><th>Country</th><th>Last feed result</th></tr></thead><tbody>{schools.map(school => <tr key={school.id}><td>{school.rank}</td><td><a className={s.link} href={school.career_url} {...external}>{school.name}</a></td><td>{school.country}</td><td>{school.feed_status}</td></tr>)}</tbody></table></div></details><p>Expired deadlines move listings out of the active view. Conflicting advert details and unconfirmed application status remain visible in the relevant status label. New discoveries require source review before publication.</p></section>
  </main>;
}
