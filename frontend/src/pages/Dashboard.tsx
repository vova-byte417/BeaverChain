import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
} from 'recharts';
import {
  Box,
  Clock,
  Zap,
  AlertTriangle,
  TrendingUp,
  Activity,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { mockDashboardStats, mockEvaluationHistory, fetchMockData } from '../mock/data';
import type { DashboardStats, EvaluationRecord } from '../types';

function StatCard({
  title,
  value,
  icon: Icon,
  trend,
  trendUp = true,
  color = 'purple',
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  trend?: string;
  trendUp?: boolean;
  color?: 'purple' | 'green' | 'blue' | 'orange';
}) {
  const colorClasses = {
    purple: 'bg-primary/10 text-primary',
    green: 'bg-semantic-success/10 text-semantic-success',
    blue: 'bg-semantic-info/10 text-semantic-info',
    orange: 'bg-semantic-warning/10 text-semantic-warning',
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-ink-subtle">{title}</p>
            <p className="text-2xl font-bold text-ink mt-1">{value}</p>
            {trend && (
              <div className="flex items-center gap-1 mt-2">
                <TrendingUp
                  className={`w-4 h-4 ${
                    trendUp ? 'text-semantic-success' : 'text-semantic-error'
                  }`}
                />
                <span
                  className={`text-xs font-medium ${
                    trendUp ? 'text-semantic-success' : 'text-semantic-error'
                  }`}
                >
                  {trend}
                </span>
              </div>
            )}
          </div>
          <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
            <Icon className="w-6 h-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [history, setHistory] = useState<EvaluationRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [statsData, historyData] = await Promise.all([
          fetchMockData(mockDashboardStats),
          fetchMockData(mockEvaluationHistory),
        ]);
        setStats(statsData);
        setHistory(historyData);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  if (loading || !stats) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-ink-muted">加载中...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-ink">仪表盘</h2>
          <p className="text-ink-subtle mt-1">监控您的 AI 模型性能与使用情况</p>
        </div>
        <Badge variant="success">系统运行正常</Badge>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          title="模型总数"
          value={stats.totalModels}
          icon={Box}
          color="purple"
        />
        <StatCard
          title="版本总数"
          value={stats.totalVersions}
          icon={Activity}
          color="blue"
        />
        <StatCard
          title="活跃部署"
          value={stats.activeDeployments}
          icon={Zap}
          trend="+2 本周"
          trendUp={true}
          color="green"
        />
        <StatCard
          title="Token 消耗"
          value={`${(stats.tokenConsumption / 1000000).toFixed(1)}M`}
          icon={Zap}
          trend="+12.5%"
          trendUp={false}
          color="orange"
        />
        <StatCard
          title="平均延迟"
          value={`${stats.avgLatency}ms`}
          icon={Clock}
          trend="-8.2%"
          trendUp={true}
          color="green"
        />
        <StatCard
          title="幻觉率"
          value={`${(stats.hallucinationRate * 100).toFixed(1)}%`}
          icon={AlertTriangle}
          trend="-0.3%"
          trendUp={true}
          color="purple"
        />
      </div>

      {/* 图表区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 延迟趋势图 */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>延迟趋势 (P95)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={history}>
                  <defs>
                    <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#5e6ad2" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#5e6ad2" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#23252a" />
                  <XAxis dataKey="timestamp" stroke="#8a8f98" fontSize={12} />
                  <YAxis stroke="#8a8f98" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f1011',
                      border: '1px solid #23252a',
                      borderRadius: '8px',
                      color: '#f7f8f8',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="latency"
                    stroke="#5e6ad2"
                    fill="url(#latencyGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 质量指标图 */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>质量指标趋势</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
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
                  />
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
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Token 消耗统计 */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>测试通过统计</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#23252a" />
                  <XAxis dataKey="timestamp" stroke="#8a8f98" fontSize={12} />
                  <YAxis stroke="#8a8f98" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f1011',
                      border: '1px solid #23252a',
                      borderRadius: '8px',
                      color: '#f7f8f8',
                    }}
                  />
                  <Bar dataKey="passedTests" name="通过测试" fill="#5e6ad2" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* 幻觉率趋势 */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>幻觉率趋势</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={history}>
                  <defs>
                    <linearGradient id="hallucinationGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#e74c3c" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#e74c3c" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#23252a" />
                  <XAxis dataKey="timestamp" stroke="#8a8f98" fontSize={12} />
                  <YAxis stroke="#8a8f98" fontSize={12} domain={[0, 0.1]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0f1011',
                      border: '1px solid #23252a',
                      borderRadius: '8px',
                      color: '#f7f8f8',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="hallucinationRate"
                    name="幻觉率"
                    stroke="#e74c3c"
                    fill="url(#hallucinationGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
