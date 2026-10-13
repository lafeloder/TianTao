'use client';

import { useEffect, useState } from 'react';
import type { PaperView, VacancyView } from '@/lib/watchlists-public';
import s from './Watchlists.module.css';

const external = { target: '_blank', rel: 'noopener noreferrer' };
const revisionStatuses = ['R&R', 'Reject & Resubmit', 'Invited revision'];
const journalNames: Record<string, string> = {
  JF: 'The Journal of Finance',
  JFE: 'Journal of Financial Economics',
  RFS: 'The Review of Financial Studies',
  JFQA: 'Journal of Financial and Quantitative Analysis',
  RF: 'Review of Finance',
  MS: 'Management Science',
};
const fullJournalName = (journal: string) => journalNames[journal] || journal;
const fmt = (date: string) => /^\d{4}-\d{2}-\d{2}$/.test(date || '')
  ? new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(date + 'T00:00:00Z'))
  : 'Not stated';

function Search({ value, change, placeholder }: { value: string; change: (value: string) => void; placeholder: string }) {
  return <label className={s.search}><span className="sr-only">Search</span><input type="search" aria-label="Search" placeholder={placeholder} value={value} onChange={e => change(e.target.value)}/></label>;
}
function Pager({ total, page, change }: { total: number; page: number; change: (page: number) => void }) {
  const pages = Math.max(1, Math.ceil(total / 25));
  if (pages === 1) return null;
  return <nav className={s.pager} aria-label="Results pagination"><button disabled={page <= 1} onClick={() => change(page - 1)}>Previous</button><span>{page} / {pages}</span><button disabled={page >= pages} onClick={() => change(page + 1)}>Next</button></nav>;
}
function WatchHero({ title, intro, date }: { title: string; intro: string; date: string }) {
  return <header className={s.watchHero}>
    <p className={s.eyebrow}>Research watch · Tian Tao</p>
    <h1 className={s.watchTitle}>{title}</h1>
    <p className={s.watchIntro}>{intro}</p>
    <div className={s.watchUpdate}><span className={s.updateDot}/><span>Last updated: {fmt(date)}</span><span aria-hidden="true">·</span><span>Updated weekly · Mondays</span></div>
  </header>;
}

