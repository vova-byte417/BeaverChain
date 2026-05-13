import type { ModelVersion, Workflow, DashboardStats, EvaluationRecord } from '../types';

// Mock 用户
export const mockUser = {
  id: 'user-1',
  name: '张三',
  email: 'zhangsan@beaverchain.ai',
  avatar: '',
};

// Mock 模型版本数据
export const mockModelVersions: ModelVersion[] = [
  {
    id: 'mv-001',
    name: 'Chatbot v1.0',
    version: 'v1.0.0',
    description: '第一个稳定版本，优化了对话流畅度',
    status: 'production',
    owner: mockUser,
    tags: ['production', 'chatbot', 'stable'],
    weights: {
      modelType: 'LLaMA-3-70B',
      fileSize: 140,
      parameters: '70B',
      quantization: '4-bit',
    },
    prompt: {
      systemPrompt: 'You are a helpful AI assistant...',
      userTemplate: '{{user_input}}',
      variables: ['user_input'],
    },
    rag: {
      enabled: true,
      knowledgeBase: 'kb-001',
      embeddingModel: 'text-embedding-ada-002',
      topK: 5,
      chunkSize: 512,
    },
    guardrails: {
      toxicityThreshold: 0.7,
      hallucinationCheck: true,
      sensitiveWords: ['敏感词1', '敏感词2'],
      outputFormat: 'markdown',
    },
    parameters: {
      temperature: 0.7,
      topP: 0.9,
      maxTokens: 2048,
      frequencyPenalty: 0.0,
      presencePenalty: 0.0,
    },
    lineage: {
      forkHistory: [],
    },
    evaluationMetrics: {
      hallucinationRate: 0.032,
      toxicityScore: 0.045,
      faithfulness: 0.92,
      relevance: 0.95,
      latencyP95: 480,
      tokenConsumption: 1250000,
    },
    createdAt: '2026-05-10T08:00:00Z',
    updatedAt: '2026-05-12T10:30:00Z',
  },
  {
    id: 'mv-002',
    name: 'Chatbot v1.1-beta',
    version: 'v1.1.0-beta',
    description: '新增 RAG 功能，待测试',
    status: 'testing',
    owner: mockUser,
    tags: ['testing', 'rag', 'beta'],
    weights: {
      modelType: 'LLaMA-3-70B',
      fileSize: 140,
      parameters: '70B',
    },
    prompt: {
      systemPrompt: 'You are a helpful AI assistant with RAG...',
      userTemplate: '{{user_input}}\n\nContext: {{context}}',
      variables: ['user_input', 'context'],
    },
    rag: {
      enabled: true,
      knowledgeBase: 'kb-002',
      embeddingModel: 'text-embedding-ada-002',
      topK: 8,
      chunkSize: 1024,
    },
    guardrails: {
      toxicityThreshold: 0.8,
      hallucinationCheck: true,
      sensitiveWords: [],
      outputFormat: 'markdown',
    },
    parameters: {
      temperature: 0.6,
      topP: 0.95,
      maxTokens: 4096,
      frequencyPenalty: 0.1,
      presencePenalty: 0.0,
    },
    lineage: {
      parentVersion: 'mv-001',
      forkHistory: ['mv-001'],
    },
    evaluationMetrics: {
      hallucinationRate: 0.028,
      toxicityScore: 0.038,
      faithfulness: 0.94,
      relevance: 0.97,
      latencyP95: 520,
      tokenConsumption: 890000,
    },
    createdAt: '2026-05-11T14:20:00Z',
    updatedAt: '2026-05-12T09:15:00Z',
  },
  {
    id: 'mv-003',
    name: 'Code Assistant',
    version: 'v0.5.0',
    description: '代码助手模型，支持多种编程语言',
    status: 'draft',
    owner: mockUser,
    tags: ['draft', 'code', 'experimental'],
    weights: {
      modelType: 'CodeLlama-34B',
      fileSize: 70,
      parameters: '34B',
    },
    prompt: {
      systemPrompt: 'You are a code assistant...',
      userTemplate: '{{code}}\n\n{{question}}',
      variables: ['code', 'question'],
    },
    rag: {
      enabled: false,
      knowledgeBase: '',
      embeddingModel: '',
      topK: 0,
      chunkSize: 0,
    },
    guardrails: {
      toxicityThreshold: 0.9,
      hallucinationCheck: false,
      sensitiveWords: [],
      outputFormat: 'markdown',
    },
    parameters: {
      temperature: 0.2,
      topP: 0.9,
      maxTokens: 8192,
      frequencyPenalty: 0.0,
      presencePenalty: 0.0,
    },
    lineage: {
      forkHistory: [],
    },
    evaluationMetrics: {
      hallucinationRate: 0.055,
      toxicityScore: 0.02,
      faithfulness: 0.88,
      relevance: 0.91,
      latencyP95: 650,
      tokenConsumption: 450000,
    },
    createdAt: '2026-05-12T07:00:00Z',
    updatedAt: '2026-05-12T07:00:00Z',
  },
];

