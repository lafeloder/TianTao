'use client';

import { useEffect, useState } from 'react';
import type { PaperView, VacancyView } from '@/lib/watchlists-public';
import s from './Watchlists.module.css';

const external = { target: '_blank', rel: 'noopener noreferrer' };
const revisionStatuses = ['R&R', 'Reject & Resubmit', 'Invited revision'];
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
function Heading({ title, date }: { title: string; date: string }) {
  return <header className={s.heading}><h1>{title}</h1><p>Updated {fmt(date)}</p></header>;
}

export function PaperWatch({ items, date, authorCoverage }: { items: PaperView[]; date: string; authorCoverage?: { linked_authors: number; author_rows: number; percent: number } }) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  useEffect(() => setPage(1), [query]);
  const filtered = items.filter(p => revisionStatuses.includes(p.status) &&
    [p.title, ...p.authors, p.journal, p.status].join(' ').toLowerCase().includes(query.trim().toLowerCase()))
    .sort((a,b) => a.title.localeCompare(b.title));
  const currentPage = Math.min(page, Math.max(1, Math.ceil(filtered.length / 25)));
  return <main className={s.page}>
    <Heading title="R&R Papers" date={date}/>
    {authorCoverage && <p className={s.directory}>{authorCoverage.linked_authors.toLocaleString()} of {authorCoverage.author_rows.toLocaleString()} Top 5 authors have a linked personal site or institution profile ({authorCoverage.percent.toFixed(2)}%). <a href="/TianTao/watchlists/Top5_Authors_Websites_RR.xlsx">Download author and R&R workbook</a></p>}
    <Search value={query} change={setQuery} placeholder="Search papers, authors or journals"/>
    <p className={s.count} role="status" aria-live="polite">{filtered.length} papers</p>
    <div className={s.list}>{filtered.slice((currentPage-1)*25,currentPage*25).map(p =>
      <article className={s.item} key={p.id}>
        <div className={s.itemHeading}><h2>{p.paper_url ? <a href={p.paper_url} {...external}>{p.title}</a> : p.title}</h2><span className={s.status}>{p.journal} · {p.status}</span></div>
        <p className={s.authors}>{p.authors.join(' · ')}</p>
        {p.ssrn_url && <a className={s.link} href={p.ssrn_url} {...external}>SSRN</a>}
        {p.verification_status === 'reference_only' && <p className={s.note}>Current status awaiting confirmation</p>}
      </article>
    )}</div>
    {!filtered.length && <p className={s.empty}>No papers found.</p>}
    <Pager total={filtered.length} page={currentPage} change={setPage}/>
  </main>;
}

export function PostdocWatch({ items, date }: { items: VacancyView[]; date: string }) {
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [today, setToday] = useState(date);
  useEffect(() => setPage(1), [query]);
  useEffect(() => { setToday(new Date().toISOString().slice(0,10)); }, []);
  const filtered = items.map(j => ({...j,status:j.deadline && j.deadline < today ? 'closed' : j.status}))
    .filter(j => [j.title,j.institution,j.country,j.city,...j.topics,j.status].join(' ').toLowerCase().includes(query.trim().toLowerCase()))
    .sort((a,b) => Number(a.status === 'closed') - Number(b.status === 'closed') ||
      (a.deadline || '9999').localeCompare(b.deadline || '9999') || a.institution.localeCompare(b.institution));
  const currentPage = Math.min(page, Math.max(1, Math.ceil(filtered.length / 25)));
  return <main className={s.page}>
    <Heading title="European Postdocs" date={date}/>
    <Search value={query} change={setQuery} placeholder="Search positions, institutions or fields"/>
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
