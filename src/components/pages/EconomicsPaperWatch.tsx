'use client';

import { useEffect, useState } from 'react';
import s from './Watchlists.module.css';
import t from './Top5RR.module.css';

export type EconomicsPaperView = {
  id: string; title: string; authors: string[]; authors_complete: boolean;
  journal: string; status: string; evidence_url: string; paper_url: string;
  ssrn_url: string; last_verified: string; field: string; keywords: string[];
};
type AuthorCoverage = { linked_authors: number; author_rows: number; percent: number };
const external = { target: '_blank', rel: 'noopener noreferrer' };
const journalNames: Record<string, string> = {
  AER: 'American Economic Review', ECTA: 'Econometrica', JPE: 'Journal of Political Economy',
  QJE: 'The Quarterly Journal of Economics', RESTUD: 'The Review of Economic Studies',
};
const dateLabel = (date: string) => /^\d{4}-\d{2}-\d{2}$/.test(date || '')
  ? new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(date + 'T00:00:00Z')) : '';

export default function EconomicsPaperWatch({ items, date, authorCoverage, sourceWindow }: { items: EconomicsPaperView[]; date: string; authorCoverage: AuthorCoverage; sourceWindow: { start: string; end: string } }) {
  const [query, setQuery] = useState('');
  const [journal, setJournal] = useState('');
  const [field, setField] = useState('');
  const [status, setStatus] = useState('');
  const [keyword, setKeyword] = useState('');
  const [view, setView] = useState<'list' | 'table'>('list');
  const [page, setPage] = useState(1);
  useEffect(() => setPage(1), [query, journal, field, status, keyword]);
  const fields = [...new Set(items.map(p => p.field))].sort();
  const strict = items.filter(p => p.status === 'R&R');
  const rejectCount = items.filter(p => p.status === 'Reject & Resubmit').length;
  const rrCounts = Object.keys(journalNames).map(code => ({ code, count: strict.filter(p => p.journal === code).length }));
  const maxRR = Math.max(1, ...rrCounts.map(entry => entry.count));
  const matches = (p: EconomicsPaperView, ignoreStatus = false, ignoreKeyword = false) =>
    (ignoreStatus || !status || p.status === status) && (!journal || p.journal === journal) && (!field || p.field === field) &&
    (ignoreKeyword || !keyword || p.keywords.includes(keyword)) &&
    [p.title, ...p.authors, p.field, ...p.keywords, p.journal, journalNames[p.journal], p.status].join(' ').toLowerCase().includes(query.trim().toLowerCase());
  const filtered = items.filter(p => matches(p)).sort((a, b) => a.title.localeCompare(b.title));
  const currentPage = Math.min(page, Math.max(1, Math.ceil(filtered.length / 25)));
  const shown = filtered.slice((currentPage - 1) * 25, currentPage * 25);
  const keywordCounts: Record<string, number> = {};
  strict.filter(p => matches(p, true, true)).forEach(p => p.keywords.forEach(value => { keywordCounts[value] = (keywordCounts[value] || 0) + 1; }));
  const rankedKeywords = Object.keys(keywordCounts).sort((a, b) => keywordCounts[b] - keywordCounts[a] || a.localeCompare(b)).slice(0, 8);
  if (keyword && keywordCounts[keyword] && !rankedKeywords.includes(keyword)) rankedKeywords[rankedKeywords.length - 1] = keyword;
  const clear = () => { setQuery(''); setJournal(''); setField(''); setStatus(''); setKeyword(''); setPage(1); };
  const sourceLink = (p: EconomicsPaperView) => <a className={s.link} href={p.evidence_url} {...external}>Author source{dateLabel(p.last_verified) && ` · checked ${dateLabel(p.last_verified)}`}</a>;
  const byline = (p: EconomicsPaperView) => <>{p.authors.join(' · ')}{!p.authors_complete && <small className={t.bylineNote}>Coauthor list under review</small>}</>;

  return <main className={`${s.page} ${s.widePage}`}>
    <header className={s.watchHero}>
      <p className={s.eyebrow}>Research watch · Tian Tao</p>
      <h1 className={s.watchTitle}>Top 5 Economics R&amp;R</h1>
      <p className={s.watchIntro}>Working papers with publicly disclosed revise-and-resubmit decisions. Tracked through author research pages.</p>
      <div className={s.watchUpdate}><span className={s.updateDot}/><span>Last updated: {dateLabel(date)}</span><span aria-hidden="true">·</span><span>Public author disclosures</span></div>
    </header>
    <p className={s.directory}>{authorCoverage.linked_authors.toLocaleString()} of {authorCoverage.author_rows.toLocaleString()} author name groups publishing in the five leading economics journals have a linked personal site or institution profile ({authorCoverage.percent.toFixed(2)}%).</p>
    <section className={s.chart} aria-labelledby="econ-rr-chart-heading">
      <div className={s.chartHeading}><div><p className={s.chartKicker}>Journal distribution</p><h2 id="econ-rr-chart-heading">R&amp;R papers by journal</h2></div><p className={s.chartTotal}><strong>{strict.length}</strong><span>R&amp;R papers</span></p></div>
      <p className={s.chartHint}>Select a journal to filter the paper list. Counts include R&amp;R decisions only.</p>
      <div className={s.chartRows} role="group" aria-label="Filter Economics R&R papers by journal">
        {rrCounts.map(({ code, count }) => <button type="button" key={code} className={s.chartRow} aria-pressed={journal === code && status === 'R&R'} onClick={() => { setJournal(journal === code && status === 'R&R' ? '' : code); setStatus('R&R'); }} title={`Show ${count} R&R papers at ${journalNames[code]}`}>
          <span className={s.chartLabel}>{journalNames[code]}</span><span className={s.chartTrack}><span className={s.chartBar} style={{ width: `${count / maxRR * 100}%` }}/></span><strong className={s.chartValue}>{count}</strong>
        </button>)}
      </div>
    </section>
    <section className={s.chart} aria-labelledby="econ-keyword-heading">
      <div className={s.chartHeading}><div><p className={s.chartKicker}>Research themes</p><h2 id="econ-keyword-heading">Keyword phrases</h2></div></div>
      <p className={s.chartHint}>Phrases in R&amp;R paper titles. Select a phrase to filter the paper list.</p>
      <div className={t.keywordGrid}>{rankedKeywords.map(value => <button type="button" className={t.keywordButton} key={value} data-keyword={value} aria-pressed={keyword === value} onClick={() => { setStatus('R&R'); setKeyword(keyword === value ? '' : value); }}><span>{value}</span><strong>{keywordCounts[value]}</strong></button>)}{!rankedKeywords.length && <p className={s.note}>No matching keyword phrases.</p>}</div>
    </section>
    <div className={`${s.filters} ${s.paperFilters}`}>
      <label className={s.search}><span className="sr-only">Search</span><input type="search" aria-label="Search" placeholder="Search papers, authors or journals" value={query} onChange={e => setQuery(e.target.value)}/></label>
      <label className={s.filter}>Journal<select value={journal} onChange={e => setJournal(e.target.value)}><option value="">All journals</option>{Object.keys(journalNames).map(code => <option key={code} value={code}>{journalNames[code]}</option>)}</select></label>
      <label className={s.filter}>Field<select value={field} onChange={e => setField(e.target.value)}><option value="">All fields</option>{fields.map(value => <option key={value} value={value}>{value}</option>)}</select></label>
      <label className={s.filter}>Status<select value={status} onChange={e => { setStatus(e.target.value); setKeyword(''); }}><option value="">All statuses</option><option value="R&R">R&amp;R</option><option value="Reject & Resubmit">Reject &amp; Resubmit</option></select></label>
    </div>
    <p className={s.fieldHint}>Fields use available topic tags and title keywords; papers may span multiple fields.</p>
    <div className={t.listControls}>
      <div><p className={t.resultCount} role="status" aria-live="polite">{filtered.length} papers</p>{keyword && <p className={t.keywordChoice}>Keyword: {keyword}</p>}</div>
      <div className={t.actions}><button className={t.clearButton} type="button" onClick={clear}>Clear filters</button><div className={t.view} role="group" aria-label="Paper display"><button className={t.viewButton} type="button" aria-pressed={view === 'list'} onClick={() => setView('list')}>List</button><button className={t.viewButton} type="button" aria-pressed={view === 'table'} onClick={() => setView('table')}>Table</button></div></div>
    </div>
    {view === 'list' ? <div className={s.list}>{shown.map(p => <article className={s.item} key={p.id}>
      <div className={s.itemHeading}><h2>{p.paper_url ? <a href={p.paper_url} {...external}>{p.title}</a> : p.title}</h2><span className={`${s.status} ${s.paperStatus}`}>{journalNames[p.journal]} · {p.status}</span></div>
      <p className={s.authors}>{byline(p)}</p>
      <div className={t.paperTopics}><span>{p.field}</span><span>{p.keywords.join(' / ')}</span></div>
      <div className={t.sourceLinks}>{p.ssrn_url && <a className={s.link} href={p.ssrn_url} {...external}>SSRN</a>}{sourceLink(p)}</div>
    </article>)}</div> : <div className={t.tableWrap}><table className={t.paperTable}><thead><tr><th scope="col">Paper / source</th><th scope="col">Authors</th><th scope="col">Journal</th><th scope="col">Status</th></tr></thead><tbody>{shown.map(p => <tr key={p.id}><td>{p.paper_url ? <a href={p.paper_url} {...external}>{p.title}</a> : p.title}<br/>{sourceLink(p)}</td><td>{byline(p)}</td><td>{journalNames[p.journal]}</td><td>{p.status}</td></tr>)}</tbody></table></div>}
    {!filtered.length && <p className={s.empty}>No papers found.</p>}
    {filtered.length > 25 && <nav className={s.pager} aria-label="Results pagination"><button disabled={currentPage <= 1} onClick={() => setPage(currentPage - 1)}>Previous</button><span>{currentPage} / {Math.ceil(filtered.length / 25)}</span><button disabled={currentPage >= Math.ceil(filtered.length / 25)} onClick={() => setPage(currentPage + 1)}>Next</button></nav>}
    <p className={t.footnote}>{strict.length} public revise-and-resubmit disclosures and {rejectCount} reject-and-resubmit disclosures, counted separately. Author discovery window: {dateLabel(sourceWindow.start)}–{dateLabel(sourceWindow.end)}. Sources retain their original visit dates; unread sources and unresolved cases are outside the paper counts. A linked webpage does not establish successful R&amp;R text reading.</p>
  </main>;
}
