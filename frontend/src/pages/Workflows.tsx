import { useState, useCallback } from 'react';
import {
  ReactFlow,
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  Handle,
  Position,
  NodeProps,
} from 'reactflow';
import 'reactflow/dist/style.css';
import {
  Plus,
  Play,
  Save,
  Settings,
  GitBranch,
  Brain,
  Database,
  Wrench,
  FileOutput,
  ArrowRight,
} from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { cn } from '../utils/cn';

// 自定义节点类型
const nodeTypes = {
  llm: LLMNode,
  condition: ConditionNode,
  rag: RAGNode,
  tool: ToolNode,
  output: OutputNode,
};

// LLM 节点
function LLMNode({ data, selected }: NodeProps) {
  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 min-w-[160px]',
        selected ? 'border-primary bg-primary/10' : 'border-hairline-strong bg-surface-1'
      )}
    >
      <Handle type="target" position={Position.Top} className="!bg-primary" />
      <div className="flex items-center gap-2 mb-1">
        <Brain className="w-4 h-4 text-primary" />
        <span className="font-medium text-ink text-sm">LLM 调用</span>
      </div>
      <p className="text-xs text-ink-subtle">{(data.label as string) || '模型推理'}</p>
      <Handle type="source" position={Position.Bottom} className="!bg-primary" />
    </div>
  );
}

// 条件节点
function ConditionNode({ data, selected }: NodeProps) {
  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 min-w-[160px]',
        selected ? 'border-semantic-warning bg-semantic-warning/10' : 'border-hairline-strong bg-surface-1'
      )}
    >
      <Handle type="target" position={Position.Top} className="!bg-semantic-warning" />
      <div className="flex items-center gap-2 mb-1">
        <GitBranch className="w-4 h-4 text-semantic-warning" />
        <span className="font-medium text-ink text-sm">条件判断</span>
      </div>
      <p className="text-xs text-ink-subtle">{(data.label as string) || '分支逻辑'}</p>
      <Handle type="source" position={Position.Bottom} className="!bg-semantic-warning" />
    </div>
  );
}

// RAG 节点
function RAGNode({ data, selected }: NodeProps) {
  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 min-w-[160px]',
        selected ? 'border-semantic-info bg-semantic-info/10' : 'border-hairline-strong bg-surface-1'
      )}
    >
      <Handle type="target" position={Position.Top} className="!bg-semantic-info" />
      <div className="flex items-center gap-2 mb-1">
        <Database className="w-4 h-4 text-semantic-info" />
        <span className="font-medium text-ink text-sm">RAG 检索</span>
      </div>
      <p className="text-xs text-ink-subtle">{(data.label as string) || '知识库检索'}</p>
      <Handle type="source" position={Position.Bottom} className="!bg-semantic-info" />
    </div>
  );
}

// 工具节点
function ToolNode({ data, selected }: NodeProps) {
  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 min-w-[160px]',
        selected ? 'border-semantic-success bg-semantic-success/10' : 'border-hairline-strong bg-surface-1'
      )}
    >
      <Handle type="target" position={Position.Top} className="!bg-semantic-success" />
      <div className="flex items-center gap-2 mb-1">
        <Wrench className="w-4 h-4 text-semantic-success" />
        <span className="font-medium text-ink text-sm">工具调用</span>
      </div>
      <p className="text-xs text-ink-subtle">{(data.label as string) || '外部工具'}</p>
      <Handle type="source" position={Position.Bottom} className="!bg-semantic-success" />
    </div>
  );
}

// 输出节点
function OutputNode({ data, selected }: NodeProps) {
  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 min-w-[160px]',
        selected ? 'border-ink-muted bg-surface-2' : 'border-hairline-strong bg-surface-1'
      )}
    >
      <Handle type="target" position={Position.Top} className="!bg-ink-muted" />
      <div className="flex items-center gap-2 mb-1">
        <FileOutput className="w-4 h-4 text-ink-muted" />
        <span className="font-medium text-ink text-sm">输出</span>
      </div>
      <p className="text-xs text-ink-subtle">{(data.label as string) || '结果输出'}</p>
    </div>
  );
}