export function PaperWatch({ items, date, authorCoverage }: { items: PaperView[]; date: string; authorCoverage?: { linked_authors: number; author_rows: number; percent: number } }) {
  const [query, setQuery] = useState('');
  const [journal, setJournal] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  useEffect(() => setPage(1), [query, journal, status]);
  const availableJournals = Object.keys(journalNames);
  const availableStatuses = revisionStatuses.filter(value => items.some(p => p.status === value));
  const rrCounts = availableJournals.map(code => ({ code, count: items.filter(p => p.journal === code && p.status === 'R&R').length }));
  const totalRR = rrCounts.reduce((total, entry) => total + entry.count, 0);
  const maxRR = Math.max(1, ...rrCounts.map(entry => entry.count));
  const chooseChartJournal = (code: string) => {
    setJournal(journal === code && status === 'R&R' ? '' : code);
    setStatus('R&R');
  };
  const filtered = items.filter(p => revisionStatuses.includes(p.status) &&
    (!journal || p.journal === journal) && (!status || p.status === status) &&
    [p.title, ...p.authors, p.journal, fullJournalName(p.journal), p.status].join(' ').toLowerCase().includes(query.trim().toLowerCase()))
    .sort((a,b) => a.title.localeCompare(b.title));
  const currentPage = Math.min(page, Math.max(1, Math.ceil(filtered.length / 25)));
  return <main className={`${s.page} ${s.widePage}`}>
    <WatchHero title="Top 5 Finance R&R" intro="Working papers with publicly disclosed revise-and-resubmit decisions. Tracked through author research pages." date={date}/>
    {authorCoverage && <p className={s.directory}>{authorCoverage.linked_authors.toLocaleString()} of {authorCoverage.author_rows.toLocaleString()} author name groups publishing in the five leading finance journals have a linked personal site or institution profile ({authorCoverage.percent.toFixed(2)}%).</p>}
    <section className={s.chart} aria-labelledby="rr-chart-heading">
      <div className={s.chartHeading}><div><p className={s.chartKicker}>Journal distribution</p><h2 id="rr-chart-heading">R&amp;R papers by journal</h2></div><p className={s.chartTotal}><strong>{totalRR}</strong><span>R&amp;R papers</span></p></div>
      <p className={s.chartHint}>Select a journal to filter the paper list. Counts include R&amp;R decisions only.</p>
      <div className={s.chartRows} role="group" aria-label="Filter R&R papers by journal">
        {rrCounts.map(({ code, count }) => <button type="button" key={code} className={s.chartRow} aria-pressed={journal === code && status === 'R&R'} onClick={() => chooseChartJournal(code)} title={`Show ${count} R&R papers at ${fullJournalName(code)}`}>
          <span className={s.chartLabel}>{fullJournalName(code)}</span><span className={s.chartTrack}><span className={s.chartBar} style={{ width: `${count / maxRR * 100}%` }}/></span><strong className={s.chartValue}>{count}</strong>
        </button>)}
      </div>
    </section>
    <div className={s.filters}>
      <Search value={query} change={setQuery} placeholder="Search papers, authors or journals"/>
      <label className={s.filter}>Journal<select value={journal} onChange={e => setJournal(e.target.value)}><option value="">All journals</option>{availableJournals.map(code => <option key={code} value={code}>{fullJournalName(code)}</option>)}</select></label>
      <label className={s.filter}>Status<select value={status} onChange={e => setStatus(e.target.value)}><option value="">All statuses</option>{availableStatuses.map(value => <option key={value} value={value}>{value}</option>)}</select></label>
    </div>
    <p className={s.count} role="status" aria-live="polite">{filtered.length} papers</p>
    <div className={s.list}>{filtered.slice((currentPage-1)*25,currentPage*25).map(p =>
      <article className={s.item} key={p.id}>
        <div className={s.itemHeading}><h2>{p.paper_url ? <a href={p.paper_url} {...external}>{p.title}</a> : p.title}</h2><span className={`${s.status} ${s.paperStatus}`}>{fullJournalName(p.journal)} · {p.status}</span></div>
        <p className={s.authors}>{p.authors.join(' · ')}</p>
        {p.ssrn_url && <a className={s.link} href={p.ssrn_url} {...external}>SSRN</a>}
        {p.evidence_url && <a className={s.link} href={p.evidence_url} {...external}>Author source · checked {fmt(p.last_verified)}</a>}
        {p.verification_status === 'reference_only' && <p className={s.note}>Current status awaiting confirmation</p>}
      </article>
    )}</div>
    {!filtered.length && <p className={s.empty}>No papers found.</p>}
    <Pager total={filtered.length} page={currentPage} change={setPage}/>
  </main>;
}

