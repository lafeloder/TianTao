import type { Metadata } from 'next';
import { PostdocWatch } from '@/components/pages/ResearchWatch';
import jobs from '../../../content/watchlists/postdocs.json';
import schools from '../../../content/watchlists/schools.json';
import meta from '../../../content/watchlists/meta.json';
import type { Vacancy, School, WatchMeta } from '@/types/watchlists';

export const metadata: Metadata = { title: 'European Postdocs', description: 'European postdoctoral opportunities in banking, corporate finance, labor and economics, with FT school scope and deadlines.' };
export default function Page() { return <PostdocWatch items={jobs.items as Vacancy[]} schools={schools.schools as School[]} meta={meta as WatchMeta} rankingUrl={schools.ranking_url}/>; }