// 初始节点
const initialNodes: Node[] = [
  {
    id: '1',
    type: 'llm',
    position: { x: 250, y: 50 },
    data: { label: '意图识别' },
  },
  {
    id: '2',
    type: 'condition',
    position: { x: 250, y: 180 },
    data: { label: '是否需要 RAG' },
  },
  {
    id: '3',
    type: 'rag',
    position: { x: 100, y: 310 },
    data: { label: '知识库检索' },
  },
  {
    id: '4',
    type: 'llm',
    position: { x: 400, y: 310 },
    data: { label: '生成回答' },
  },
  {
    id: '5',
    type: 'output',
    position: { x: 250, y: 440 },
    data: { label: '输出结果' },
  },
];

// 初始边
const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', animated: true, style: { stroke: '#5e6ad2' } },
  { id: 'e2-3', source: '2', target: '3', animated: true, style: { stroke: '#5e6ad2' } },
  { id: 'e2-4', source: '2', target: '4', animated: true, style: { stroke: '#5e6ad2' } },
  { id: 'e3-5', source: '3', target: '5', animated: true, style: { stroke: '#5e6ad2' } },
  { id: 'e4-5', source: '4', target: '5', animated: true, style: { stroke: '#5e6ad2' } },
];

// 侧边栏节点模板
const nodeTemplates = [
  { type: 'llm', label: 'LLM 调用', icon: Brain, color: 'primary' },
  { type: 'condition', label: '条件判断', icon: GitBranch, color: 'warning' },
  { type: 'rag', label: 'RAG 检索', icon: Database, color: 'info' },
  { type: 'tool', label: '工具调用', icon: Wrench, color: 'success' },
  { type: 'output', label: '输出结果', icon: FileOutput, color: 'default' },
];

