import { BugItem, CoverageMetrics, LLMMetrics, LogEntry, PRItem, Repository, Status, Task } from './types';

export const REPOSITORIES: Repository[] = [
  { id: 'repo-1', name: 'studio-ai-backend', hasReadme: true, hasSpec: true, branch: 'main', isSecure: true },
  { id: 'repo-2', name: 'studio-ai-frontend', hasReadme: true, hasSpec: false, branch: 'develop', isSecure: false },
  { id: 'repo-3', name: 'automation-scripts', hasReadme: false, hasSpec: false, branch: 'feature/auth', isSecure: true },
  { id: 'repo-4', name: 'Amitro123/automation-service', hasReadme: true, hasSpec: true, branch: 'main', isSecure: true },
];

export const MOCK_TASKS: Task[] = [
  { id: 't1', title: 'Implement JWT Authentication', status: Status.Completed },
  { id: 't2', title: 'Setup Mutation Testing (mutmut)', status: Status.InProgress },
  { id: 't3', title: 'Create Mermaid Diagram Generator', status: Status.InProgress },
  { id: 't4', title: 'Integrate Gemini 2.5 Flash', status: Status.Pending },
  { id: 't5', title: 'Finalize Security Audit', status: Status.Pending },
];

export const MOCK_BUGS: BugItem[] = [
  { id: 'BUG-101', title: 'Memory leak in session storage', severity: 'Critical', status: 'Open', createdAt: '2023-10-27T10:00:00Z' },
  { id: 'BUG-102', title: 'Webhook timeout on large payloads', severity: 'Major', status: 'In Progress', createdAt: '2023-10-26T14:30:00Z' },
  { id: 'BUG-103', title: 'Typo in README', severity: 'Minor', status: 'Open', createdAt: '2023-10-25T09:15:00Z' },
];

export const MOCK_PRS: PRItem[] = [
  {
    id: 45,
    title: 'feat: Add Tailwind Support',
    author: 'dev_alex',
    status: 'Merged',
    checksPassed: true,
    url: 'https://github.com/Amitro123/automation-service/pull/45',
    createdAt: '2023-10-28T11:20:00Z',
    automationStatus: [
      { name: 'Code Review', status: 'success', details: 'No issues found' },
      { name: 'Spec Update', status: 'success', details: 'Updated spec.md' }
    ]
  },
  {
    id: 46,
    title: 'fix: API Rate Limiting',
    author: 'qa_sarah',
    status: 'Open',
    checksPassed: false,
    url: 'https://github.com/Amitro123/automation-service/pull/46',
    createdAt: '2023-10-29T09:45:00Z',
    automationStatus: [
      { name: 'Code Review', status: 'failed', details: 'Critical bugs found' },
      { name: 'Spec Update', status: 'pending' }
    ]
  },
  {
    id: 47,
    title: 'chore: Update dependencies',
    author: 'bot_renovate',
    status: 'Closed',
    checksPassed: true,
    url: 'https://github.com/Amitro123/automation-service/pull/47',
    createdAt: '2023-10-25T16:00:00Z',
    automationStatus: []
  },
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
  mutationStatus: 'success',
  mutationReason: 'All tests passed'
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