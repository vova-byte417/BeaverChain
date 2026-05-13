import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
} from 'recharts';
import {
  BarChart3,
  Brain,
  AlertTriangle,
  Shield,
  RefreshCw,
  Download,
  ChevronDown,
  CheckCircle2,
  XCircle,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { mockEvaluationHistory, fetchMockData } from '../mock/data';
import type { EvaluationRecord } from '../types';

// 质量指标配置
const metricConfig = {
  faithfulness: {
    label: '忠实度',
    description: '回答与上下文信息的一致性',
    color: '#27a644',
    threshold: 0.9,
  },
  relevance: {
    label: '相关性',
    description: '回答与问题的相关程度',
    color: '#5e6ad2',
    threshold: 0.9,
  },
  hallucinationRate: {
    label: '幻觉率',
    description: '生成虚假信息的比例',
    color: '#e74c3c',
    threshold: 0.05,
    inverse: true,
  },
  toxicityScore: {
    label: '毒性评分',
    description: '有害或不当内容的程度',
    color: '#f39c12',
    threshold: 0.1,
    inverse: true,
  },
};

function MetricCard({
  label,
  value,
  description,
  color,
  threshold,
  inverse = false,
}: {
  label: string;
  value: number;
  description: string;
  color: string;
  threshold: number;
  inverse?: boolean;
}) {
  const isGood = inverse ? value <= threshold : value >= threshold;
  const TrendIcon = isGood ? TrendingUp : TrendingDown;

  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="font-medium text-ink">{label}</h3>
            <p className="text-xs text-ink-subtle mt-0.5">{description}</p>
          </div>
          <div
            className={`p-2 rounded-lg ${
              isGood ? 'bg-semantic-success/10' : 'bg-semantic-warning/10'
            }`}
          >
            {isGood ? (
              <CheckCircle2 className="w-5 h-5 text-semantic-success" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-semantic-warning" />
            )}
          </div>
        </div>

        <div className="flex items-end gap-2 mb-3">
          <span className="text-3xl font-bold text-ink">
            {(value * 100).toFixed(1)}%
          </span>
          <span
            className={`flex items-center gap-0.5 text-xs font-medium mb-1 ${
              isGood ? 'text-semantic-success' : 'text-semantic-warning'
            }`}
          >
            <TrendIcon className="w-3.5 h-3.5" />
            {isGood ? '良好' : '需改进'}
          </span>
        </div>

        {/* 进度条 */}
        <div className="h-2 bg-surface-2 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${inverse ? (1 - value) * 100 : value * 100}%`,
              backgroundColor: color,
            }}
          />
        </div>
        <p className="text-xs text-ink-tertiary mt-1.5">
          阈值: {(threshold * 100).toFixed(0)}%
        </p>
      </CardContent>
    </Card>
  );
}

function TestCaseItem({
  title,
  status,
  category,
  duration,
}: {
  title: string;
  status: 'pass' | 'fail' | 'warning';
  category: string;
  duration: string;
}) {
  const statusConfig = {
    pass: { icon: CheckCircle2, color: 'text-semantic-success', label: '通过' },
    fail: { icon: XCircle, color: 'text-semantic-error', label: '失败' },
    warning: { icon: AlertTriangle, color: 'text-semantic-warning', label: '警告' },
  };
  const config = statusConfig[status];
  const StatusIcon = config.icon;

  return (
    <div className="flex items-center justify-between p-3 bg-surface-2 rounded-lg">
      <div className="flex items-center gap-3">
        <StatusIcon className={`w-5 h-5 ${config.color}`} />
        <div>
          <p className="text-sm font-medium text-ink">{title}</p>
          <p className="text-xs text-ink-subtle">{category}</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs text-ink-subtle">{duration}</span>
        <Badge variant={status === 'pass' ? 'success' : status === 'fail' ? 'error' : 'warning'}>
          {config.label}
        </Badge>
      </div>
    </div>
  );
}

