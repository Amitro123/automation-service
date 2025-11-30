export enum Status {
  Completed = 'Completed',
  InProgress = 'InProgress',
  Pending = 'Pending',
  Failed = 'Failed',
}

export interface Repository {
  id: string;
  name: string;
  hasReadme: boolean;
  hasSpec: boolean;
  branch: string;
  isSecure: boolean;
}

export interface Task {
  id: string;
  title: string;
  status: Status;
}

export interface Bug {
  id: string;
  title: string;
  severity: 'Critical' | 'Major' | 'Minor';
  status: 'Open' | 'In Progress' | 'Closed';
  createdAt: string;
}

export interface PullRequest {
  id: number;
  title: string;
  author: string;
  status: 'Merged' | 'Open' | 'Closed';
  checksPassed: boolean;
}

export interface LLMMetrics {
  tokensUsed: number;
  estimatedCost: number;
  efficiencyScore: number; // 0-100
  sessionMemoryUsage: number; // percentage
}

export interface CoverageMetrics {
  total: number; // percentage
  uncoveredLines: number;
  mutationScore: number; // percentage
}

export interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR';
  message: string;
}