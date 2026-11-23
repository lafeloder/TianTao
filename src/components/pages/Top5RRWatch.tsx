'use client';

import { useEffect, useState, type KeyboardEvent, type ReactNode } from 'react';
import s from './Top5RR.module.css';

type Discipline = 'finance' | 'economics' | 'accounting' | 'management';
const disciplines: Discipline[] = ['finance', 'economics', 'accounting', 'management'];

export default function Top5RRWatch({ finance, economics, accounting, management }: { finance: ReactNode; economics: ReactNode; accounting: ReactNode; management: ReactNode }) {
  const [discipline, setDiscipline] = useState<Discipline>('finance');

  useEffect(() => {
    const restore = () => {
      const selected = new URL(window.location.href).searchParams.get('discipline') as Discipline;
      setDiscipline(disciplines.includes(selected) ? selected : 'finance');
    };
    restore();
    window.addEventListener('popstate', restore);
    return () => window.removeEventListener('popstate', restore);
  }, []);

  const choose = (next: Discipline) => {
    setDiscipline(next);
    const url = new URL(window.location.href);
    if (next !== 'finance') url.searchParams.set('discipline', next);
    else url.searchParams.delete('discipline');
    window.history.replaceState(window.history.state, '', url);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const offset = event.key === 'ArrowLeft' ? -1 : 1;
    const next: Discipline = event.key === 'Home' ? 'finance' : event.key === 'End' ? 'management' : disciplines[(disciplines.indexOf(discipline) + offset + disciplines.length) % disciplines.length];
    choose(next);
    event.currentTarget.parentElement?.querySelector<HTMLButtonElement>(`[data-rr-tab="${next}"]`)?.focus();
  };

  return <div className={s.shell}>
    <div className={s.tabsWrap}>
      <div className={s.tabs} style={{ overflowX: 'auto', whiteSpace: 'nowrap' }} role="tablist" aria-label="R&R discipline">
        <button type="button" role="tab" id="finance-rr-tab" data-rr-tab="finance" aria-controls="finance-rr-panel" aria-selected={discipline === 'finance'} tabIndex={discipline === 'finance' ? 0 : -1} onClick={() => choose('finance')} onKeyDown={onKeyDown}>Finance R&amp;R</button>
        <button type="button" role="tab" id="economics-rr-tab" data-rr-tab="economics" aria-controls="economics-rr-panel" aria-selected={discipline === 'economics'} tabIndex={discipline === 'economics' ? 0 : -1} onClick={() => choose('economics')} onKeyDown={onKeyDown}>Economics R&amp;R</button>
        <button type="button" role="tab" id="accounting-rr-tab" data-rr-tab="accounting" aria-controls="accounting-rr-panel" aria-selected={discipline === 'accounting'} tabIndex={discipline === 'accounting' ? 0 : -1} onClick={() => choose('accounting')} onKeyDown={onKeyDown}>Accounting R&amp;R</button>
        <button type="button" role="tab" id="management-rr-tab" data-rr-tab="management" aria-controls="management-rr-panel" aria-selected={discipline === 'management'} tabIndex={discipline === 'management' ? 0 : -1} onClick={() => choose('management')} onKeyDown={onKeyDown}>Management R&amp;R</button>
      </div>
    </div>
    <div id="finance-rr-panel" role="tabpanel" aria-labelledby="finance-rr-tab" hidden={discipline !== 'finance'} className={s.panel}>{finance}</div>
    <div id="economics-rr-panel" role="tabpanel" aria-labelledby="economics-rr-tab" hidden={discipline !== 'economics'} className={s.panel}>{economics}</div>
    <div id="accounting-rr-panel" role="tabpanel" aria-labelledby="accounting-rr-tab" hidden={discipline !== 'accounting'} className={s.panel}>{accounting}</div>
    <div id="management-rr-panel" role="tabpanel" aria-labelledby="management-rr-tab" hidden={discipline !== 'management'} className={s.panel}>{management}</div>
  </div>;
}
