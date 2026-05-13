import { Search, Bell, User, ChevronDown } from 'lucide-react';

export function Header() {
  return (
    <header className="h-14 bg-surface-1 border-b border-hairline flex items-center justify-between px-6">
      {/* 左侧 - 页面标题 */}
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold text-ink">AI 模型构建平台</h1>
      </div>

      {/* 右侧 - 搜索、通知、用户 */}
      <div className="flex items-center gap-4">
        {/* 搜索框 */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-subtle" />
          <input
            type="text"
            placeholder="搜索模型、工作流..."
            className="w-64 pl-9 pr-4 py-1.5 bg-surface-2 border border-hairline rounded-md text-sm text-ink placeholder-ink-tertiary focus:outline-none focus:ring-2 focus:ring-primary-focus focus:border-transparent transition-all"
          />
        </div>

        {/* 通知按钮 */}
        <button className="relative p-2 rounded-md text-ink-muted hover:text-ink hover:bg-surface-2 transition-colors">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-semantic-error rounded-full"></span>
        </button>

        {/* 用户菜单 */}
        <div className="flex items-center gap-2 pl-4 border-l border-hairline">
          <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
            <User className="w-4 h-4 text-primary" />
          </div>
          <span className="text-sm font-medium text-ink">管理员</span>
          <ChevronDown className="w-4 h-4 text-ink-subtle" />
        </div>
      </div>
    </header>
  );
}
