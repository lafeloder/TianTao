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
  source_author: string;
  first_seen: string;
  last_verified: string;
  source_updated: string;
  topics: string[];
  evidence_excerpt: string;
  eligibility: Eligibility | null;
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
}
