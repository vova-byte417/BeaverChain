import { useState } from 'react';
import {
  Settings,
  MessageSquare,
  Database,
  Shield,
  Save,
  Plus,
  Trash2,
  ToggleLeft,
  ChevronRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { cn } from '../utils/cn';

const settingsTabs = [
  { id: 'prompt', label: 'Prompt 管理', icon: MessageSquare },
  { id: 'rag', label: 'RAG 配置', icon: Database },
  { id: 'guardrails', label: 'Guardrails 规则', icon: Shield },
];

// Prompt 模板列表
const mockPromptTemplates = [
  {
    id: 'pt-001',
    name: '默认系统提示',
    description: '通用对话场景的系统提示词',
    version: 'v2.1',
    isDefault: true,
    updatedAt: '2026-05-12',
  },
  {
    id: 'pt-002',
    name: '代码助手',
    description: '针对编程场景优化的提示词',
    version: 'v1.5',
    isDefault: false,
    updatedAt: '2026-05-10',
  },
  {
    id: 'pt-003',
    name: '文档摘要',
    description: '用于长文档摘要的专用提示词',
    version: 'v1.2',
    isDefault: false,
    updatedAt: '2026-05-08',
  },
];

// RAG 知识库配置
const mockRAGConfigs = [
  {
    id: 'kb-001',
    name: '产品知识库',
    description: '包含产品文档、FAQ、使用指南',
    embeddingModel: 'text-embedding-ada-002',
    chunkSize: 512,
    isActive: true,
    docCount: 284,
  },
  {
    id: 'kb-002',
    name: '技术文档库',
    description: 'API 文档、技术规范、架构设计',
    embeddingModel: 'text-embedding-ada-002',
    chunkSize: 1024,
    isActive: true,
    docCount: 156,
  },
];

// Guardrails 规则
const mockGuardrailsRules = {
  toxicity: {
    enabled: true,
    threshold: 0.7,
    description: '检测并过滤有害或攻击性内容',
  },
  hallucination: {
    enabled: true,
    threshold: 0.8,
    description: '检测事实性错误和虚假信息',
  },
  sensitiveData: {
    enabled: true,
    threshold: 0.9,
    description: '检测并屏蔽敏感个人信息',
  },
  promptInjection: {
    enabled: true,
    threshold: 0.85,
    description: '防御提示词注入攻击',
  },
  outputFormat: {
    enabled: false,
    format: 'markdown',
    description: '强制输出格式规范',
  },
};

function PromptSettings() {
  const [templates] = useState(mockPromptTemplates);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-ink">Prompt 模板</h3>
          <p className="text-sm text-ink-subtle mt-1">管理和版本化您的提示词模板</p>
        </div>
        <Button leftIcon={<Plus className="w-4 h-4" />}>
          创建模板
        </Button>
      </div>

      {/* 模板列表 */}
      <div className="space-y-3">
        {templates.map((template) => (
          <Card
            key={template.id}
            className={cn(
              'cursor-pointer transition-all hover:border-hairline-strong',
              selectedTemplate === template.id && 'border-primary'
            )}
            onClick={() => setSelectedTemplate(template.id)}
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h4 className="font-medium text-ink">{template.name}</h4>
                    <Badge variant="default">{template.version}</Badge>
                    {template.isDefault && <Badge variant="purple">默认</Badge>}
                  </div>
                  <p className="text-sm text-ink-subtle">{template.description}</p>
                  <p className="text-xs text-ink-tertiary mt-2">
                    更新于 {template.updatedAt}
                  </p>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  <Button variant="ghost" size="sm">
                    编辑
                  </Button>
                  <Button variant="ghost" size="sm">
                    版本历史
                  </Button>
                  <ChevronRight className="w-5 h-5 text-ink-subtle" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 编辑器区域 */}
      {selectedTemplate && (
        <Card>
          <CardHeader>
            <CardTitle>编辑 Prompt 模板</CardTitle>
            <CardDescription>修改提示词内容和参数</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-ink mb-1.5">模板名称</label>
              <Input defaultValue="默认系统提示" />
            </div>
            <div>
              <label className="block text-sm font-medium text-ink mb-1.5">描述</label>
              <Input defaultValue="通用对话场景的系统提示词" />
            </div>
            <div>
              <label className="block text-sm font-medium text-ink mb-1.5">Prompt 内容</label>
              <textarea
                className="w-full h-48 px-4 py-3 bg-surface-1 border border-hairline rounded-lg text-ink placeholder-ink-tertiary focus:outline-none focus:ring-2 focus:ring-primary-focus resize-none font-mono text-sm"
                defaultValue={`你是一个专业的 AI 助手，旨在帮助用户解决问题。

请遵循以下原则：
1. 回答要准确、简洁、有条理
2. 不知道的问题要诚实说明
3. 保持友好和专业的语气
4. 必要时可以向用户提问确认`}
              />
            </div>
            <div className="flex items-center gap-3">
              <Button leftIcon={<Save className="w-4 h-4" />}>
                保存更改
              </Button>
              <Button variant="secondary">创建新版本</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function RAGSettings() {
  const [configs] = useState(mockRAGConfigs);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-ink">知识库配置</h3>
          <p className="text-sm text-ink-subtle mt-1">配置 RAG 检索的知识库和参数</p>
        </div>
        <Button leftIcon={<Plus className="w-4 h-4" />}>
          添加知识库
        </Button>
      </div>

      <div className="space-y-4">
        {configs.map((config) => (
          <Card key={config.id}>
            <CardContent className="p-5">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-ink">{config.name}</h4>
                    <Badge variant={config.isActive ? 'success' : 'default'}>
                      {config.isActive ? '已启用' : '已禁用'}
                    </Badge>
                  </div>
                  <p className="text-sm text-ink-subtle mt-1">{config.description}</p>
                </div>
                <Button variant="ghost" size="sm">
                  配置
                </Button>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="bg-surface-2 rounded-lg p-3">
                  <p className="text-xs text-ink-subtle mb-1">嵌入模型</p>
                  <p className="text-sm font-medium text-ink">{config.embeddingModel}</p>
                </div>
                <div className="bg-surface-2 rounded-lg p-3">
                  <p className="text-xs text-ink-subtle mb-1">分块大小</p>
                  <p className="text-sm font-medium text-ink">{config.chunkSize} tokens</p>
                </div>
                <div className="bg-surface-2 rounded-lg p-3">
                  <p className="text-xs text-ink-subtle mb-1">文档数量</p>
                  <p className="text-sm font-medium text-ink">{config.docCount} 篇</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 全局 RAG 参数 */}
      <Card>
        <CardHeader>
          <CardTitle>全局检索参数</CardTitle>
          <CardDescription>配置 RAG 检索的默认行为</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-ink mb-1.5">Top-K 检索结果</label>
              <Input type="number" defaultValue="5" />
            </div>
            <div>
              <label className="block text-sm font-medium text-ink mb-1.5">相似度阈值</label>
              <Input type="number" defaultValue="0.7" step="0.1" />
            </div>
            <div>
              <label className="block text-sm font-medium text-ink mb-1.5">重叠 token 数</label>
              <Input type="number" defaultValue="64" />
            </div>
            <div>
              <label className="block text-sm font-medium text-ink mb-1.5">最大检索 token</label>
              <Input type="number" defaultValue="4096" />
            </div>
          </div>
          <Button leftIcon={<Save className="w-4 h-4" />}>
            保存配置
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function GuardrailsSettings() {
  const [rules, setRules] = useState(mockGuardrailsRules);

  const toggleRule = (ruleId: string) => {
    setRules((prev) => ({
      ...prev,
      [ruleId]: {
        ...prev[ruleId as keyof typeof prev],
        enabled: !prev[ruleId as keyof typeof prev].enabled,
      },
    }));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-ink">Guardrails 安全规则</h3>
          <p className="text-sm text-ink-subtle mt-1">配置内容安全和输出质量控制规则</p>
        </div>
      </div>

      <div className="grid gap-4">
        {Object.entries(rules).map(([ruleId, rule]) => (
          <Card key={ruleId}>
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <button
                      onClick={() => toggleRule(ruleId)}
                      className={`relative w-11 h-6 rounded-full transition-colors ${
                        rule.enabled ? 'bg-primary' : 'bg-surface-2'
                      }`}
                    >
                      <span
                        className={`absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition-transform ${
                          rule.enabled ? 'translate-x-5' : ''
                        }`}
                      />
                    </button>
                    <h4 className="font-medium text-ink capitalize">
                      {ruleId === 'toxicity'
                        ? '毒性检测'
                        : ruleId === 'hallucination'
                        ? '幻觉检测'
                        : ruleId === 'sensitiveData'
                        ? '敏感数据保护'
                        : ruleId === 'promptInjection'
                        ? '提示词注入防御'
                        : '输出格式控制'}
                    </h4>
                    <Badge variant={rule.enabled ? 'success' : 'default'}>
                      {rule.enabled ? '已启用' : '已禁用'}
                    </Badge>
                  </div>
                  <p className="text-sm text-ink-subtle mb-3">{rule.description}</p>

                  {ruleId !== 'outputFormat' && (
                    <div className="flex items-center gap-4">
                      <div>
                        <label className="text-xs text-ink-subtle block mb-1">触发阈值</label>
                        <Input
                          type="number"
                          className="w-24"
                          value={rule.threshold}
                          step="0.05"
                          onChange={(e) => {
                            setRules((prev) => ({
                              ...prev,
                              [ruleId]: {
                                ...prev[ruleId as keyof typeof prev],
                                threshold: parseFloat(e.target.value),
                              },
                            }));
                          }}
                        />
                      </div>
                    </div>
                  )}
                </div>

                <Button variant="ghost" size="sm">
                  高级设置
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <Button leftIcon={<Save className="w-4 h-4" />}>
          保存所有规则
        </Button>
        <Button variant="secondary">恢复默认设置</Button>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('prompt');

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-lg bg-primary/10">
          <Settings className="w-6 h-6 text-primary" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-ink">配置管理</h2>
          <p className="text-ink-subtle mt-1">管理系统配置、Prompt 模板、RAG 设置和安全规则</p>
        </div>
      </div>

      {/* 标签页导航 */}
      <div className="flex items-center gap-1 p-1 bg-surface-1 rounded-lg w-fit">
        {settingsTabs.map((tab) => {
          const isActive = activeTab === tab.id;
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
                isActive
                  ? 'bg-surface-2 text-ink'
                  : 'text-ink-subtle hover:text-ink hover:bg-surface-2/50'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* 标签页内容 */}
      <div>
        {activeTab === 'prompt' && <PromptSettings />}
        {activeTab === 'rag' && <RAGSettings />}
        {activeTab === 'guardrails' && <GuardrailsSettings />}
      </div>
    </div>
  );
}
