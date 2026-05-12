import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Box,
  GitBranch,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  Bot,
} from 'lucide-react';
import { cn } from '../../utils/cn';

const navigation = [
  { name: '仪表盘', href: '/', icon: LayoutDashboard },
  { name: '模型管理', href: '/models', icon: Box },
  { name: '工作流编排', href: '/workflows', icon: GitBranch },
  { name: '评估中心', href: '/evaluations', icon: BarChart3 },
  { name: '配置管理', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  return (
    <div
      className={cn(
        'flex flex-col bg-surface-1 border-r border-hairline transition-all duration-300',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Logo 区域 */}
      <div className="flex items-center h-14 px-4 border-b border-hairline">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
            <Bot className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <span className="font-semibold text-ink">BeaverChain</span>
          )}
        </div>
      </div>

      {/* 导航菜单 */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-primary text-white'
                  : 'text-ink-muted hover:bg-surface-2 hover:text-ink'
              )}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </NavLink>
          );
        })}
      </nav>

      {/* 折叠按钮 */}
      <div className="p-3 border-t border-hairline">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md text-sm text-ink-muted hover:bg-surface-2 hover:text-ink transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <>
              <ChevronLeft className="w-5 h-5" />
              <span>收起菜单</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
