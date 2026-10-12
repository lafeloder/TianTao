export interface Eligibility {
  author: string;
  doi: string;
  journal: string;
  title: string;
  published: string;
}

export interface Paper {
  id: string;
  title: string;
  authors: string[];
  journal: string;
  status: string;
  evidence_url: string;
  paper_url: string;
  ssrn_url?: string;
  source_author: string;
  first_seen: string;
  last_verified: string;
  source_updated: string;
  topics: string[];
  evidence_excerpt: string;
  eligibility: Eligibility | null;
  verification?: string;
  verification_status?: string;
  reference_url?: string;
  reference_date?: string;
  reference_checked_on?: string;
  reference_ids?: string[];
  source_scope?: string;
  authors_note?: string;
  status_original?: string;
  primary_source_url?: string;
  eligibility_status?: string;
}

export interface Vacancy {
  id: string;
  title: string;
  institution: string;
  country: string;
  city: string;
  rank: number | null;
  scope: string;
  topics: string[];
  fit: string;
  deadline: string;
  status: string;
  duration: string;
  start: string;
  salary: string;
  source_url: string;
  apply_url: string;
  source_type: string;
  last_verified: string;
  notes: string;
  source_reports?: { name: string; url: string; checked_on: string; reported_status?: string }[];
  reference_ids?: string[];
  verification?: string;
  search_status?: string;
  deadline_at?: string;
  first_seen?: string;
}

export interface CoverageSource {
  name: string;
  url: string;
  total_scanned: number;
  in_scope: number;
  matched: number;
  missing: number;
  checked_on: string;
  status: string;
  note?: string;
}

export interface School {
  id: string;
  rank: number;
  name: string;
  country: string;
  career_url: string;
  feed_status: string;
  last_attempted?: string;
  last_fetched?: string;
}

export interface WatchMeta {
  last_run: string;
  publication_window_start: string;
  publication_window_end: string;
  articles: number;
  author_name_groups: number;
  author_identity_records: number;
  approved_homepages: number;
  homepages_scanned_this_run: number;
  schools: number;
  feeds_fetched: number;
  review_queue: number;
  coverage_note: string;
  linkedin_note: string;
  journals: Record<string, { status: string; articles: number; checked_on: string | null }>;
  benchmark_sources?: { papers: CoverageSource[]; jobs: CoverageSource[] };
  paper_sources_checked?: number;
  reference_paper_rows?: number;
  job_counts?: { active: number; historical: number; uncertain: number; total: number };
}
