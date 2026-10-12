import type { Metadata } from 'next';
import { PaperWatch } from '@/components/pages/ResearchWatch';
import rr from '../../../content/watchlists/rr.json';
import meta from '../../../content/watchlists/meta.json';
import type { Paper, WatchMeta } from '@/types/watchlists';

export const metadata: Metadata = { title: 'Top 5 Finance R&R', description: 'Author-disclosed R&R working papers at JF, JFE, RFS, RF and JFQA, with source evidence and coverage.' };
export default function Page() { return <PaperWatch items={rr.items as Paper[]} meta={meta as WatchMeta}/>; }