// Mock 工作流数据
export const mockWorkflows: Workflow[] = [
  {
    id: 'wf-001',
    name: '客服对话流程',
    description: '处理客户咨询的标准工作流',
    status: 'running',
    nodes: [
      { id: 'n1', type: 'llm', position: { x: 250, y: 100 }, data: { label: '意图识别' } },
      { id: 'n2', type: 'condition', position: { x: 250, y: 250 }, data: { label: '是否需要 RAG' } },
      { id: 'n3', type: 'rag', position: { x: 100, y: 400 }, data: { label: '知识库检索' } },
      { id: 'n4', type: 'llm', position: { x: 400, y: 400 }, data: { label: '生成回答' } },
      { id: 'n5', type: 'output', position: { x: 250, y: 550 }, data: { label: '输出结果' } },
    ],
    edges: [
      { id: 'e1', source: 'n1', target: 'n2' },
      { id: 'e2', source: 'n2', target: 'n3' },
      { id: 'e3', source: 'n2', target: 'n4' },
      { id: 'e4', source: 'n3', target: 'n4' },
      { id: 'e5', source: 'n4', target: 'n5' },
    ],
    createdAt: '2026-05-08T10:00:00Z',
    updatedAt: '2026-05-12T08:30:00Z',
  },
  {
    id: 'wf-002',
    name: '文档摘要流程',
    description: '自动摘要长文档的工作流',
    status: 'completed',
    nodes: [
      { id: 'n1', type: 'llm', position: { x: 250, y: 100 }, data: { label: '分块处理' } },
      { id: 'n2', type: 'llm', position: { x: 250, y: 250 }, data: { label: '生成摘要' } },
      { id: 'n3', type: 'llm', position: { x: 250, y: 400 }, data: { label: '合并优化' } },
    ],
    edges: [
      { id: 'e1', source: 'n1', target: 'n2' },
      { id: 'e2', source: 'n2', target: 'n3' },
    ],
    createdAt: '2026-05-05T14:00:00Z',
    updatedAt: '2026-05-10T16:20:00Z',
  },
];

// Mock 仪表板统计数据
export const mockDashboardStats: DashboardStats = {
  totalModels: 12,
  totalVersions: 48,
  tokenConsumption: 25890000,
  avgLatency: 420,
  hallucinationRate: 0.035,
  activeDeployments: 8,
};

// Mock 评估历史数据
export const mockEvaluationHistory: EvaluationRecord[] = [
  { id: 'eval-001', modelVersion: 'v1.0.0', timestamp: '2026-05-08', hallucinationRate: 0.042, toxicityScore: 0.052, faithfulness: 0.89, relevance: 0.93, totalTests: 1000, passedTests: 945 },
  { id: 'eval-002', modelVersion: 'v1.0.0', timestamp: '2026-05-09', hallucinationRate: 0.038, toxicityScore: 0.048, faithfulness: 0.90, relevance: 0.94, totalTests: 1000, passedTests: 952 },
  { id: 'eval-003', modelVersion: 'v1.0.0', timestamp: '2026-05-10', hallucinationRate: 0.035, toxicityScore: 0.045, faithfulness: 0.91, relevance: 0.94, totalTests: 1200, passedTests: 1150 },
  { id: 'eval-004', modelVersion: 'v1.0.0', timestamp: '2026-05-11', hallucinationRate: 0.033, toxicityScore: 0.042, faithfulness: 0.92, relevance: 0.95, totalTests: 1200, passedTests: 1168 },
  { id: 'eval-005', modelVersion: 'v1.0.0', timestamp: '2026-05-12', hallucinationRate: 0.032, toxicityScore: 0.045, faithfulness: 0.92, relevance: 0.95, totalTests: 1500, passedTests: 1462 },
];

// Mock API 函数
export async function fetchMockData<T>(data: T, delay = 500): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(data), delay));
}
