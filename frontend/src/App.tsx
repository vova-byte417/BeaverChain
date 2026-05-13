import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import Dashboard from './pages/Dashboard';
import Models from './pages/Models';
import Workflows from './pages/Workflows';
import Evaluations from './pages/Evaluations';
import SettingsPage from './pages/Settings';

function App() {
  return (
    <Router>
      <div className="h-screen w-screen flex bg-canvas text-ink overflow-hidden">
        {/* 侧边栏 */}
        <Sidebar />

        {/* 主内容区 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* 顶部导航 */}
          <Header />

          {/* 页面内容 */}
          <main className="flex-1 overflow-y-auto p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/models" element={<Models />} />
              <Route path="/workflows" element={<Workflows />} />
              <Route path="/evaluations" element={<Evaluations />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