export default function Workflows() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [workflowName, setWorkflowName] = useState('客服对话工作流');
  const [isRunning, setIsRunning] = useState(false);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: '#5e6ad2' } }, eds)),
    [setEdges]
  );

  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const reactFlowBounds = event.currentTarget.getBoundingClientRect();
      const type = event.dataTransfer.getData('application/reactflow');

      // 检查是否是有效的节点类型
      if (!nodeTemplates.find((t) => t.type === type)) return;

      const position = {
        x: event.clientX - reactFlowBounds.left - 80,
        y: event.clientY - reactFlowBounds.top - 30,
      };

      const newNode: Node = {
        id: `${+new Date()}`,
        type,
        position,
        data: { label: '新节点' },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [setNodes]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const handleRun = () => {
    setIsRunning(true);
    setTimeout(() => setIsRunning(false), 2000);
  };

  return (
    <div className="flex flex-col h-full">
      {/* 顶部工具栏 */}
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-hairline">
        <div className="flex items-center gap-4">
          <div>
            <h2 className="text-xl font-bold text-ink">工作流编排</h2>
            <p className="text-sm text-ink-subtle">可视化设计 AI 工作流程</p>
          </div>
          <div className="h-8 w-px bg-hairline" />
          <input
            type="text"
            value={workflowName}
            onChange={(e) => setWorkflowName(e.target.value)}
            className="px-3 py-1.5 bg-transparent border border-hairline rounded-md text-ink text-sm focus:outline-none focus:ring-2 focus:ring-primary-focus"
          />
          <Badge variant={isRunning ? 'success' : 'default'}>
            {isRunning ? '运行中' : '已就绪'}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" leftIcon={<Save className="w-4 h-4" />}>
            保存
          </Button>
          <Button
            leftIcon={<Play className="w-4 h-4" />}
            onClick={handleRun}
            isLoading={isRunning}
          >
            {isRunning ? '运行中' : '运行'}
          </Button>
          <Button variant="tertiary" leftIcon={<Settings className="w-4 h-4" />} />
        </div>
      </div>

      <div className="flex flex-1 gap-4 overflow-hidden">
        {/* 左侧节点面板 */}
        <div className="w-48 flex-shrink-0">
          <Card className="h-full">
            <CardContent className="p-4">
              <h3 className="text-sm font-semibold text-ink mb-3">节点库</h3>
              <p className="text-xs text-ink-subtle mb-4">拖拽节点到画布创建工作流</p>
              <div className="space-y-2">
                {nodeTemplates.map((template) => {
                  const colorClasses = {
                    primary: 'bg-primary/10 text-primary border-primary/20',
                    warning: 'bg-semantic-warning/10 text-semantic-warning border-semantic-warning/20',
                    info: 'bg-semantic-info/10 text-semantic-info border-semantic-info/20',
                    success: 'bg-semantic-success/10 text-semantic-success border-semantic-success/20',
                    default: 'bg-surface-2 text-ink-muted border-hairline',
                  };
                  return (
                    <div
                      key={template.type}
                      draggable
                      onDragStart={(e) => onDragStart(e, template.type)}
                      className={`flex items-center gap-2 p-3 rounded-lg border cursor-grab hover:opacity-80 active:cursor-grabbing transition-opacity ${colorClasses[template.color as keyof typeof colorClasses]}`}
                    >
                      <template.icon className="w-4 h-4 flex-shrink-0" />
                      <span className="text-sm font-medium">{template.label}</span>
                    </div>
                  );
                })}
              </div>

              <div className="mt-6 pt-4 border-t border-hairline">
                <h4 className="text-sm font-semibold text-ink mb-3">工作流统计</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-ink-subtle">节点数量</span>
                    <span className="text-ink font-medium">{nodes.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-subtle">连接数量</span>
                    <span className="text-ink font-medium">{edges.length}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 主画布区域 */}
        <div className="flex-1 bg-surface-1 border border-hairline rounded-lg overflow-hidden">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onDrop={onDrop}
            onDragOver={onDragOver}
            nodeTypes={nodeTypes}
            fitView
            className="bg-canvas"
          >
            <Background variant={BackgroundVariant.Dots} gap={12} size={1} color="#23252a" />
            <Controls
              className="!bg-surface-1 !border-hairline"
              position="bottom-right"
            />
          </ReactFlow>
        </div>

        {/* 右侧属性面板 */}
        <div className="w-64 flex-shrink-0">
          <Card className="h-full">
            <CardContent className="p-4">
              <h3 className="text-sm font-semibold text-ink mb-4">节点属性</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-ink-subtle mb-1.5">
                    节点标签
                  </label>
                  <input
                    type="text"
                    placeholder="选择节点编辑属性"
                    disabled
                    className="w-full px-3 py-2 bg-surface-2 border border-hairline rounded-md text-sm text-ink-muted placeholder-ink-tertiary focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-ink-subtle mb-1.5">
                    节点类型
                  </label>
                  <input
                    type="text"
                    placeholder="未选择"
                    disabled
                    className="w-full px-3 py-2 bg-surface-2 border border-hairline rounded-md text-sm text-ink-muted placeholder-ink-tertiary focus:outline-none"
                  />
                </div>
                <div className="pt-4 border-t border-hairline">
                  <h4 className="text-xs font-semibold text-ink mb-3">操作提示</h4>
                  <ul className="space-y-2 text-xs text-ink-subtle">
                    <li className="flex items-start gap-2">
                      <span className="text-primary">•</span>
                      从左侧拖拽节点到画布
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-primary">•</span>
                      点击节点连接线建立连接
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-primary">•</span>
                      双击节点编辑标签
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-primary">•</span>
                      拖拽移动节点位置
                    </li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
