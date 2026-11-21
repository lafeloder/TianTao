'use client';

import { useEffect, useState, type KeyboardEvent, type ReactNode } from 'react';
import s from './Top5RR.module.css';

type Discipline = 'finance' | 'economics';

export default function Top5RRWatch({ finance, economics }: { finance: ReactNode; economics: ReactNode }) {
  const [discipline, setDiscipline] = useState<Discipline>('finance');

  useEffect(() => {
    const restore = () => setDiscipline(new URL(window.location.href).searchParams.get('discipline') === 'economics' ? 'economics' : 'finance');
    restore();
    window.addEventListener('popstate', restore);
    return () => window.removeEventListener('popstate', restore);
  }, []);

  const choose = (next: Discipline) => {
    setDiscipline(next);
    const url = new URL(window.location.href);
    if (next === 'economics') url.searchParams.set('discipline', next);
    else url.searchParams.delete('discipline');
    window.history.replaceState(window.history.state, '', url);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const next: Discipline = event.key === 'Home' ? 'finance' : event.key === 'End' ? 'economics' : discipline === 'finance' ? 'economics' : 'finance';
    choose(next);
    event.currentTarget.parentElement?.querySelector<HTMLButtonElement>(`[data-rr-tab="${next}"]`)?.focus();
  };

  return <div className={s.shell}>
    <div className={s.tabsWrap}>
      <div className={s.tabs} role="tablist" aria-label="R&R discipline">
        <button type="button" role="tab" id="finance-rr-tab" data-rr-tab="finance" aria-controls="finance-rr-panel" aria-selected={discipline === 'finance'} tabIndex={discipline === 'finance' ? 0 : -1} onClick={() => choose('finance')} onKeyDown={onKeyDown}>Finance R&amp;R</button>
        <button type="button" role="tab" id="economics-rr-tab" data-rr-tab="economics" aria-controls="economics-rr-panel" aria-selected={discipline === 'economics'} tabIndex={discipline === 'economics' ? 0 : -1} onClick={() => choose('economics')} onKeyDown={onKeyDown}>Economics R&amp;R</button>
      </div>
    </div>
    <div id="finance-rr-panel" role="tabpanel" aria-labelledby="finance-rr-tab" hidden={discipline !== 'finance'} className={s.panel}>{finance}</div>
    <div id="economics-rr-panel" role="tabpanel" aria-labelledby="economics-rr-tab" hidden={discipline !== 'economics'} className={s.panel}>{economics}</div>
  </div>;
}