export function PostdocWatch({ items, date }: { items: VacancyView[]; date: string }) {
  const [query, setQuery] = useState('');
  const [country, setCountry] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [today, setToday] = useState(date);
  useEffect(() => setPage(1), [query, country, statusFilter]);
  useEffect(() => { setToday(new Date().toLocaleDateString('en-CA', { timeZone: 'Europe/London' })); }, []);
  const effective = items.map(j => ({...j,status:j.deadline && j.deadline < today ? 'closed' : j.status}));
  const active = effective.filter(j => j.status !== 'closed');
  const countryCounts = [...new Set(active.map(j => j.country).filter(Boolean))]
    .map(name => ({ name, count: active.filter(j => j.country === name).length }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
  const maxCountryCount = Math.max(1, ...countryCounts.map(entry => entry.count));
  const availableCountries = [...new Set(items.map(j => j.country).filter(Boolean))].sort();
  const chooseChartCountry = (name: string) => {
    setCountry(country === name && statusFilter === 'active' ? '' : name);
    setStatusFilter('active');
  };
  const filtered = effective
    .filter(j => (!country || j.country === country) &&
      (!statusFilter || (statusFilter === 'active' ? j.status !== 'closed' : j.status === statusFilter)) &&
      [j.title,j.institution,j.country,j.city,...j.topics,j.status].join(' ').toLowerCase().includes(query.trim().toLowerCase()))
    .sort((a,b) => Number(a.status === 'closed') - Number(b.status === 'closed') ||
      (a.deadline || '9999').localeCompare(b.deadline || '9999') || a.institution.localeCompare(b.institution));
  const currentPage = Math.min(page, Math.max(1, Math.ceil(filtered.length / 25)));
  return <main className={`${s.page} ${s.widePage}`}>
    <WatchHero title="European Postdocs" intro="Postdoctoral opportunities in banking, corporate finance, labor economics and general economics. Built around Europe’s top 50 business schools in the FT ranking." date={date}/>
    <section className={s.chart} aria-labelledby="postdoc-chart-heading">
      <div className={s.chartHeading}><div><p className={s.chartKicker}>Country distribution</p><h2 id="postdoc-chart-heading">Active postdocs by country</h2></div><p className={s.chartTotal}><strong>{active.length}</strong><span>active or deadline unknown</span></p></div>
      <p className={s.chartHint}>Select a country to show its active and deadline-unknown positions. Closed positions remain available in the filters below.</p>
      <div className={`${s.chartRows} ${s.countryChartRows}`} role="group" aria-label="Filter active postdocs by country">
        {countryCounts.map(({ name, count }) => <button type="button" key={name} className={s.chartRow} aria-pressed={country === name && statusFilter === 'active'} onClick={() => chooseChartCountry(name)} title={`Show ${count} active or deadline-unknown positions in ${name}`}>
          <span className={s.chartLabel}>{name}</span><span className={s.chartTrack}><span className={s.chartBar} style={{ width: `${count / maxCountryCount * 100}%` }}/></span><strong className={s.chartValue}>{count}</strong>
        </button>)}
      </div>
    </section>
    <div className={s.filters}>
      <Search value={query} change={setQuery} placeholder="Search positions, institutions or fields"/>
      <label className={s.filter}>Country<select value={country} onChange={e => setCountry(e.target.value)}><option value="">All countries</option>{availableCountries.map(name => <option key={name} value={name}>{name}</option>)}</select></label>
      <label className={s.filter}>Status<select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}><option value="">All statuses</option><option value="active">Active &amp; uncertain</option><option value="open">Open only</option><option value="deadline unknown">Deadline unknown</option><option value="closed">Closed only</option></select></label>
    </div>
    <p className={s.count} role="status" aria-live="polite">{filtered.length} positions</p>
    <div className={s.list}>{filtered.slice((currentPage-1)*25,currentPage*25).map(j =>
      <article className={s.item} key={j.id}>
        <div className={s.itemHeading}><h2><a href={j.apply_url} {...external}>{j.title}</a></h2><span className={s.status}>{j.status}</span></div>
        <p className={s.authors}>{[j.institution,j.city,j.country].filter(Boolean).join(' · ')}</p>
        <p className={s.note}>{j.topics.join(' · ')} · Deadline: {fmt(j.deadline)}</p>
        <div className={s.details}>{j.duration && j.duration !== 'Not stated' && <span>{j.duration}</span>}{j.start && j.start !== 'Not stated' && <span>Start: {j.start}</span>}</div>
        <a className={s.link} href={j.apply_url} {...external}>{j.status === 'closed' ? 'Position details' : 'Application details'}</a>
      </article>
    )}</div>
    {!filtered.length && <p className={s.empty}>No positions found.</p>}
    <Pager total={filtered.length} page={currentPage} change={setPage}/>
  </main>;
}
