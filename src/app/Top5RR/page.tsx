import type { Metadata } from 'next';
import { PaperWatch } from '@/components/pages/ResearchWatch';
import rr from '../../../content/watchlists/rr.json';
import meta from '../../../content/watchlists/meta.json';
import type { Paper } from '@/types/watchlists';
import { paperView } from '@/lib/watchlists-public';

export const metadata: Metadata = { title: 'R&R Papers', description: 'Search working papers and journal revision decisions.' };
export default function Page() { return <PaperWatch items={(rr.items as Paper[]).filter(p => p.source_scope === 'top5' && ['R&R', 'Reject & Resubmit', 'Invited revision'].includes(p.status)).map(paperView)} date={meta.last_run} authorCoverage={meta.author_homepage_coverage}/>; }
