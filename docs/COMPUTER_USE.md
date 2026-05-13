# Computer-Use (CUA) 使用指南

本文档详细说明 BeaverChain 平台的 Computer-Use Agent (CUA) 功能使用方法。

> 🔴 **最高优先级技能**：根据系统配置，Computer-Use 技能已被设置为最高优先级，涉及 GUI 操作、浏览器控制、键鼠自动化等任务时会优先使用此技能。

## 📋 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [核心功能](#核心功能)
- [使用场景](#使用场景)
- [API 接口](#api-接口)
- [命令行工具](#命令行工具)
- [配置说明](#配置说明)
- [最佳实践](#最佳实践)
- [故障排查](#故障排查)

## 概述

### 什么是 Computer-Use Agent？

Computer-Use Agent (CUA) 是 BeaverChain 平台内置的智能 GUI 自动化代理，它可以：

- 🖱️ **控制鼠标键盘** - 模拟真实用户的键鼠操作
- 🌐 **浏览器自动化** - 访问网页、填写表单、点击按钮
- 📸 **屏幕截图分析** - 实时截图并理解屏幕内容
- 📊 **Office 文档操作** - Word、Excel、PowerPoint 自动化
- 🧠 **多步任务编排** - 智能规划复杂任务执行步骤
- 👀 **视觉理解** - 基于视觉的界面元素识别和定位

### 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                         用户任务描述                          │
│         "打开浏览器访问百度，搜索 AI，截图保存结果"            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        任务规划器                             │
│         解析任务 → 拆分子步骤 → 确定执行顺序                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        视觉感知层                             │
│         截图 → 图像分析 → 元素定位 → 坐标转换                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        动作执行层                             │
│         鼠标移动/点击 → 键盘输入 → 滚动 → 拖拽                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        结果验证层                             │
│         操作后截图 → 验证预期结果 → 失败重试/下一步            │
└─────────────────────────────────────────────────────────────┘
```

### 支持的平台

| 平台 | 支持状态 | 备注 |
|------|---------|------|
| Linux (X11) | ✅ 完全支持 | 推荐 Ubuntu 22.04+ |
| macOS | ✅ 完全支持 | 需要开启辅助功能权限 |
| Windows | ✅ 完全支持 | 推荐 Win 10/11 |
| Headless Linux | ✅ 支持 | 使用虚拟显示器 |
| Docker 容器 | ✅ 支持 | 需要特殊配置 |

## 快速开始

### 前置条件

1. **Python 环境**：Python 3.10+
2. **系统依赖**：
   ```bash
   # Ubuntu/Debian
   sudo apt install scrot xdotool wmctrl

   # macOS (使用 Homebrew)
   brew install cliclick

   # Windows (使用 Chocolatey)
   choco install autohotkey
   ```

3. **模型配置**：确保已配置支持多模态的模型

### 第一个 CUA 任务

#### 1. 启动 CUA 服务

```bash
# 启动 CUA 服务
cd backend
python -m cua.server --host 0.0.0.0 --port 8001
```

#### 2. 提交任务

```python
from cua.client import CUAClient

# 初始化客户端
client = CUAClient("http://localhost:8001")

# 提交任务
task = client.submit_task(
    task_description="""
    请完成以下操作：
    1. 打开浏览器
    2. 访问 https://www.baidu.com
    3. 在搜索框中输入 "人工智能"
    4. 点击搜索按钮
    5. 截图保存搜索结果
    """,
    max_steps=20,
    save_screenshots=True,
    headless=False
)

print(f"任务 ID: {task.task_id}")
print(f"任务状态: {task.status}")
```

#### 3. 查看执行结果

```python
# 等待任务完成
result = client.wait_for_completion(task.task_id, timeout=300)

# 查看执行步骤
for step in result.steps:
    print(f"Step {step.number}: {step.action}")
    print(f"  描述: {step.description}")
    print(f"  状态: {step.status}")
    if step.screenshot_path:
        print(f"  截图: {step.screenshot_path}")

# 查看最终结果
print(f"\n任务完成: {result.success}")
print(f"结果摘要: {result.summary}")
print(f"输出文件: {result.output_files}")
```

### 命令行快速执行

```bash
# 执行简单任务
cua run "打开计算器，计算 256 * 1024"

# 执行包含多步的复杂任务
cua run "
打开浏览器访问 google.com
搜索 'machine learning'
打开第一个搜索结果
截图保存到 report.png
" --max-steps 30

# 查看任务历史
cua list

# 查看特定任务详情
cua show <task-id>
```

## 核心功能

### 1. 浏览器自动化

#### 基础操作

```python
from cua import BrowserAgent

agent = BrowserAgent()

# 访问网页
agent.navigate("https://www.example.com")

# 填写表单
agent.fill_form(
    selector="#username",
    text="myusername"
)
agent.fill_form("#password", "mypassword")

# 点击按钮
agent.click_button("//button[contains(text(), '登录')]")

# 等待页面加载
agent.wait_for_page_load(timeout=30)

# 截图
agent.take_screenshot("login_result.png")
```

#### 高级操作

```python
# 滚动页面
agent.scroll(direction="down", amount=500)  # 向下滚动 500 像素

# 悬停元素
agent.hover_selector("#menu")

# 拖拽操作
agent.drag_and_drop(
    from_selector="#item-to-drag",
    to_selector="#drop-target"
)

# 处理弹窗
agent.handle_alert(accept=True)

# 切换 iframe
agent.switch_to_iframe("frame-name")
```

#### 真实场景：Web 自动化测试

```python
def test_ecommerce_checkout():
    """电商结账流程测试"""
    agent = BrowserAgent()

    # 1. 访问商品页面
    agent.navigate("https://shop.example.com/product/123")

    # 2. 添加到购物车
    agent.click_button("Add to Cart")
    agent.wait_for_element(".cart-count", text="1")

    # 3. 进入结账页面
    agent.click_button("Checkout")

    # 4. 填写收货地址
    agent.fill_form("#name", "张三")
    agent.fill_form("#address", "北京市朝阳区xxx路xxx号")
    agent.fill_form("#phone", "13800138000")

    # 5. 选择支付方式并提交
    agent.click("#payment-alipay")
    agent.click_button("Submit Order")

    # 6. 验证结果
    agent.wait_for_page_contain("订单提交成功")
    agent.take_screenshot("order_success.png")

    print("✅ 结账流程测试通过")
```

### 2. 桌面应用自动化

#### 文件管理器操作

```python
from cua import DesktopAgent

agent = DesktopAgent()

# 打开文件管理器
agent.open_app("nautilus")

# 导航到目录
agent.type_text("/home/user/documents")
agent.press_key("Enter")

# 创建新文件夹
agent.right_click(100, 100)  # 在指定坐标右键
agent.type_text("New Folder")
agent.press_key("Enter")
agent.type_text("project_files")
agent.press_key("Enter")
```

#### 文本编辑器操作

```python
from cua import EditorAgent

agent = EditorAgent(editor="code")  # 使用 VS Code

# 打开文件
agent.open_file("/path/to/project/main.py")

# 跳转到特定行
agent.goto_line(42)

# 编辑代码
agent.select_line()
agent.type_text("    print('Hello, BeaverChain!')")

# 保存文件
agent.save()
agent.close()
```

### 3. Office 文档自动化

#### Word 文档操作

```python
from cua.office import WordDocument

# 创建新文档
doc = WordDocument()
doc.create()

# 添加标题
doc.add_heading("项目报告", level=1)

# 添加段落
doc.add_paragraph("""
本报告总结了项目的关键成果和进展。
主要包括以下几个方面：
""")

# 添加列表
doc.add_bullet_list([
    "需求分析完成",
    "架构设计评审通过",
    "核心功能开发中",
    "测试用例编写中"
])

# 添加表格
data = [
    ["阶段", "进度", "负责人"],
    ["需求分析", "100%", "张三"],
    ["架构设计", "100%", "李四"],
    ["开发实现", "60%", "王五"],
    ["测试验证", "20%", "赵六"],
]
doc.add_table(data)

# 保存文档
doc.save("project_report.docx")
```

#### Excel 表格操作

```python
from cua.office import ExcelDocument

# 打开现有表格
excel = ExcelDocument("sales_data.xlsx")

# 读取数据
data = excel.read_range("A1:C10")
print(data)

# 写入数据
excel.write_cell("D2", "=B2*C2")

# 添加图表
excel.add_chart(
    chart_type="bar",
    data_range="A1:C10",
    title="月度销售数据",
    position="E1"
)

# 应用格式
excel.apply_format(
    range="A1:C1",
    bold=True,
    background_color="#4472C4",
    font_color="white"
)

# 保存
excel.save()
```

#### PowerPoint 演示文稿

```python
from cua.office import PowerPointDocument

# 创建演示文稿
ppt = PowerPointDocument()

# 添加标题幻灯片
ppt.add_title_slide(
    title="BeaverChain 产品发布会",
    subtitle="企业级大模型构建平台"
)

# 添加内容幻灯片
ppt.add_content_slide(
    title="核心功能",
    bullets=[
        "🚀 一键模型部署",
        "⚡ 量化优化加速",
        "🔧 完整的 API 接口",
        "📊 实时监控面板"
    ]
)

# 添加带图片的幻灯片
ppt.add_image_slide(
    title="架构概览",
    image_path="architecture.png",
    caption="图 1: 系统整体架构"
)

# 保存
ppt.save("product_presentation.pptx")
```

### 4. 截图与视觉分析

#### 基础截图功能

```python
from cua import ScreenshotAnalyzer

analyzer = ScreenshotAnalyzer()

# 截取全屏
screenshot = analyzer.take_screenshot()
screenshot.save("full_screen.png")

# 截取指定区域
screenshot = analyzer.take_screenshot(
    region=(x, y, width, height)
)

# 截取特定窗口
screenshot = analyzer.take_window_screenshot("Firefox")
```

#### 视觉元素定位

```python
# 查找按钮位置
button_pos = analyzer.find_button("登录")
print(f"登录按钮位置: {button_pos}")

# 查找文本输入框
input_pos = analyzer.find_input_field("搜索")
print(f"搜索框位置: {input_pos}")

# 查找包含特定文本的区域
regions = analyzer.find_text_on_screen("人工智能")
for region in regions:
    print(f"找到文本在: {region.bbox}")
    analyzer.highlight_region(region.bbox)
```

#### OCR 文字识别

```python
# 对截图进行 OCR
result = analyzer.ocr_analyze(screenshot)

# 打印识别到的文字
for text_item in result.texts:
    print(f"文本: {text_item.content}")
    print(f"位置: {text_item.bbox}")
    print(f"置信度: {text_item.confidence}")

# 搜索特定文本
matches = result.search("BeaverChain")
for match in matches:
    print(f"找到匹配: {match.content} at {match.bbox}")
```

### 5. 任务规划与重试机制

#### 智能任务规划

```python
from cua import TaskPlanner

planner = TaskPlanner()

# 复杂任务自动拆分为步骤
task = planner.plan("""
请给我生成一份完整的销售报告：
1. 打开 Excel 销售数据文件
2. 汇总本月销售数据
3. 创建销售图表
4. 将图表复制到 Word 报告中
5. 保存并发送邮件给经理
""")

# 查看计划的步骤
for i, step in enumerate(task.steps, 1):
    print(f"Step {i}: {step.description}")
    print(f"  预期动作: {step.action}")
    print(f"  依赖: {step.depends_on}")
```

#### 自动重试和错误恢复

```python
from cua import RobustExecutor

executor = RobustExecutor(max_retries=3)

@executor.retry_on_failure
def click_login_button():
    """点击登录按钮，失败自动重试"""
    agent = BrowserAgent()
    agent.click_button("登录")
    agent.wait_for_page_contain("欢迎")

# 带重试策略的执行
result = executor.execute(
    task=click_login_button,
    retry_on=[TimeoutError, ElementNotFoundError],
    backoff="exponential"  # 指数退避
)

# 查看执行统计
print(f"尝试次数: {result.attempts}")
print(f"是否成功: {result.success}")
print(f"总耗时: {result.total_time}s")
```

## 使用场景

### 场景 1: Web 应用自动化测试

```python
"""
场景: 测试用户注册流程
"""
from cua import BrowserAgent

def test_user_registration():
    agent = BrowserAgent()

    # 1. 访问注册页面
    agent.navigate("https://example.com/register")

    # 2. 填写注册表单
    agent.fill_form("#username", "testuser")
    agent.fill_form("#email", "testuser@example.com")
    agent.fill_form("#password", "SecurePass123!")
    agent.fill_form("#confirm_password", "SecurePass123!")

    # 3. 同意条款并提交
    agent.click("#agree_terms")
    agent.click_button("注册")

    # 4. 验证注册成功
    agent.wait_for_page_contain("注册成功")

    # 5. 验证验证邮件提示
    assert agent.page_contains("验证邮件已发送")

    # 6. 保存证据截图
    agent.take_screenshot("registration_success.png")

    print("✅ 用户注册流程测试通过")
```

### 场景 2: 数据录入自动化

```python
"""
场景: 从 CSV 批量录入数据到 Web 表单
"""
import csv
from cua import BrowserAgent

def batch_data_entry(csv_path: str):
    agent = BrowserAgent()
    agent.navigate("https://example.com/data-entry")

    # 登录系统
    agent.fill_form("#username", "admin")
    agent.fill_form("#password", "admin123")
    agent.click_button("登录")

    # 读取 CSV 数据
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            print(f"正在录入第 {i} 条数据...")

            # 填写表单
            agent.fill_form("#name", row["姓名"])
            agent.fill_form("#department", row["部门"])
            agent.fill_form("#position", row["职位"])
            agent.fill_form("#salary", row["薪资"])

            # 提交
            agent.click_button("保存")

            # 等待保存完成
            agent.wait_for_element_to_disappear("#loading-spinner")

            # 验证保存成功
            if agent.page_contains("保存成功"):
                print(f"  ✅ 第 {i} 条数据录入成功")
            else:
                print(f"  ❌ 第 {i} 条数据录入失败")
                agent.take_screenshot(f"error_entry_{i}.png")

            # 点击新建，准备下一条
            agent.click_button("新建记录")

    print(f"\n✅ 批量录入完成，共 {i} 条记录")
```

### 场景 3: 报告生成自动化

```python
"""
场景: 自动生成每周项目报告
"""
from datetime import datetime
from cua.office import WordDocument, ExcelDocument
from cua import BrowserAgent

def generate_weekly_report():
    # 1. 从项目管理系统获取数据
    browser = BrowserAgent()
    browser.navigate("https://project.example.com/dashboard")

    # 登录（如果需要）
    if browser.page_contains("登录"):
        browser.fill_form("#username", "report_bot")
        browser.fill_form("#password", "bot_password")
        browser.click_button("登录")

    # 2. 导出本周数据
    browser.click_button("导出数据")
    browser.select_option("#time_range", "本周")
    browser.click_button("下载 Excel")
    browser.wait_for_download_complete()

    # 3. 处理 Excel 数据
    excel = ExcelDocument(browser.get_latest_download())
    metrics = excel.calculate_summary({
        "完成任务数": "SUM(B:B)",
        "进行中任务": "COUNTIF(C:C, \"进行中\")",
        "团队平均速度": "AVERAGE(D:D)"
    })

    # 4. 生成 Word 报告
    doc = WordDocument()
    doc.create()

    # 添加报告标题
    today = datetime.now().strftime("%Y年%m月%d日")
    doc.add_heading(f"项目周报 - {today}", level=1)

    # 添加概览部分
    doc.add_heading("一、关键指标", level=2)
    doc.add_bullet_list([
        f"✅ 完成任务数: {metrics['完成任务数']}",
        f"🔄 进行中任务: {metrics['进行中任务']}",
        f"📊 团队平均速度: {metrics['团队平均速度']} 点/天"
    ])

    # 添加数据表格
    doc.add_heading("二、详细数据", level=2)
    doc.add_excel_table(excel, range="A1:E20")

    # 5. 保存报告
    report_path = f"weekly_report_{datetime.now().strftime('%Y%m%d')}.docx"
    doc.save(report_path)

    print(f"✅ 周报已生成: {report_path}")
    return report_path
```

### 场景 4: UI 回归测试

```python
"""
场景: UI 界面回归测试 - 验证不同分辨率下的显示效果
"""
from cua import BrowserAgent, ScreenshotAnalyzer

def ui_regression_test():
    agent = BrowserAgent()
    analyzer = ScreenshotAnalyzer()

    test_resolutions = [
        (1920, 1080),  # Full HD
        (1366, 768),   # 笔记本
        (375, 667),    # 手机
        (768, 1024),   # 平板
    ]

    test_pages = [
        "/",
        "/dashboard",
        "/models",
        "/deployments",
        "/settings"
    ]

    for width, height in test_resolutions:
        print(f"\n测试分辨率: {width}x{height}")
        agent.set_window_size(width, height)

        for page in test_pages:
            print(f"  测试页面: {page}")
            agent.navigate(f"https://example.com{page}")
            agent.wait_for_page_load()

            # 截图
            screenshot = agent.take_screenshot()

            # 与基线截图对比
            baseline = analyzer.load_baseline(f"baseline_{page}_{width}x{height}.png")
            diff = analyzer.compare_images(screenshot, baseline)

            if diff.percentage > 0.02:  # 允许 2% 差异
                print(f"    ❌ 检测到差异: {diff.percentage:.1%}")
                diff.save(f"diff_{page}_{width}x{height}.png")
            else:
                print(f"    ✅ 无显著差异")

    print("\n✅ UI 回归测试完成")
```

## API 接口

### REST API

#### 提交任务

```http
POST /api/v1/cua/tasks
Content-Type: application/json

{
  "task_description": "打开浏览器访问百度，搜索 AI",
  "max_steps": 20,
  "headless": false,
  "save_screenshots": true,
  "timeout_seconds": 300
}
```

**响应:**

```json
{
  "task_id": "cua-task-abc123",
  "status": "running",
  "created_at": "2024-05-13T10:00:00Z",
  "estimated_completion": "2024-05-13T10:05:00Z"
}
```

#### 查询任务状态

```http
GET /api/v1/cua/tasks/{task_id}
```

**响应:**

```json
{
  "task_id": "cua-task-abc123",
  "status": "completed",
  "current_step": 15,
  "total_steps": 15,
  "progress": 100,
  "started_at": "2024-05-13T10:00:00Z",
  "completed_at": "2024-05-13T10:03:45Z",
  "result": {
    "success": true,
    "summary": "成功访问百度并搜索 AI",
    "output_files": [
      "/data/cua/runs/abc123/step_5.png",
      "/data/cua/runs/abc123/step_10.png",
      "/data/cua/runs/abc123/final_result.png"
    ]
  }
}
```

#### 获取任务步骤详情

```http
GET /api/v1/cua/tasks/{task_id}/steps
```

**响应:**

```json
{
  "task_id": "cua-task-abc123",
  "steps": [
    {
      "step_number": 1,
      "action": "open_app",
      "description": "打开浏览器",
      "status": "success",
      "start_time": "2024-05-13T10:00:01Z",
      "end_time": "2024-05-13T10:00:05Z",
      "screenshot_path": "/data/cua/runs/abc123/step_1.png"
    }
    // ... 更多步骤
  ]
}
```

#### 获取截图

```http
GET /api/v1/cua/tasks/{task_id}/screenshots/{step}
```

#### 中断任务

```http
POST /api/v1/cua/tasks/{task_id}/interrupt
```

### Python SDK

```python
from cua import CUAClient

# 初始化客户端
client = CUAClient(
    base_url="http://localhost:8001",
    api_key="your-api-key"
)

# 同步执行任务
result = client.run_task(
    "打开浏览器访问百度，搜索 '大模型'",
    max_steps=20
)

# 异步提交任务
task_id = client.submit_task("...")

# 轮询状态
while True:
    status = client.get_task_status(task_id)
    print(f"进度: {status.progress}%")
    if status.status in ["completed", "failed"]:
        break
    time.sleep(5)

# 获取结果
result = client.get_task_result(task_id)
```

## 命令行工具

### 基本命令

```bash
# 执行任务
cua run "任务描述"
cua run --max-steps 30 --timeout 600 "任务描述"

# 查看任务列表
cua list
cua list --limit 10  # 最近 10 个任务

# 查看任务详情
cua show <task-id>

# 查看任务步骤
cua steps <task-id>

# 获取任务截图
cua screenshot <task-id> <step-number>
cua screenshot <task-id> --all  # 所有步骤截图

# 取消任务
cua cancel <task-id>

# 重试失败任务
cua retry <task-id>
```

### 配置文件

`~/.cua/config.yaml`:

```yaml
server:
  url: http://localhost:8001
  api_key: your-api-key

task:
  max_steps: 20
  timeout_seconds: 300
  save_screenshots: true
  headless: false

model:
  provider: ark
  base_url: https://ark.cn-beijing.volces.com/api/v3
  model_id: doubao-seed-code

storage:
  runs_dir: ~/.cua/runs
  screenshot_quality: 85
  keep_runs_days: 30
```

## 配置说明

### 核心配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `model.provider` | `ark` | 模型提供商 |
| `model.base_url` | - | API 端点 |
| `model.model_id` | `doubao-seed-code` | 多模态模型 ID |
| `task.max_steps` | `20` | 最大步骤数 |
| `task.timeout_seconds` | `300` | 超时时间（秒） |
| `task.save_screenshots` | `true` | 是否保存每步截图 |
| `task.headless` | `false` | 是否无头模式 |

### 视觉识别配置

```yaml
vision:
  ocr_enabled: true
  ocr_language: chs  # chs=简体中文, cht=繁体中文, eng=英文
  element_confidence_threshold: 0.8
  screenshot_quality: 90
  compare_tolerance: 0.02  # 图片比较容忍度
```

### 浏览器配置

```yaml
browser:
  default_browser: chrome  # chrome, firefox, edge
  headless: false
  user_agent: "Mozilla/5.0 ... BeaverCrawler/1.0"
  timeout: 30
  window_size: [1920, 1080]
  download_dir: ~/Downloads
```

## 最佳实践

### 1. 任务描述编写指南

**❌ 不好的任务描述:**
```
"处理一下那个报表"
```

**✅ 好的任务描述:**
```
"1. 打开 Excel 文件 sales_report_may.xlsx
2. 选择 '汇总' 工作表
3. 选中数据区域 A1:D20
4. 插入柱状图
5. 将图表标题设置为 '五月销售数据'
6. 保存文件"
```

**任务描述最佳实践:**
- ✅ 分解为清晰的步骤
- ✅ 使用明确的动词（打开、点击、输入、选择）
- ✅ 指定文件名、菜单项、按钮文本等精确信息
- ✅ 说明预期结果
- ❌ 不要使用模糊的指代（"那个"、"处理一下"）
- ❌ 不要假设上下文
- ❌ 不要省略关键信息

### 2. 错误处理和恢复

```python
from cua import CUAClient, CUARetryStrategy

# 配置重试策略
strategy = CUARetryStrategy(
    max_retries=3,
    retry_on=[
        "ElementNotFoundError",
        "TimeoutError",
        "ClickInterceptedError"
    ],
    backoff_factor=2,  # 指数退避
    screenshot_on_error=True
)

client = CUAClient(retry_strategy=strategy)

# 执行任务
try:
    result = client.run_task("复杂的多步任务")
except ElementNotFoundError as e:
    print(f"元素未找到: {e.element_name}")
    # 尝试替代方案
    result = client.run_task("使用备用路径的任务描述")
except TimeoutError:
    print("任务超时，检查网络连接或增加超时时间")
```

### 3. 性能优化

| 优化项 | 建议值 | 说明 |
|--------|--------|------|
| `screenshot_quality` | 70-85 | 降低图片质量可显著加快处理 |
| `max_steps` | 10-30 | 单任务不要太复杂，拆分为多个任务 |
| `headless` | `true` | 服务器环境使用无头模式 |
| 并发任务数 | 1-4 | 受 GPU 显存限制 |

### 4. 安全最佳实践

- 🔒 **隔离环境运行**：CUA 拥有完全的系统访问权限，建议在隔离的虚拟机或容器中运行
- 🔒 **最小权限原则**：不要用 root/administrator 运行 CUA
- 🔒 **网络隔离**：限制 CUA 只能访问必要的网络资源
- 🔒 **输入验证**：对外部传入的任务描述进行严格验证
- 🔒 **审计日志**：完整记录所有 CUA 操作，便于安全审计

## 故障排查

### 常见问题

#### 问题 1: 找不到页面元素

**症状:**
```
ElementNotFoundError: Could not find button "登录"
```

**解决方案:**
1. 检查选择器是否正确
2. 增加等待时间：`agent.wait_for_element(selector, timeout=30)`
3. 尝试不同的定位方式：CSS 选择器 → XPath → 文本匹配 → 图像匹配
4. 检查是否在 iframe 中
5. 检查是否有弹窗遮挡

#### 问题 2: 点击没有效果

**症状:** 点击操作成功返回，但页面没有变化

**解决方案:**
1. 检查坐标是否正确
2. 尝试多次点击
3. 等待页面完全加载后再操作
4. 检查元素是否被其他元素遮挡
5. 尝试 JavaScript 点击替代原生点击

#### 问题 3: OCR 识别不准确

**症状:** 找不到预期的文字，或识别到错误的文字

**解决方案:**
1. 提高截图分辨率
2. 放大屏幕或浏览器缩放比例
3. 调整 OCR 语言设置（`ocr_language`）
4. 使用更精确的区域截取
5. 考虑使用模板匹配替代 OCR

#### 问题 4: 任务执行缓慢

**症状:** 每步执行需要 10 秒以上

**优化建议:**
1. 减少截图分辨率
2. 关闭不必要的截图保存
3. 使用更快的 GPU 进行视觉推理
4. 调整 `step_delay` 配置（但要注意稳定性）
5. 拆分为多个并行任务

#### 问题 5: 模型配置错误

**症状:**
```
ModelError: Invalid combination of reasoning_effort and thinking type
```

**解决方案:**
1. 检查模型是否支持多模态
2. 禁用 `reasoning_effort` 参数
3. 检查 API 端点是否正确
4. 验证 API Key 权限

### 诊断工具

```bash
# 运行系统诊断
cua doctor

# 检查依赖
cua doctor --dependencies

# 检查模型连接
cua doctor --model

# 检查显示环境
cua doctor --display

# 生成完整诊断报告
cua doctor --report diagnostics_report.txt
```

### 日志查看

```bash
# 查看实时日志
cua logs --follow

# 查看特定任务的日志
cua logs --task <task-id>

# 查看错误日志
cua logs --level error

# 导出日志
cua logs --export run_logs.txt
```

### 获取帮助

如遇到本文档未涵盖的问题：

1. 📖 查看运行日志：`cua logs`
2. 🔍 运行诊断工具：`cua doctor`
3. 📝 在 GitHub 提交 Issue
4. 📧 联系技术支持

---

**文档版本**: v1.0.0  
**最后更新**: 2024-05-13  
**CUA 版本**: 2.3.0
