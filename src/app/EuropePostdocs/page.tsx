import type { Metadata } from 'next';
import { PostdocWatch } from '@/components/pages/ResearchWatch';
import jobs from '../../../content/watchlists/postdocs.json';
import meta from '../../../content/watchlists/meta.json';
import type { Vacancy } from '@/types/watchlists';
import { vacancyView } from '@/lib/watchlists-public';

export const metadata: Metadata = { title: 'European Postdocs', description: 'Search European postdoctoral positions in finance and economics.' };
export default function Page() { return <PostdocWatch items={(jobs.items as Vacancy[]).map(vacancyView)} date={meta.last_run}/>; }
