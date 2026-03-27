# Codex Context Summary

更新时间：2026-03-26

本文件是当前项目的压缩上下文版，目标是保留核心决策、约束和下一步动作，尽量把体量控制在 `research.md` 的约 40% 到 55%。后续如果上下文变长，优先保留本文件，再按需回看 `research.md`。

## 项目目标

搭建一个电子烟线上商店新品自动检测系统，优先解决：

1. 按市场监控指定零售网站的新品发布。
2. 后续可扩展到产品热度监测，比如评论数增长、评分变化、价格变化、库存变化。
3. 尽量免费，第一阶段优先考虑 GitHub 仓库管理和轻量自动化。
4. 当前用户是小白，系统设计要尽量简单、可解释、可逐步升级。

## 当前主判断

- 第一阶段最重要的功能是“发现新品”，不是先做复杂热度模型。
- 最稳的新品判断方式是：某产品链接、SKU、handle 或产品 ID 首次出现在目标列表页中。
- 第一版监控对象应优先选：`New Arrivals`、`What's New`、`Latest`、支持按时间排序的分类页。
- 不推荐先盯首页，因为首页噪音很大。

## 当前推荐技术路线

### 推荐主线

第一版采用“轻量 Python + 配置文件 + 本地或 GitHub Actions 定时运行 + Markdown/JSON 报告”。

核心链路：

`站点配置 -> 抓取列表页 -> 提取产品 -> 和历史记录比对 -> 识别新品 -> 写入 state -> 生成报告`

### 为什么不是一开始就上复杂框架

- 用户当前更需要低门槛和可解释性。
- 很多目标站的新品列表页已经足够结构化，不需要先上 Scrapy 全家桶。
- 后面站点一多、动态页面一多，再升级到 Scrapy + Playwright 更合适。

## GitHub 的角色

GitHub 适合作为：

- 代码仓库
- 配置管理
- 轻量定时任务
- 静态报告展示

GitHub 不适合作为：

- 高频浏览器渲染平台
- 复杂登录态和强反爬的长期稳定运行环境

结论：GitHub 适合第一版试水，但不一定适合最终稳定平台。

## 已确认的通用系统框架

### 模块 A：站点清单

每个站点应配置：

- `site_id`
- `market`
- `base_url`
- `list_url`
- `platform`
- `fetch_mode`
- `check_interval`
- `supports_review_tracking`

### 模块 B：抓取

分两类：

- `http`：直接抓 HTML，便宜、快，适合大多数静态/半静态列表页
- `browser`：Playwright 渲染，适合动态页面、年龄验证、接口后加载场景

### 模块 C：提取

第一版只提：

- 产品名
- 产品 URL
- 产品唯一键
- 价格
- 是否售罄
- 评论数
- 首次发现时间

### 模块 D：差异检测

- 当前产品集合与历史集合做对比
- 新出现的记录记为新品
- 同一个产品的价格、评论数、库存状态变化则记为趋势或状态变更

### 模块 E：输出

第一版输出优先级：

1. `reports/*.md`
2. `data/state/*.json`
3. 后续再接飞书、邮件或网页面板

## 已调研的开源方向

### 第一推荐

