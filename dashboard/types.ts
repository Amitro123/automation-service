export interface AutomationTaskStatus {
  name: string;
  status: string; // success, failed, skipped, pending
  details?: string;
}

export interface PRItem {
  id: number;
  title: string;
  author: string;
  status: string;
  checksPassed: boolean;
  url: string;
  createdAt: string;
  automationStatus: AutomationTaskStatus[];
  runId?: string;
}

export interface BugItem {
  id: string;
  title: string;
  severity: string;
  status: string;
  createdAt: string;
}

export interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR';
  message: string;
}

export interface Task {
  id: string;
  title: string;
  status: Status;
}

export enum Status {
  Pending = 'Pending',
  InProgress = 'InProgress',
  Completed = 'Completed',
  Failed = 'Failed',
}

export interface Repository {
  id: string;
  name: string;
  branch: string;
  hasReadme: boolean;
  hasSpec: boolean;
  isSecure: boolean;
}

export interface CoverageMetrics {
  total: number;
  uncoveredLines: number;
  mutationScore: number;
  mutationStatus: string;
  mutationReason?: string;
}

export interface LLMMetrics {
  tokensUsed: number;
  estimatedCost: number;
  efficiencyScore: number;
  sessionMemoryUsage: number;
  totalRuns: number;
}

export interface DashboardMetrics {
  coverage: CoverageMetrics;
  llm: LLMMetrics;
  tasks: Task[];
  bugs: BugItem[];
  prs: PRItem[];
  logs: LogEntry[];
  security: {
    isSecure: boolean;
    vulnerabilities: number;
    lastScan: string;
  };
  projectProgress: number;
}

export interface RunHistoryItem {
  id: string;
  commit_sha: string;
  branch: string;
  status: 'completed' | 'running' | 'failed' | 'pending' | 'skipped';
  start_time: string;
  end_time?: string;
  summary?: string;
  tasks: Record<string, unknown>;
  metrics: Record<string, number>;
  trigger_type?: 'pr_opened' | 'pr_synchronized' | 'pr_reopened' | 'push_with_pr' | 'push_without_pr';
  run_type?: 'full_automation' | 'partial' | 'skipped_trivial_change' | 'skipped_docs_only' | 'lightweight_only';
  pr_number?: number;
  skip_reason?: string;
}