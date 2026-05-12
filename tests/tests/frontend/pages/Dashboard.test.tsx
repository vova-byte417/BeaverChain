import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import Dashboard from '@/pages/Dashboard'

// Mock chart components
vi.mock('recharts', () => ({
  LineChart: () => <div data-testid="line-chart">Line Chart</div>,
  Line: () => <div>Line</div>,
  XAxis: () => <div>XAxis</div>,
  YAxis: () => <div>YAxis</div>,
  CartesianGrid: () => <div>Grid</div>,
  Tooltip: () => <div>Tooltip</div>,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  BarChart: () => <div data-testid="bar-chart">Bar Chart</div>,
  Bar: () => <div>Bar</div>,
  PieChart: () => <div data-testid="pie-chart">Pie Chart</div>,
  Pie: () => <div>Pie</div>,
  Cell: () => <div>Cell</div>,
}))

describe('Dashboard Page', () => {
  it('should render dashboard title', () => {
    render(<Dashboard />)
    expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument()
  })

  it('should display statistics cards', () => {
    render(<Dashboard />)
    
    // 应该有统计卡片
    expect(screen.getByText(/total models/i) || screen.getByText(/模型总数/i)).toBeInTheDocument()
    expect(screen.getByText(/active workflows/i) || screen.getByText(/运行中工作流/i)).toBeInTheDocument()
    expect(screen.getByText(/evaluation runs/i) || screen.getByText(/评估次数/i)).toBeInTheDocument()
  })

  it('should render charts', () => {
    render(<Dashboard />)
    
    expect(screen.getByTestId('line-chart')).toBeInTheDocument()
    expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
  })

  it('should display recent activity section', () => {
    render(<Dashboard />)
    expect(screen.getByText(/recent activity/i) || screen.getByText(/最近活动/i)).toBeInTheDocument()
  })

  it('should display quick actions', () => {
    render(<Dashboard />)
    expect(screen.getByRole('button', { name: /new model/i }) || screen.getByRole('button', { name: /新建模型/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /run evaluation/i }) || screen.getByRole('button', { name: /运行评估/i })).toBeInTheDocument()
  })
})