[`dgtlmoon/changedetection.io`](https://github.com/dgtlmoon/changedetection.io)

适合快速验证“新品页面有没有新增内容”，优点是低代码、上手快；缺点是后期做结构化产品库和热度模型会受限。

### 第二推荐

[`scrapy/scrapy`](https://github.com/scrapy/scrapy)

适合第二阶段工程化，尤其是多市场、多站点和自定义逻辑增多之后。

### 强辅助

[`scrapy-plugins/scrapy-playwright`](https://github.com/scrapy-plugins/scrapy-playwright)

适合动态渲染页面。

## 美国站点最新观察

以下观察基于 2026-03-26 对指定站点页面的实际检查。

### 1. VaporDNA

- 入口：`https://vapordna.com/collections/whats-new`
- 页面可直接读取大量产品文本。
- 页面包含排序项 `Old -> New` 和 `New -> Old`。
- 列表页直接能看到产品名、价格、是否售罄、评论数。
- 页脚出现 `shopify.com` 链接，可确认是 Shopify 生态页面。

判断：

- 第一批最适合纳入。
- 可先用 `requests + BeautifulSoup` 跑。
- 热度监测可优先使用列表页评论数字段。

### 2. Mega Vape USA

- 入口：`https://megavapeusa.com/collections/new-disposables`
- 页面可直接读到产品名和价格。
- 页面显示 `15 products`，适合做新品集合对比。
- 站点多处出现 `Wholesale`、`Log In For Price`。
- 2026-03-26 页面顶部显示：`THIS WEB SITE IS CURRENTLY NOT OPORATIONAL !!! DO NOT PLACE ORDDERS !! THANK YOU`

判断：

- 技术上可抓。
- 业务上应降优先级，因为站点当前公开提示不可运营。
- 更像批发站，而不是典型零售站。

### 3. Vape City USA

- 入口：`https://vapecityusa.com/collections/new-arrivals`
- 页面可直接读到 `40 products`、产品名、价格、`New` 标记。
- 支持 `Date, new to old` 排序。
- 产品详情页可直接读到 `No reviews`、`Customer Reviews` 等文本。
- 详情页还能看到带 `shopify` 的库存或变体 JSON 片段。
- 页面存在 Cookie 和年龄验证文本，但未阻断主要内容读取。

判断：

- 第一批强烈建议纳入。
- 列表页负责新品发现，详情页负责评论数趋势。

### 4. Vapesourcing

- 用户给定入口：`https://vapesourcing.com/uswarehouse.html`
- 更适合的新品入口：`https://vapesourcing.com/usa-new-disposable-kit.html`
- 页面可直接读取产品名、价格、`New` 标签、评论数、结果总数。
- `.html` 类目录页较像自定义商城或 Magento 系电商风格，这是基于 URL 结构和目录页表现的推断。

判断：

- 第一批强烈建议纳入。
- 适合先走静态抓取。
- 新品入口应优先换成 `usa-new-disposable-kit.html`，比 `uswarehouse.html` 更聚焦新品。

### 5. Element Vape

- 入口：`https://www.elementvape.com/new-arrivals`
- 原始页面文本显示 `0 Display`。
- `Disposable` 和 `Vaporizers` 分类页同样显示 `0 Display`。

判断：

- 这是当前 5 个站里最难的一个。
- 静态 HTML 不足以拿到列表数据。
- 第一版应单独归类为 `browser` 或后续做接口逆向。
- 不建议它阻塞整个 MVP。

## 当前推荐分层策略

### 第一层：立刻做

- VaporDNA
- Vape City USA
- Vapesourcing

### 第二层：可做但降优先级

- Mega Vape USA

原因：当前页面公开提示站点不运营。

### 第三层：单独处理

- Element Vape

原因：需要浏览器渲染或接口分析。

## 已确定的工程思路

### 推荐项目骨架

- `config/`
- `src/new_product_detection/`
- `data/state/`
- `reports/`
- `scripts/`
- `.github/workflows/`

### 第一版不必做的事

- 不先做数据库服务
- 不先做网页后台
- 不先做品牌归一化
- 不先做 AI 分类
- 不先做全站搜索

## 下一步方向

下一步应以 `plan.md` 为执行蓝图，先搭一个美国市场 MVP：

1. 建站点配置文件。
2. 为 5 个站点建立 adapter。
3. 先跑新品检测。
4. 再为部分站点补评论数追踪。
5. 最后接 GitHub Actions 或本地定时运行。

## 使用规则

后续如果需要快速恢复上下文，优先读取：

1. `codex.md`
2. `plan.md`
3. `research.md`

其中：

- `codex.md` 负责压缩摘要
- `plan.md` 负责实施方案
- `research.md` 保留更完整的调研细节

## 实施优先级补充

### 立即纳入 MVP 的站点

- `vapordna_us`
- `vapecityusa_us`
- `vapesourcing_us`

原因：

- 页面内容在当前检查下可以直接读取。
- 新品入口明确。
- 至少部分页面可直接读取价格和评论相关文本。
- 这 3 个站足以证明“新品检测系统”是可行的。

### 第二批纳入的站点

- `megavapeusa_us`

原因：

- 技术上并不难抓。
- 但 2026-03-26 页面存在“当前不运营”的公开提示。
- 因此它更适合作为技术验证对象，而不是业务优先对象。

### 单独排期的站点

- `elementvape_us`

原因：

- 当前原始 HTML 无法直接给出产品列表。
- 很可能需要浏览器渲染或接口逆向。
- 它不应该阻塞前 3 到 4 个站的快速上线。

## 已知风险与处理原则

### 风险 1：站点样式会变

处理原则：

- 第一版优先依赖稳定特征，比如产品 URL 模式，而不是脆弱的深层 CSS 类名。
- 每个站独立 adapter，避免一个站改版拖垮全部逻辑。

### 风险 2：评论数并不是每个站都稳定可得

处理原则：

- 把评论追踪定义为“可选增强功能”。
- 先保证新品检测稳定，再补热度字段。

### 风险 3：GitHub Actions 不是长期完美运行环境

处理原则：

- 第一版把 GitHub 当作免费调度和结果展示平台。
- 如果后面站点增多、频率变高或浏览器任务变多，再迁移到本地常驻或 VPS。

### 风险 4：电子烟站点常见年龄验证、Cookie 弹窗、局部反爬

处理原则：

- 先尝试纯 HTTP。
- 如果只是前端弹窗但 HTML 里已经有列表数据，不要过早上浏览器。
- 只有静态抓取确实拿不到数据时，再升级到 Playwright。

## 保留决策

下面这些决策，在没有新证据前默认不变：

- 新品检测优先于热度分析。
- 列表页优先于首页。
- 轻量 Python 架构优先于直接上重框架。
- `codex.md` 作为后续最优先读取的上下文入口。
- `plan.md` 作为下一步实际实施蓝图。
