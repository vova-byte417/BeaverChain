# BeaverChain - AI 模型构建平台

BeaverChain 是一个一站式大模型构建与管理平台，提供完整的模型版本控制、Prompt 管理、工作流编排和质量评估能力。

## ✨ 核心功能

### 📊 仪表盘 (Dashboard)
- 实时监控模型关键指标
- Token 消耗统计
- 延迟和质量趋势图表
- 系统运行状态概览

### 📦 模型管理 (Models)
- 模型版本化管理
- 权重、Prompt、RAG 配置统一快照
- 版本对比和回滚
- 部署状态追踪

### 🔀 工作流编排 (Workflows)
- 可视化拖拽式编辑器
- 多种节点类型：LLM 调用、条件分支、RAG 检索、工具调用
- 实时预览和调试
- 工作流版本历史

### 📈 评估中心 (Evaluations)
- 幻觉率检测
- 毒性评分
- 忠实度和相关性分析
- 自动化测试用例
- 质量趋势分析

### ⚙️ 配置管理 (Settings)
- Prompt 模板版本管理
- RAG 知识库配置
- Guardrails 安全规则
- 敏感数据保护

## 🛠 技术栈

### 前端
- **框架**: React 19 + TypeScript
- **构建工具**: Vite 6
- **样式**: TailwindCSS v4
- **状态管理**: Zustand
- **图表**: Recharts
- **工作流**: ReactFlow
- **图标**: Lucide React

### 设计系统
- 深色主题 (Dark Mode)
- Linear.app 风格设计语言
- 8px 网格系统
- 可访问性支持

## 🚀 快速开始

### 安装依赖
```bash
npm install
```

### 启动开发服务器
```bash
npm run dev
```

访问 http://localhost:3000 查看应用

### 构建生产版本
```bash
npm run build
```

### 预览生产构建
```bash
npm run preview
```

## 📁 项目结构

```
src/
├── components/          # 可复用组件
│   ├── ui/             # 基础 UI 组件
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   └── Badge.tsx
│   └── layout/         # 布局组件
│       ├── Sidebar.tsx
│       └── Header.tsx
├── pages/              # 页面组件
│   ├── Dashboard.tsx
│   ├── Models.tsx
│   ├── Workflows.tsx
│   ├── Evaluations.tsx
│   └── Settings.tsx
├── types/              # TypeScript 类型定义
├── mock/               # Mock 数据
├── utils/              # 工具函数
│   └── cn.ts          # className 合并工具
├── App.tsx             # 根组件
├── main.tsx            # 入口文件
└── index.css           # 全局样式
```

## 🎨 设计规范

### 颜色系统
- **主色**: `#5e6ad2` (紫色)
- **成功**: `#27a644` (绿色)
- **警告**: `#f39c12` (橙色)
- **错误**: `#e74c3c` (红色)
- **信息**: `#3498db` (蓝色)
- **背景**: `#010102` (深黑)
- **表面**: `#0f1011`, `#141516`, `#18191a`

### 排版
- 字体家族: Inter (系统无衬线字体 fallback)
- 字号层级: 12px - 32px
- 行高: 1.2 (标题) - 1.5 (正文)

### 间距
- 基础单位: 4px
- 标准间距: 8px, 12px, 16px, 24px, 32px, 48px

## 📦 核心组件

### Button 按钮
```tsx
<Button variant="primary" size="md" isLoading={false}>
  按钮文本
</Button>
```

变体: `primary`, `secondary`, `tertiary`, `danger`, `ghost`
尺寸: `sm`, `md`, `lg`

### Card 卡片
```tsx
<Card>
  <CardHeader>
    <CardTitle>标题</CardTitle>
    <CardDescription>描述文字</CardDescription>
  </CardHeader>
  <CardContent>内容区域</CardContent>
</Card>
```

## 🔧 开发指南

### 新增页面
1. 在 `src/pages/` 创建页面组件
2. 在 `src/App.tsx` 添加路由配置
3. 在 `src/components/layout/Sidebar.tsx` 添加导航菜单

### 新增组件
1. 在 `src/components/ui/` 添加基础组件
2. 在 `src/components/features/` 添加业务组件
3. 遵循现有组件的 TypeScript 类型规范

### 样式规范
- 使用 TailwindCSS 原子类
- 自定义主题变量定义在 `src/index.css` 的 `@theme` 块中
- 避免使用内联样式，优先使用 Tailwind 类

## 📊 质量指标阈值

| 指标 | 目标值 | 警告阈值 |
|------|--------|---------|
| 幻觉率 | < 3% | > 5% |
| 毒性评分 | < 0.05 | > 0.1 |
| 忠实度 | > 90% | < 85% |
| 相关性 | > 95% | < 90% |
| P95 延迟 | < 500ms | > 1000ms |

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件

---

**BeaverChain** - 让 AI 模型构建更简单 🦫
