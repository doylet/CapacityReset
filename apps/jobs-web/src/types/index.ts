export interface Cluster {
  cluster_id: number;
  cluster_name: string;
  cluster_keywords: string[];
  cluster_size: number;
}

export interface Job {
  job_posting_id: string;
  job_title: string;
  company_name: string;
  job_location: string;
  job_summary: string;
  job_posted_date: string;
  skills_count?: number;
  cluster?: Cluster;
}

export interface JobFilters {
  location: string;
  skill_name: string;
  cluster_id: string;
}
