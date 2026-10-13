import type { Metadata } from 'next';
import { PaperWatch } from '@/components/pages/ResearchWatch';
import rr from '../../../content/watchlists/rr.json';
import meta from '../../../content/watchlists/meta.json';
import type { Paper } from '@/types/watchlists';
import { paperView } from '@/lib/watchlists-public';

export const metadata: Metadata = { title: 'Top 5 Finance R&R', description: 'Author-disclosed revise-and-resubmit working papers at six journals.' };
export default function Page() { return <PaperWatch items={(rr.items as Paper[]).filter(p => p.source_scope === 'top5' && ['R&R', 'Reject & Resubmit', 'Invited revision'].includes(p.status)).map(paperView)} date={meta.last_run} authorCoverage={meta.author_homepage_coverage} msAuthorAudit={(meta as typeof meta & { ms_author_audit?: { author_name_groups: number; linked_homepages: number; verified_homepages: number; profile_linked_homepages: number; homepage_percent: number } }).ms_author_audit}/>; }
