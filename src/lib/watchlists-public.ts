import type { Paper, Vacancy } from '@/types/watchlists';

export type PaperView = Pick<Paper, 'id' | 'title' | 'authors' | 'journal' | 'status' | 'paper_url' | 'evidence_url' | 'last_verified' | 'verification_status'> & { ssrn_url?: string };
export type VacancyView = Pick<Vacancy, 'id' | 'title' | 'institution' | 'city' | 'country' | 'topics' | 'deadline' | 'status' | 'apply_url' | 'duration' | 'start'>;

export function paperView(p: Paper & { ssrn_url?: string }): PaperView {
  return { id:p.id,title:p.title,authors:p.authors,journal:p.journal,status:p.status,
    paper_url:p.paper_url,evidence_url:p.evidence_url,last_verified:p.last_verified,
    ssrn_url:p.ssrn_url || (/ssrn\.com\/.*abstract_id=\d+/.test(p.paper_url) ? p.paper_url : ''),verification_status:p.verification_status };
}
export function vacancyView(j: Vacancy): VacancyView {
  return { id:j.id,title:j.title,institution:j.institution,city:j.city,country:j.country,
    topics:j.topics,deadline:j.deadline,status:j.status,apply_url:j.apply_url,duration:j.duration,start:j.start };
}
