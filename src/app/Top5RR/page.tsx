import { getPageMetadata } from '@/lib/seo';
import { PaperWatch } from '@/components/pages/ResearchWatch';
import rr from '../../../content/watchlists/rr.json';
import meta from '../../../content/watchlists/meta.json';
import type { Paper } from '@/types/watchlists';
import { paperView } from '@/lib/watchlists-public';
import Top5RRWatch from '@/components/pages/Top5RRWatch';
import EconomicsPaperWatch, { type EconomicsPaperView } from '@/components/pages/EconomicsPaperWatch';
import economics from '../../../content/watchlists/economics-rr.json';

export const metadata = getPageMetadata('Top5RR', 'Top 5 R&R', 'Author-disclosed revise-and-resubmit working papers in finance and economics.');
export default function Page() {
  const finance = <PaperWatch items={(rr.items as Paper[]).filter(p => p.source_scope === 'top5' && ['R&R', 'Reject & Resubmit', 'Invited revision'].includes(p.status)).map(paperView)} date={meta.rr_last_run || meta.last_run} authorCoverage={meta.finance_top5_author_homepage_coverage}/>;
  const economicsItems: EconomicsPaperView[] = economics.items.filter(p => ['R&R', 'Reject & Resubmit'].includes(p.status)).map(p => ({ id:p.id,title:p.title,authors:p.authors,authors_complete:p.authors_complete,journal:p.journal,status:p.status,evidence_url:p.evidence_url,paper_url:p.paper_url,ssrn_url:p.ssrn_url,last_verified:p.last_verified,field:p.field,keywords:p.keywords }));
  const economicsView = <EconomicsPaperWatch items={economicsItems} date={economics.updated_on} authorCoverage={economics.author_homepage_coverage} sourceWindow={economics.author_discovery_window}/>;
  return <Top5RRWatch finance={finance} economics={economicsView}/>;
}