export default function Evaluations() {
  const [history, setHistory] = useState<EvaluationRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchMockData(mockEvaluationHistory);
        setHistory(data);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const latestEval = history[history.length - 1];

  // 雷达图数据
  const radarData = latestEval
    ? [
        { subject: '忠实度', value: latestEval.faithfulness * 100, fullMark: 100 },
        { subject: '相关性', value: latestEval.relevance * 100, fullMark: 100 },
        { subject: '安全性', value: (1 - latestEval.toxicityScore) * 100, fullMark: 100 },
        { subject: '事实性', value: (1 - latestEval.hallucinationRate) * 100, fullMark: 100 },
        { subject: '一致性', value: 92, fullMark: 100 },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-ink">评估中心</h2>
          <p className="text-ink-subtle mt-1">全面监控和评估 AI 模型的输出质量</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" leftIcon={<Download className="w-4 h-4" />}>
            导出报告
          </Button>
          <Button leftIcon={<RefreshCw className="w-4 h-4" />}>
            运行评估
          </Button>
        </div>
      </div>

      {/* 核心质量指标 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {latestEval &&
          Object.entries(metricConfig).map(([key, config]) => (
            <MetricCard
              key={key}
              label={config.label}
              value={latestEval[key as keyof EvaluationRecord] as number}
              description={config.description}
              color={config.color}
              threshold={config.threshold}
              inverse={config.inverse}
            />
          ))}
      </div>

      {/* 图表区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 质量趋势图 */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>质量指标趋势</CardTitle>
              <Button variant="ghost" size="sm" rightIcon={<ChevronDown className="w-4 h-4" />}>
                最近 7 天
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#23252a" />
                  <XAxis dataKey="timestamp" stroke="#8a8f98" fontSize={12} />
                  <YAxis stroke="#8a8f98" fontSize={12} domain={[0, 1]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f1011',
                      border: '1px solid #23252a',
                      borderRadius: '8px',
                      color: '#f7f8f8',
                    }}
                    formatter={(value: number) => [(value * 100).toFixed(1) + '%']}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="faithfulness"
                    name="忠实度"
                    stroke="#27a644"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="relevance"
                    name="相关性"
                    stroke="#5e6ad2"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="hallucinationRate"
                    name="幻觉率"
                    stroke="#e74c3c"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 雷达图 */}
        <Card>
          <CardHeader>
            <CardTitle>综合质量评估</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                  <PolarGrid stroke="#23252a" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#8a8f98', fontSize: 12 }} />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#8a8f98', fontSize: 10 }} />
                  <Radar
                    name="当前版本"
                    dataKey="value"
                    stroke="#5e6ad2"
                    fill="#5e6ad2"
                    fillOpacity={0.3}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 测试结果和统计 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 测试用例列表 */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>最近测试用例</CardTitle>
              <Button variant="ghost" size="sm">
                查看全部
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <TestCaseItem
                title="事实一致性测试 - 历史事件"
                status="pass"
                category="事实性"
                duration="2.3s"
              />
              <TestCaseItem
                title="事实一致性测试 - 科学知识"
                status="pass"
                category="事实性"
                duration="1.8s"
              />
              <TestCaseItem
                title="毒性检测 - 仇恨言论"
                status="pass"
                category="安全性"
                duration="0.5s"
              />
              <TestCaseItem
                title="毒性检测 - 歧视性语言"
                status="warning"
                category="安全性"
                duration="0.6s"
              />
              <TestCaseItem
                title="相关性测试 - 开放域问答"
                status="pass"
                category="相关性"
                duration="1.2s"
              />
              <TestCaseItem
                title="忠实度测试 - 长文档摘要"
                status="fail"
                category="忠实度"
                duration="3.1s"
              />
            </div>
          </CardContent>
        </Card>

        {/* 测试统计 */}
        <Card>
          <CardHeader>
            <CardTitle>测试统计</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-subtle">总测试数</span>
                <span className="text-lg font-bold text-ink">1,500</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-subtle">通过率</span>
                <span className="text-lg font-bold text-semantic-success">97.5%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-subtle">平均耗时</span>
                <span className="text-lg font-bold text-ink">1.5s</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-subtle">失败用例</span>
                <span className="text-lg font-bold text-semantic-error">37</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-ink-subtle">警告用例</span>
                <span className="text-lg font-bold text-semantic-warning">12</span>
              </div>

              <div className="pt-4 border-t border-hairline">
                <h4 className="text-sm font-medium text-ink mb-3">测试类别分布</h4>
                <div className="h-32">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={[
                        { name: '事实性', value: 450, fill: '#5e6ad2' },
                        { name: '安全性', value: 300, fill: '#27a644' },
                        { name: '相关性', value: 400, fill: '#3498db' },
                        { name: '忠实度', value: 350, fill: '#f39c12' },
                      ]}
                      layout="vertical"
                    >
                      <XAxis type="number" stroke="#8a8f98" fontSize={10} />
                      <YAxis dataKey="name" type="category" stroke="#8a8f98" fontSize={10} width={60} />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
