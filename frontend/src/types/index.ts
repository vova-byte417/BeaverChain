// 模型版本类型
export interface ModelVersion {
  id: string;
  name: string;
  version: string;
  description: string;
  status: 'draft' | 'testing' | 'production' | 'archived';
  owner: User;
  tags: string[];
  weights: WeightsConfig;
  prompt: PromptConfig;
  rag: RAGConfig;
  guardrails: GuardrailsConfig;
  parameters: InferenceParameters;
  lineage: LineageInfo;
  evaluationMetrics: EvaluationMetrics;
  createdAt: string;
  updatedAt: string;
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

export interface WeightsConfig {
  modelType: string;
  fileSize: number;
  parameters: string;
  quantization?: string;
}

export interface PromptConfig {
  systemPrompt: string;
  userTemplate: string;
  variables: string[];
}

export interface RAGConfig {
  enabled: boolean;
  knowledgeBase: string;
  embeddingModel: string;
  topK: number;
  chunkSize: number;
}

export interface GuardrailsConfig {
  toxicityThreshold: number;
  hallucinationCheck: boolean;
  sensitiveWords: string[];
  outputFormat: string;
}

export interface InferenceParameters {
  temperature: number;
  topP: number;
  maxTokens: number;
  frequencyPenalty: number;
  presencePenalty: number;
}

export interface LineageInfo {
  parentVersion?: string;
  derivedFrom?: string;
  forkHistory: string[];
}

export interface EvaluationMetrics {
  hallucinationRate: number;
  toxicityScore: number;
  faithfulness: number;
  relevance: number;
  latencyP95: number;
  tokenConsumption: number;
}

// 工作流类型
export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowNode {
  id: string;
  type: 'llm' | 'condition' | 'rag' | 'tool' | 'output';
  position: { x: number; y: number };
  data: Record<string, unknown>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  type?: string;
}

// 仪表板统计类型
export interface DashboardStats {
  totalModels: number;
  totalVersions: number;
  tokenConsumption: number;
  avgLatency: number;
  hallucinationRate: number;
  activeDeployments: number;
}

// 评估记录类型
export interface EvaluationRecord {
  id: string;
  modelVersion: string;
  timestamp: string;
  hallucinationRate: number;
  toxicityScore: number;
  faithfulness: number;
  relevance: number;
  totalTests: number;
  passedTests: number;
}
