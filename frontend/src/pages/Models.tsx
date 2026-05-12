import { useEffect, useState } from 'react';
import { Plus, Search, MoreHorizontal, ArrowUpRight, Clock, Tag, CheckCircle2, AlertCircle, Loader } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { mockModelVersions, fetchMockData } from '../mock/data';
import type { ModelVersion } from '../types';

const statusConfig = {
  production: { label: '生产环境', variant: 'success' as const, icon: CheckCircle2 },
  testing: { label: '测试中', variant: 'info' as const, icon: Loader },
  draft: { label: '草稿', variant: 'default' as const, icon: Clock },
  archived: { label: '已归档', variant: 'warning' as const, icon: AlertCircle },
};

function ModelCard({ model }: { model: ModelVersion }) {
  const status = statusConfig[model.status];
  const StatusIcon = status.icon;

  return (
    <Card className="hover:border-hairline-strong transition-colors cursor-pointer">
      <CardContent className="p-5">
        {/* 头部 */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-ink">{model.name}</h3>
              <Badge variant={status.variant} className="flex items-center gap-1">
                <StatusIcon className="w-3 h-3" />
                {status.label}
              </Badge>
            </div>
            <p className="text-sm text-ink-subtle mt-1">版本: {model.version}</p>
          </div>
          <button className="p-1.5 rounded-md text-ink-subtle hover:text-ink hover:bg-surface-2 transition-colors">
            <MoreHorizontal className="w-5 h-5" />
          </button>
        </div>

        {/* 描述 */}
        <p className="text-sm text-ink-muted mb-4 line-clamp-2">{model.description}</p>

        {/* 指标 */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-surface-2 rounded-md p-3">
            <p className="text-xs text-ink-subtle mb-1">幻觉率</p>
            <p className="text-lg font-semibold text-semantic-success">
              {(model.evaluationMetrics.hallucinationRate * 100).toFixed(1)}%
            </p>
          </div>
          <div className="bg-surface-2 rounded-md p-3">
            <p className="text-xs text-ink-subtle mb-1">P95 延迟</p>
            <p className="text-lg font-semibold text-ink">
              {model.evaluationMetrics.latencyP95}ms
            </p>
          </div>
        </div>

        {/* 标签 */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {model.tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-surface-2 text-ink-muted text-xs rounded-md"
            >
              <Tag className="w-3 h-3" />
              {tag}
            </span>
          ))}
        </div>

        {/* 底部操作 */}
        <div className="flex items-center justify-between pt-3 border-t border-hairline">
          <span className="text-xs text-ink-tertiary">
            更新于 {new Date(model.updatedAt).toLocaleDateString('zh-CN')}
          </span>
          <Button variant="ghost" size="sm" rightIcon={<ArrowUpRight className="w-4 h-4" />}>
            查看详情
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function Models() {
  const [models, setModels] = useState<ModelVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchMockData(mockModelVersions);
        setModels(data);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const filteredModels = models.filter(
    (model) =>
      model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.version.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-ink">模型管理</h2>
          <p className="text-ink-subtle mt-1">管理您的 AI 模型版本，包括权重、Prompt、RAG 配置等</p>
        </div>
        <Button leftIcon={<Plus className="w-4 h-4" />}>
          创建新版本
        </Button>
      </div>

      {/* 搜索和筛选 */}
      <div className="flex items-center gap-4">
        <div className="flex-1 max-w-md">
          <Input
            placeholder="搜索模型名称、版本或描述..."
            leftIcon={<Search className="w-4 h-4" />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary">全部状态</Button>
          <Button variant="secondary">重置筛选</Button>
        </div>
      </div>

      {/* 统计概览 */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-ink-subtle">总模型数</p>
            <p className="text-2xl font-bold text-ink mt-1">{models.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-ink-subtle">生产环境</p>
            <p className="text-2xl font-bold text-semantic-success mt-1">
              {models.filter((m) => m.status === 'production').length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-ink-subtle">测试中</p>
            <p className="text-2xl font-bold text-semantic-info mt-1">
              {models.filter((m) => m.status === 'testing').length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-ink-subtle">草稿</p>
            <p className="text-2xl font-bold text-ink-muted mt-1">
              {models.filter((m) => m.status === 'draft').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 模型列表 */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-ink-muted">加载中...</div>
        </div>
      ) : filteredModels.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="w-16 h-16 rounded-full bg-surface-2 flex items-center justify-center mb-4">
              <Search className="w-8 h-8 text-ink-subtle" />
            </div>
            <h3 className="text-lg font-semibold text-ink mb-2">未找到匹配的模型</h3>
            <p className="text-ink-subtle text-center max-w-sm">
              尝试调整搜索关键词或清除筛选条件
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredModels.map((model) => (
            <ModelCard key={model.id} model={model} />
          ))}
        </div>
      )}
    </div>
  );
}
