import { getPageMetadata } from '@/lib/seo';
import { PaperWatch } from '@/components/pages/ResearchWatch';
import rr from '../../../content/watchlists/rr.json';
import meta from '../../../content/watchlists/meta.json';
import type { Paper } from '@/types/watchlists';
import { paperView } from '@/lib/watchlists-public';

export const metadata = getPageMetadata('Top5RR', 'Top 5 Finance R&R', 'Author-disclosed revise-and-resubmit working papers at six journals.');
export default function Page() { return <PaperWatch items={(rr.items as Paper[]).filter(p => p.source_scope === 'top5' && ['R&R', 'Reject & Resubmit', 'Invited revision'].includes(p.status)).map(paperView)} date={meta.rr_last_run || meta.last_run} authorCoverage={meta.finance_top5_author_homepage_coverage}/>; }
