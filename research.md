# 电子烟线上商店新品自动检测系统调研

更新时间：2026-03-26

## 先说结论

- 如果你的目标是“免费 + 尽快跑起来 + 你现在还是小白”，我不建议一开始就把 GitHub 当成完整的长期监控平台。
- 最稳的第一版思路是：监控“新品列表页/分类页/搜索结果页” -> 抽取产品卡片 -> 和历史记录比对 -> 发现新产品就提醒。
- “监测某款产品热度”是可以做的，但更适合放在第二层：先发现新品，再持续记录该产品页的评论数、评分数、价格、库存变化。
- 从我调研的 GitHub 开源仓库看，最适合作为你第一阶段参考或直接采用的是 [`dgtlmoon/changedetection.io`](https://github.com/dgtlmoon/changedetection.io)；如果后面要做成更强的定制爬虫，Python 方向优先看 [`scrapy/scrapy`](https://github.com/scrapy/scrapy) 和 [`scrapy-plugins/scrapy-playwright`](https://github.com/scrapy-plugins/scrapy-playwright)。

## 1. 用大白话解释这套系统怎么工作

你可以把这个系统理解成“一个会定时去逛网站的数字助理”。

它的工作顺序很简单：

1. 你给它一个市场和若干网址，比如美国站、德国站、英国站的“新品页”或“某分类页”。
2. 系统定时打开这些网页。
3. 系统把页面里的产品卡片信息摘出来，比如产品名、链接、价格、图片、评论数。
4. 系统把这次看到的结果，和上一次保存的结果做比较。
5. 如果出现了以前没见过的产品链接或产品 ID，就把它标记为“新品”。
6. 系统把新品写进数据库或表格，并把提醒发给你。
7. 如果你还想看热度，系统就继续每天去看这个产品详情页，记录评论数和评分数是不是涨得快。

一句话概括：

`监控页面 -> 抽取字段 -> 和历史比对 -> 发现新品 -> 记录趋势 -> 发提醒`

## 2. 为什么“先盯新品列表页”最重要

“跟踪发布新品”这件事，最核心不是先做复杂 AI，而是先选对页面。

优先级建议如下：

1. 最优先监控：`New Arrivals / New Products / Just In / Latest` 这类页面。
2. 第二优先：分类页，前提是页面支持“按最新排序”。
3. 第三优先：站内搜索页，比如某个关键词或品牌的搜索结果页。
4. 最不推荐直接盯首页，因为首页广告位、横幅、推荐位经常变化，噪音很大。

为什么这样做最稳：

- 列表页天然就是“产品集合”，最容易发现“新增成员”。
- 只要产品 URL、SKU、handle、产品名里有一个稳定字段，就能做去重。
- 这类页面通常比详情页更轻，也更适合低成本定时抓取。

## 3. “新品”到底怎么判断

我建议第一版把“新品”定义得非常朴素：

- 某个产品链接第一次出现在被监控页面中。
- 或者某个产品 ID / SKU / handle 第一次出现。
- 如果站点字段不稳定，就退而求其次，用“产品名 + 链接”组合作为唯一键。

第一版不要把“新品”定义成太复杂的东西，比如：

- 标题里带 `new`
- 图片角标写了 `new`
- 评论很少

这些都可以当辅助信号，但不适合作为第一判断条件，因为误判会很多。

## 4. 热度监测能不能做

可以做，但要分难度。

### 最容易做的情况

页面 HTML 或 JSON-LD 里直接有这些字段：

- `reviewCount`
- `ratingCount`
- `ratingValue`
- `price`
- `availability`

Schema.org 的 `AggregateRating` 明确包含 `ratingCount` 和 `reviewCount` 属性，所以如果电商站点在页面里埋了结构化数据，这条路会很顺。[Schema.org AggregateRating](https://schema.org/AggregateRating)

### 中等难度的情况

评论不是写在 HTML 里，而是页面加载后再调用接口拿数据。

这时系统可以：

- 用浏览器自动化把页面渲染出来后再取值。
- 或者直接分析网页请求的接口，定时请求那个评论 API。

### 最难的情况

如果目标站点有这些特征，难度会明显上升：

- Cloudflare / Turnstile / 验证码
- 强登录限制
- 年龄验证弹窗之后还叠加接口签名
- 评论数据来自第三方组件并且频繁变 token

对电子烟网站，我的推断是：年龄验证弹窗、Cookie 弹窗很常见；这类问题通常能用浏览器自动化步骤处理。但如果上到强验证码或强反爬，就不适合拿 GitHub Actions 做长期稳定监控，后面更适合本地机器或便宜 VPS。

## 5. 给小白的逻辑框架

不要把它想成“大而全平台”，先把它拆成 5 个小模块：

### 模块 A：目标站点清单

你维护一份站点表：

- 市场：美国 / 德国 / 英国
- 站点名
- 监控 URL
- 页面类型：新品页 / 分类页 / 搜索页 / 详情页
- 检查频率

### 模块 B：页面采集

系统定时抓网页内容。

分两种：

- 轻量抓取：直接请求 HTML，便宜、快。
- 浏览器抓取：用 Playwright 这类工具打开页面，适合 JS 重的网站。

### 模块 C：字段抽取

从页面里提取你真正在意的内容：

- 产品名
- 产品 URL
- SKU 或唯一 ID
- 价格
- 库存状态
- 评论数
- 评分数

### 模块 D：差异比较

把“今天看到的产品集合”和“昨天保存的产品集合”做对比。

- 新出现：记为新品
- 价格变了：记为价格变化
- 评论数涨了：记为热度增长
- 缺货变有货：记为库存变化

### 模块 E：提醒与展示

最后把结果发给你看。

第一版最简单的输出方式可以是：

- Markdown 报告
- CSV / Excel
- 飞书机器人 / 邮件 / Telegram / Discord 通知
- 静态网页仪表盘

## 6. 免费和 GitHub 部署，到底推不推荐

我的判断是：

- GitHub 很适合做“代码仓库 + 配置管理 + 轻量定时任务 + 静态报告展示”。
- GitHub 不太适合做“重浏览器爬虫 + 高频监控 + 复杂登录态 + 需要长期稳定常驻的监控后端”。

### GitHub 适合你的地方

- 免费保存代码、配置、历史结果。
- 可以用 GitHub Actions 定时跑脚本。
- 可以用 GitHub Pages 放一个静态结果页面。
- 对小白来说，版本管理和协作比自己搭服务器更轻。

### GitHub 不适合你的地方

GitHub 官方文档显示：

- 定时工作流最短只能每 5 分钟运行一次。
- 定时工作流只会在默认分支上运行。
- 高峰期可能延迟，严重时排队任务可能被丢弃。
- 公共仓库如果 60 天没有活动，定时工作流会被自动禁用。
- 公共仓库使用标准 GitHub-hosted runner 是免费的；私有仓库则受免费分钟数配额限制。

这些约束意味着：

- 如果你要做“每 15 分钟扫一次 10 个列表页”的轻量 MVP，GitHub 可以。
- 如果你要做“几十个站点 + 浏览器渲染 + 登录态 + 高可靠提醒”，GitHub 不够稳。

### 我对你现阶段的建议

如果你只想先做出结果，我建议按下面优先级选：

1. `最适合小白`：本地电脑或轻量 Docker 跑低代码监测工具。
2. `最适合纯免费试水`：GitHub 仓库 + GitHub Actions + 简单 Python 脚本 + 静态报告。
3. `后期更稳`：便宜 VPS 跑自定义服务。

换句话说：

- GitHub 适合做第一版试水。
- GitHub 不一定是最终形态。

## 7. GitHub 开源仓库深度调研

下面是我按“新品发布监测”这个主目标做的筛选。

| 仓库 | 截至 2026-03-26 的公开情况 | 定位 | 对你是否适合 | 结论 |
| --- | --- | --- | --- | --- |
| [`dgtlmoon/changedetection.io`](https://github.com/dgtlmoon/changedetection.io) | 约 30.8k stars，最新 release `0.54.6`（2026-03-17） | 网站变更监测平台 | 非常适合第一阶段 | 第一推荐 |
| [`scrapy/scrapy`](https://github.com/scrapy/scrapy) | 约 61k stars，最新 release `2.14.2`（2026-03-18） | Python 爬虫框架 | 适合第二阶段定制化 | 第二推荐 |
| [`scrapy-plugins/scrapy-playwright`](https://github.com/scrapy-plugins/scrapy-playwright) | 约 1.4k stars，最新 release `v0.0.46`（2026-01-21） | Scrapy 的 JS 渲染补强 | 适合动态页面 | 强辅助组件 |
| [`apify/crawlee`](https://github.com/apify/crawlee) | 约 22.5k stars，最新 release `v3.16.0`（2026-02-06） | Node.js/TS 爬虫与浏览器自动化 | 适合 JS/TS 体系 | 可选替代 |
| [`huginn/huginn`](https://github.com/huginn/huginn) | 约 49k stars，最新 release `v2022.08.18`（2022-08-18） | 类 IFTTT/Zapier 的自托管自动化平台 | 思路强，但上手成本偏高 | 不作首选 |
| [`paschmann/changd`](https://github.com/paschmann/changd) | 约 172 stars，最新 release `v1.3.0`（2022-07-12） | 视觉截图/XPath/API 监测 | 适合视觉变更和截图对比 | 小众备选 |
| [`wezm/rsspls`](https://github.com/wezm/rsspls) | 约 393 stars，最新 release `0.11.2`（2026-01-05） | 把网页转换成 RSS feed | 适合简单列表页订阅 | 轻量备选 |
| [`subreme/shopify-monitor`](https://github.com/subreme/shopify-monitor) | 41 stars，最新 release `v0.1.2`（2021-12-21） | Shopify 商店变动监测 | 只适合 Shopify 站点 | 平台特化方案 |

### 7.1 第一推荐：changedetection.io

仓库：[`dgtlmoon/changedetection.io`](https://github.com/dgtlmoon/changedetection.io)

我为什么把它排第一：

- 它就是专门做网页变化监测的。
- 它支持监测页面局部内容，不是只能看整页有没有变。
- 它支持浏览器步骤，可以点击按钮、填输入框、接受 Cookie、做简单交互。
- 它本身就支持价格变化、补货提醒、JSON 变化、提取文本等场景。

对于你的场景，它最有价值的点是：

- 先监控“新品列表页”，只提取产品卡片区域。
- 如果站点有年龄弹窗或 Cookie 弹窗，能通过 browser steps 先处理。
- 可以先不写太多代码，就把“页面是否出现新产品”跑起来。

它的短板也要说清楚：

- 它更像“监控平台”，不是专门为“产品库建模”设计的。
- 如果你后面要做复杂的数据表、跨站点去重、品牌归一化、热度评分，它就会显得不够灵活。
- 如果要放在 GitHub Actions 上长期跑，不是最舒服的形态，因为它更适合有持久化存储的本地/Docker/VPS 场景。

我的结论：

- 如果你想最快验证“新品监控”是否可行，它是最值得先试的仓库。

### 7.2 第二推荐：Scrapy

仓库：[`scrapy/scrapy`](https://github.com/scrapy/scrapy)

它不是现成成品，而是框架。

优点：

- Python 生态成熟，教程多。
- 很适合把“站点清单 -> 解析器 -> 存储 -> 去重 -> 导出”做成正式项目。
- 一旦你开始监控多个市场、多个站点，Scrapy 的结构化优势会很明显。

缺点：

- 对小白来说，第一周的学习门槛高于 changedetection.io。
- 你需要自己写解析逻辑，不是开箱即用的 UI 产品。

我的结论：

- 它不是你最省力的第一步，但很可能是你后续真正可扩展的主框架。

### 7.3 强辅助：scrapy-playwright

仓库：[`scrapy-plugins/scrapy-playwright`](https://github.com/scrapy-plugins/scrapy-playwright)

它的定位很明确：给 Scrapy 加浏览器能力。

适合什么时候上它：

- 页面是 JS 渲染的。
- 需要等待列表加载。
- 需要点击“接受年龄验证”或“加载更多”。
- 评论数是渲染后才出现的。

它不是独立平台，而是 Scrapy 的加强件。

我的结论：

- 只要你后面发现目标站点是动态页面，它几乎就是 Python 路线的标配补充。

### 7.4 JS/TS 方向可选：Crawlee

仓库：[`apify/crawlee`](https://github.com/apify/crawlee)

优点：

- HTTP 抓取和浏览器抓取能统一起来。
- 提供队列、存储、会话、代理等能力。
- 对现代 JS 网站友好。

缺点：

- 你现在是小白，如果你也不熟 Node.js，这条路并不会比 Python 更轻松。
- 对你当前阶段来说，Crawlee 更像“可选替代”，不是最顺手的起步路线。

我的结论：

- 如果你后面更想做浏览器自动化、且愿意走 JS/TS 技术栈，可以把它视为 Scrapy 的 Node 版竞争者。

### 7.5 自动化平台思路很强，但不建议你先上：Huginn

仓库：[`huginn/huginn`](https://github.com/huginn/huginn)

优点：

- 能把“抓取、判断、通知、工作流”串成自动化流程。
- 很像自托管版 IFTTT/Zapier。
- 很适合把多来源信息拼接成规则流。

缺点：

- 学会 agent、事件流、规则编排本身就要花时间。
- 你现在的重点是先把“新品识别”跑通，而不是先搭一个复杂自动化平台。
- 公开 release 停留在 2022-08-18，虽然仓库依然有价值，但我不会把它作为你第一选择。

我的结论：

- 它更适合第二阶段做“通知编排”和复杂流程，不适合你先开荒。

### 7.6 视觉监控备选：Changd

仓库：[`paschmann/changd`](https://github.com/paschmann/changd)

优点：

- 支持截图差异、XPath、API 监控。
- 对“页面看起来变了没有”这类视觉监测很直观。

缺点：

- 项目相对小众。
- release 比较旧。
- 对“新品数据建模”这件事没有 changedetection.io 那么贴题。

我的结论：

- 如果某些站点很难抽结构化字段，但页面视觉变化很明确，它可以当补充工具。

### 7.7 轻量思路：rsspls

仓库：[`wezm/rsspls`](https://github.com/wezm/rsspls)

优点：

- 思路非常简单，把网页变成 feed。
- 对“新品列表页”这种更新型页面很友好。
- 如果某些站点结构稳定、内容少、无需 JS，这条路很轻。

缺点：

- 它更像“订阅器生成器”，不是完整监控平台。
- 对复杂登录、动态加载、年龄验证、热度分析帮助有限。

我的结论：

- 它适合某些特别简单的目标站，当成超轻量备选，不适合当整个平台主骨架。

### 7.8 平台特化方案：Shopify Monitor

仓库：[`subreme/shopify-monitor`](https://github.com/subreme/shopify-monitor)

它的价值不在于通用，而在于提醒我们一个现实：

- 如果某个目标站点本身就是 Shopify，很多新品数据可以直接从 `/products.json` 这类接口或平台特征里拿到。

优点：

- 对 Shopify 店铺特别直接。
- 很适合“新品/补货/上新提醒”。

缺点：

- 通用性很差。
- 只对 Shopify 站点有用。
- 仓库也比较老。

我的结论：

- 等你把具体网站 URL 给我后，我会先判断每个站点是不是 Shopify、WooCommerce、Shopware 或自研站；如果真是 Shopify，这类平台特化思路可以极大降低难度。

## 8. 我建议你的 MVP 这样做

### 路线 A：最适合小白，先验证可行性

技术思路：

- 用 `changedetection.io` 监控每个市场的新品列表页。
- 先只做“发现新品”。
- 只抽最关键字段：产品名、URL、价格、首见时间。

适合你，如果你想：

- 先快速看到结果
- 尽量少写代码
- 先验证哪些站点能抓

### 路线 B：最适合免费 GitHub 试水

技术思路：

- GitHub 仓库里放站点配置和 Python 脚本。
- GitHub Actions 每 15 到 60 分钟定时跑一次。
- 结果保存为 JSON / CSV / SQLite 导出文件。
- 用 GitHub Pages 或 Markdown 报告展示结果。

适合你，如果你想：

- 尽量免费
- 把所有东西都放在 GitHub 管理
- 接受“轻量、低频、偶尔延迟”的现实

### 路线 C：后期稳定升级版

技术思路：

- Scrapy 做主爬虫。
- 动态站点接入 scrapy-playwright。
- SQLite 或 Postgres 存储产品与历史快照。
- 通知接飞书或邮件。
- 部署到 VPS。

适合你，如果你想：

- 真正长期维护
- 同时监控更多市场和网站
- 后面做热度排行、价格趋势、品牌分析

## 9. 我给你的推荐顺序

如果只看你现在的阶段，我的推荐顺序是：

1. 先把“新品监控”定义清楚：只盯列表页，不先追求全站。
2. 先用低代码或轻代码方案把 1 到 3 个站点跑通。
3. 只有当你确认站点稳定可抓后，再做评论增长和热度模型。
4. 只有当站点数量上来后，再投入 Scrapy 级别的正式工程化。

## 10. 下一步应该收集什么信息

等你认可这个框架后，下一步最有价值的不是马上写很多代码，而是把输入信息整理好：

- 市场名称
- 网站名称
- 具体 URL
- 这是新品页、分类页、搜索页，还是产品详情页
- 这个网站有没有年龄验证弹窗
- 你最想收到哪种提醒：新品、价格变化、评论增长、补货

只要你给出第一批 URL，我下一步就可以帮你做两件很具体的事情：

- 逐站判断应该用哪种抓取方案。
- 在 `E:\github\new_product_detection` 里开始搭第一版监控项目骨架。

## 11. 本次结论

一句最直接的话：

你这个需求完全能做，而且第一阶段不需要先上复杂 AI。

真正关键的是：

- 先选对页面
- 先把“新品判断规则”做朴素
- 先跑通 1 到 3 个站点
- 再叠加热度监测

如果让我替你做技术路线选择，我当前会这样定：

- `第一版推荐思路`：以“新品列表页监测”为核心。
- `第一版推荐工具`：优先参考或采用 `changedetection.io`。
- `如果坚持 GitHub 免费部署`：做轻量 Python + GitHub Actions 方案，但接受它不是最终稳定平台。
- `第二阶段正式工程化`：转向 Scrapy + Playwright。

## 参考来源

- GitHub Actions billing: https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions
- GitHub Actions usage limits and billing: https://docs.github.com/actions/learn-github-actions/usage-limits-billing-and-administration
- GitHub workflow syntax `on.schedule`: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax
- GitHub events that trigger workflows: https://docs.github.com/articles/events-that-trigger-workflows
- GitHub troubleshooting scheduled workflows: https://docs.github.com/enterprise-cloud/latest/actions/monitoring-and-troubleshooting-workflows/troubleshooting-workflows/about-troubleshooting-workflows
- Schema.org AggregateRating: https://schema.org/AggregateRating
- changedetection.io: https://github.com/dgtlmoon/changedetection.io
- Scrapy: https://github.com/scrapy/scrapy
- scrapy-playwright: https://github.com/scrapy-plugins/scrapy-playwright
- Crawlee: https://github.com/apify/crawlee
- Huginn: https://github.com/huginn/huginn
- Changd: https://github.com/paschmann/changd
- rsspls: https://github.com/wezm/rsspls
- Shopify Monitor: https://github.com/subreme/shopify-monitor
