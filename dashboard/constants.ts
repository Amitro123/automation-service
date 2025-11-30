import { Bug, CoverageMetrics, LLMMetrics, LogEntry, PullRequest, Repository, Status, Task } from './types';

export const REPOSITORIES: Repository[] = [
  { id: 'repo-1', name: 'studio-ai-backend', hasReadme: true, hasSpec: true, branch: 'main', isSecure: true },
  { id: 'repo-2', name: 'studio-ai-frontend', hasReadme: true, hasSpec: false, branch: 'develop', isSecure: false },
  { id: 'repo-3', name: 'automation-scripts', hasReadme: false, hasSpec: false, branch: 'feature/auth', isSecure: true },
];

export const MOCK_TASKS: Task[] = [
  { id: 't1', title: 'Implement JWT Authentication', status: Status.Completed },
  { id: 't2', title: 'Setup Mutation Testing (mutmut)', status: Status.InProgress },
  { id: 't3', title: 'Create Mermaid Diagram Generator', status: Status.InProgress },
  { id: 't4', title: 'Integrate Gemini 2.5 Flash', status: Status.Pending },
  { id: 't5', title: 'Finalize Security Audit', status: Status.Pending },
];

export const MOCK_BUGS: Bug[] = [
  { id: 'BUG-101', title: 'Memory leak in session storage', severity: 'Critical', status: 'Open', createdAt: '2h ago' },
  { id: 'BUG-102', title: 'Webhook timeout on large payloads', severity: 'Major', status: 'In Progress', createdAt: '5h ago' },
  { id: 'BUG-103', title: 'Typo in README', severity: 'Minor', status: 'Open', createdAt: '1d ago' },
];

export const MOCK_PRS: PullRequest[] = [
  { id: 45, title: 'feat: Add Tailwind Support', author: 'dev_alex', status: 'Merged', checksPassed: true },
  { id: 46, title: 'fix: API Rate Limiting', author: 'qa_sarah', status: 'Open', checksPassed: false },
  { id: 47, title: 'chore: Update dependencies', author: 'bot_renovate', status: 'Closed', checksPassed: true },
];

export const INITIAL_METRICS: LLMMetrics = {
  tokensUsed: 145020,
  estimatedCost: 1.45,
  efficiencyScore: 88,
  sessionMemoryUsage: 42,
};

export const COVERAGE_DATA: CoverageMetrics = {
  total: 78,
  uncoveredLines: 124,
  mutationScore: 65,
};

export const INITIAL_LOGS: LogEntry[] = [
  { timestamp: '10:00:01', level: 'INFO', message: 'StudioAI Backend Service Started' },
  { timestamp: '10:00:05', level: 'INFO', message: 'Connected to GitHub Webhook' },
  { timestamp: '10:05:22', level: 'WARN', message: 'High latency detected in Orchestrator' },
  { timestamp: '10:15:00', level: 'INFO', message: 'Scheduled Spec Update triggered' },
];

export const ARCHITECTURE_DIAGRAM = `
graph TD
  subgraph Webhook_Server
    A[Flask Webhook Server]
  end

  subgraph Orchestrator
    B1[Code Reviewer]
    B2[README Updater]
    B3[Spec Updater]
    B4[Code Review Updater]
  end

  A -->|Push Event| Orchestrator
  B1 --> GitHub_API[GitHub API]
  B2 --> GitHub_API
  B3 --> GitHub_API
  B4 --> CodeReviewMD[code_review.md]

  subgraph LLM
    Gemini[Gemini LLM]
  end

  B1 --> Gemini
  B2 --> Gemini
  B3 --> Gemini
  B4 --> SessionMemory[Session Memory]

  classDef implemented fill:#28a745,stroke:#333,stroke-width:2px,color:white;
  classDef inProgress fill:#ffc107,stroke:#333,stroke-width:2px,color:black;
  classDef pending fill:#fff,stroke:#333,stroke-width:1px,stroke-dasharray: 5 5;

  class A,B1,GitHub_API implemented;
  class B2,B3,Gemini inProgress;
  class B4,SessionMemory pending;
`;