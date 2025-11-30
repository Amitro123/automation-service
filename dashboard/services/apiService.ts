// API Service for connecting to automation-service backend
const API_BASE_URL = 'http://localhost:8080/api';

export interface DashboardMetrics {
  coverage: {
    total: number;
    uncoveredLines: number;
    mutationScore: number;
  };
  llm: {
    tokensUsed: number;
    estimatedCost: number;
    efficiencyScore: number;
    sessionMemoryUsage: number;
  };
  tasks: Array<{
    id: string;
    title: string;
    status: string;
  }>;
  bugs: Array<{
    id: string;
    title: string;
    severity: string;
    status: string;
    createdAt: string;
  }>;
  prs: Array<{
    id: number;
    title: string;
    author: string;
    status: string;
    checksPassed: boolean;
  }>;
  logs: Array<{
    timestamp: string;
    level: string;
    message: string;
  }>;
  security: {
    isSecure: boolean;
    vulnerabilities: number;
    lastScan: string;
  };
}

export async function fetchDashboardMetrics(): Promise<DashboardMetrics> {
  try {
    const response = await fetch(`${API_BASE_URL}/metrics`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch dashboard metrics:', error);
    // Return mock data as fallback
    return getMockMetrics();
  }
}

export async function fetchLogs(limit: number = 50): Promise<Array<{timestamp: string; level: string; message: string}>> {
  try {
    const response = await fetch(`${API_BASE_URL}/logs?limit=${limit}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch logs:', error);
    return [];
  }
}

export async function fetchRepositoryStatus(repoName: string) {
  try {
    const response = await fetch(`${API_BASE_URL}/repository/${repoName}/status`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch repository status:', error);
    return null;
  }
}

// Mock data fallback
function getMockMetrics(): DashboardMetrics {
  return {
    coverage: {
      total: 78,
      uncoveredLines: 124,
      mutationScore: 65,
    },
    llm: {
      tokensUsed: 145020,
      estimatedCost: 1.45,
      efficiencyScore: 88,
      sessionMemoryUsage: 42,
    },
    tasks: [
      { id: 't1', title: 'Implement JWT Authentication', status: 'Completed' },
      { id: 't2', title: 'Setup Mutation Testing (mutmut)', status: 'InProgress' },
      { id: 't3', title: 'Create Mermaid Diagram Generator', status: 'InProgress' },
      { id: 't4', title: 'Integrate Gemini 2.5 Flash', status: 'Pending' },
      { id: 't5', title: 'Finalize Security Audit', status: 'Pending' },
    ],
    bugs: [
      { id: 'BUG-101', title: 'Memory leak in session storage', severity: 'Critical', status: 'Open', createdAt: '2h ago' },
      { id: 'BUG-102', title: 'Webhook timeout on large payloads', severity: 'Major', status: 'In Progress', createdAt: '5h ago' },
      { id: 'BUG-103', title: 'Typo in README', severity: 'Minor', status: 'Open', createdAt: '1d ago' },
    ],
    prs: [
      { id: 45, title: 'feat: Add Tailwind Support', author: 'dev_alex', status: 'Merged', checksPassed: true },
      { id: 46, title: 'fix: API Rate Limiting', author: 'qa_sarah', status: 'Open', checksPassed: false },
      { id: 47, title: 'chore: Update dependencies', author: 'bot_renovate', status: 'Closed', checksPassed: true },
    ],
    logs: [
      { timestamp: new Date().toLocaleTimeString(), level: 'INFO', message: 'StudioAI Backend Service Started' },
      { timestamp: new Date().toLocaleTimeString(), level: 'INFO', message: 'Connected to GitHub Webhook' },
    ],
    security: {
      isSecure: true,
      vulnerabilities: 0,
      lastScan: new Date().toISOString(),
    },
  };
}
