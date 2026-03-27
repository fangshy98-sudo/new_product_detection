# 美国电子烟零售站新品监测实施计划

更新时间：2026-03-26

## 1. 目标

基于以下 5 个美国站，先做一个可运行的美国市场 MVP：

- `https://vapordna.com/`
- `https://megavapeusa.com/`
- `https://vapecityusa.com/`
- `https://vapesourcing.com/uswarehouse.html`
- `https://www.elementvape.com/`

MVP 只优先解决两件事：

1. 发现新品。
2. 为部分站点记录评论数或评分数，给后续“热度监测”留接口。

## 2. 站点逐个判断

以下判断基于 2026-03-26 的页面实际检查。

| 站点 | 推荐监控页 | 当前判断 | 建议抓取方式 | 优先级 |
| --- | --- | --- | --- | --- |
| VaporDNA | `https://vapordna.com/collections/whats-new` | Shopify 生态，列表页直接有产品名、价格、评论数 | `http` | 高 |
| Mega Vape USA | `https://megavapeusa.com/collections/new-disposables` | 站点可抓，但页面公开提示当前不运营，更像批发站 | `http` | 中 |
| Vape City USA | `https://vapecityusa.com/collections/new-arrivals` | 列表页适合发现新品，详情页可补评论数 | `http` | 高 |
| Vapesourcing | `https://vapesourcing.com/usa-new-disposable-kit.html` | 比 `uswarehouse.html` 更像新品入口，页面可直读评论数 | `http` | 高 |
| Element Vape | `https://www.elementvape.com/new-arrivals` | 原始 HTML 显示 `0 Display`，疑似前端渲染 | `browser` | 单独处理 |

## 3. 总体方案选择

### 方案 A：只用 changedetection.io

优点：

- 上手最快。
- 几乎不需要写代码。
- 很适合先验证 1 到 2 个站。

缺点：

- 不适合做结构化产品库。
- 后续评论数、价格趋势、跨站点分析会变难。
- 很难把逻辑沉淀成你自己的代码资产。

结论：

- 适合验证，不适合作为你这 5 个美国站的长期主方案。

### 方案 B：Python + requests + BeautifulSoup + JSON state

优点：

- 免费。
- 对小白仍然可控。
- 对 VaporDNA、Vape City、Vapesourcing、Mega 这 4 个站足够用。
- 和 GitHub Actions 非常兼容。

缺点：

- 遇到前端渲染站点会卡住。
- 站点增多后，需要做 adapter 管理。

结论：

- 这是第一版主推荐方案。

### 方案 C：Python + requests 为主，Playwright 只兜底 Element Vape

优点：

- 兼顾轻量和覆盖率。
- 不会让最难的 Element Vape 拖累整个 MVP。
- 代码结构合理，便于以后扩展更多动态站点。

缺点：

- 比纯 requests 多一层复杂度。
- GitHub Actions 跑 Playwright 会更耗时。

结论：

- 这是我最推荐的折中方案。

### 方案 D：直接上 Scrapy + Playwright

优点：

- 扩展性最好。
- 后期适合多市场、多站点、多规则。

缺点：

- 对你当前阶段偏重。
- 现在就上，会花较多时间在框架学习而不是出结果。

结论：

- 适合作为第二阶段升级方案，不建议现在直接开。

## 4. 推荐方案

采用 `方案 C`：

- `requests + BeautifulSoup` 先覆盖 4 个静态或半静态站点。
- `Playwright` 单独处理 Element Vape。
- 输出 `JSON state + Markdown report`。
- 调度优先支持本地运行，再补 GitHub Actions。

## 5. 建议的项目结构

下面这些文件是建议新增的第一版骨架。

| 路径 | 动作 | 作用 |
| --- | --- | --- |
| `E:\github\new_product_detection\requirements.txt` | 新增 | Python 依赖 |
| `E:\github\new_product_detection\config\sites\us_retailers.yaml` | 新增 | 5 个站的配置 |
| `E:\github\new_product_detection\src\new_product_detection\__init__.py` | 新增 | 包入口 |
| `E:\github\new_product_detection\src\new_product_detection\models.py` | 新增 | 数据结构 |
| `E:\github\new_product_detection\src\new_product_detection\config_loader.py` | 新增 | 读取 YAML 配置 |
| `E:\github\new_product_detection\src\new_product_detection\fetch.py` | 新增 | HTTP/浏览器抓取封装 |
| `E:\github\new_product_detection\src\new_product_detection\adapters\__init__.py` | 新增 | adapter 工厂 |
| `E:\github\new_product_detection\src\new_product_detection\adapters\shopify_like.py` | 新增 | VaporDNA、Mega、Vape City 解析 |
| `E:\github\new_product_detection\src\new_product_detection\adapters\vapesourcing.py` | 新增 | Vapesourcing 解析 |
| `E:\github\new_product_detection\src\new_product_detection\adapters\elementvape_browser.py` | 新增 | Element Vape 浏览器解析 |
| `E:\github\new_product_detection\src\new_product_detection\diff.py` | 新增 | 新品比较逻辑 |
| `E:\github\new_product_detection\src\new_product_detection\storage.py` | 新增 | 读写 state |
| `E:\github\new_product_detection\src\new_product_detection\report.py` | 新增 | 生成 Markdown 报告 |
| `E:\github\new_product_detection\scripts\run_us_monitor.py` | 新增 | 美国市场入口脚本 |
| `E:\github\new_product_detection\.github\workflows\us_monitor.yml` | 新增 | GitHub Actions 定时运行 |
| `E:\github\new_product_detection\data\state\us_products.json` | 新增 | 历史状态 |
| `E:\github\new_product_detection\reports\us_latest.md` | 新增 | 最新报告 |
| `E:\github\new_product_detection\codex.md` | 已新增 | 压缩上下文 |
| `E:\github\new_product_detection\research.md` | 已存在 | 详细调研 |

## 6. 关键配置示例

### 文件：`E:\github\new_product_detection\config\sites\us_retailers.yaml`

```yaml
sites:
  - site_id: vapordna_us
    market: us
    display_name: VaporDNA
    base_url: https://vapordna.com
    list_url: https://vapordna.com/collections/whats-new
    platform: shopify_like
    fetch_mode: http
    product_url_pattern: "/products/"
    supports_review_tracking: true
    enabled: true

  - site_id: megavapeusa_us
    market: us
    display_name: Mega Vape USA
    base_url: https://megavapeusa.com
    list_url: https://megavapeusa.com/collections/new-disposables
    platform: shopify_like
    fetch_mode: http
    product_url_pattern: "/products/"
    supports_review_tracking: false
    enabled: true

  - site_id: vapecityusa_us
    market: us
    display_name: Vape City USA
    base_url: https://vapecityusa.com
    list_url: https://vapecityusa.com/collections/new-arrivals
    platform: shopify_like
    fetch_mode: http
    product_url_pattern: "/products/"
    supports_review_tracking: true
    enabled: true

  - site_id: vapesourcing_us
    market: us
    display_name: Vapesourcing USA
    base_url: https://vapesourcing.com
    list_url: https://vapesourcing.com/usa-new-disposable-kit.html
    platform: vapesourcing_html
    fetch_mode: http
    product_url_pattern: ".html"
    supports_review_tracking: true
    enabled: true

  - site_id: elementvape_us
    market: us
    display_name: Element Vape
    base_url: https://www.elementvape.com
    list_url: https://www.elementvape.com/new-arrivals
    platform: elementvape_browser
    fetch_mode: browser
    product_url_pattern: "/"
    supports_review_tracking: false
    enabled: false
```

为什么这样配：

- `platform` 决定使用哪种 adapter。
- `fetch_mode` 决定是 `requests` 还是 `Playwright`。
- `elementvape_us` 先保留但默认 `enabled: false`，避免它阻塞 MVP。

## 7. 数据结构示例

### 文件：`E:\github\new_product_detection\src\new_product_detection\models.py`

```python
from dataclasses import dataclass, asdict
from decimal import Decimal
from typing import Optional


@dataclass(slots=True)
class SiteConfig:
    site_id: str
    market: str
    display_name: str
    base_url: str
    list_url: str
    platform: str
    fetch_mode: str
    product_url_pattern: str
    supports_review_tracking: bool
    enabled: bool = True


@dataclass(slots=True)
class ProductRecord:
    site_id: str
    market: str
    product_key: str
    name: str
    product_url: str
    price_text: Optional[str] = None
    price_value: Optional[Decimal] = None
    review_count: Optional[int] = None
    in_stock: Optional[bool] = None
    first_seen_at: Optional[str] = None
    last_seen_at: Optional[str] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        if self.price_value is not None:
            data["price_value"] = str(self.price_value)
        return data
```

为什么第一版就建 `ProductRecord`：

- 以后你要加评论数趋势，不用重构数据模型。
- `product_key` 可以统一做去重键。

## 8. Shopify 类站点的解析代码示例

### 文件：`E:\github\new_product_detection\src\new_product_detection\adapters\shopify_like.py`

```python
from __future__ import annotations

import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from new_product_detection.models import ProductRecord, SiteConfig

PRICE_RE = re.compile(r"\$\s*([0-9]+(?:\.[0-9]{2})?)")
REVIEW_RE = re.compile(r"(?:(\d+)\s+reviews?|No\s+reviews)", re.I)


def parse_shopify_like_list(html: str, site: SiteConfig) -> list[ProductRecord]:
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    products: list[ProductRecord] = []

    for anchor in soup.select("a[href*='/products/']"):
        href = anchor.get("href", "").strip()
        if not href:
            continue

        product_url = urljoin(site.base_url, href)
        product_key = product_url.split("?")[0].rstrip("/")
        if product_key in seen:
            continue

        card_text = anchor.parent.get_text(" ", strip=True)
        name = anchor.get_text(" ", strip=True) or product_key.rsplit("/", 1)[-1]
        price_match = PRICE_RE.search(card_text)
        review_match = REVIEW_RE.search(card_text)

        review_count = None
        if review_match:
            raw = review_match.group(0).lower()
            review_count = 0 if "no reviews" in raw else int(review_match.group(1))

        products.append(
            ProductRecord(
                site_id=site.site_id,
                market=site.market,
                product_key=product_key,
                name=name,
                product_url=product_url,
                price_text=price_match.group(0) if price_match else None,
                review_count=review_count,
                in_stock="sold out" not in card_text.lower(),
            )
        )
        seen.add(product_key)

    return products
```

为什么我先推荐这个解析策略：

- 对 Shopify 类站点，`/products/` 链接本身就是强特征。
- 第一版先用“链接 + 周边文本”提取，能更快跑起来。
- 等站点稳定后，再替换成更精确的 CSS 选择器或 JSON 接口。

## 9. Vapesourcing 解析代码示例

### 文件：`E:\github\new_product_detection\src\new_product_detection\adapters\vapesourcing.py`

```python
from __future__ import annotations

import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from new_product_detection.models import ProductRecord, SiteConfig

PRICE_RE = re.compile(r"\$\s*([0-9]+(?:\.[0-9]{2})?)")
REVIEW_RE = re.compile(r"(\d+)\s+Reviews?", re.I)


def parse_vapesourcing_list(html: str, site: SiteConfig) -> list[ProductRecord]:
    soup = BeautifulSoup(html, "html.parser")
    products: list[ProductRecord] = []
    seen: set[str] = set()

    for anchor in soup.select("a[href$='.html']"):
        href = anchor.get("href", "").strip()
        text = anchor.get_text(" ", strip=True)
        if not text or len(text) < 8:
            continue
        if "blog" in href or "news" in href:
            continue

        product_url = urljoin(site.base_url, href)
        product_key = product_url.split("?")[0].rstrip("/")
        if product_key in seen:
            continue

        card_text = anchor.parent.get_text(" ", strip=True)
        if "$" not in card_text:
            continue

        price_match = PRICE_RE.search(card_text)
        review_match = REVIEW_RE.search(card_text)

        products.append(
            ProductRecord(
                site_id=site.site_id,
                market=site.market,
                product_key=product_key,
                name=text,
                product_url=product_url,
                price_text=price_match.group(0) if price_match else None,
                review_count=int(review_match.group(1)) if review_match else None,
                in_stock="out of stock" not in card_text.lower(),
            )
        )
        seen.add(product_key)

    return products
```

为什么不直接复用 Shopify 解析器：

- Vapesourcing 的目录页是 `.html` 风格，不应强依赖 `/products/`。
- 单独 adapter 更稳，也方便以后针对这个站做微调。

## 10. Element Vape 的浏览器兜底示例

### 文件：`E:\github\new_product_detection\src\new_product_detection\adapters\elementvape_browser.py`

```python
from __future__ import annotations

from playwright.sync_api import sync_playwright
from new_product_detection.models import ProductRecord, SiteConfig


def parse_elementvape_with_browser(site: SiteConfig) -> list[ProductRecord]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(site.list_url, wait_until="networkidle", timeout=60000)

        # 第一轮只做最保守等待，后面如果需要再加点击逻辑
        page.wait_for_timeout(4000)

        links = page.locator("a").evaluate_all(
            """
            nodes => nodes
              .map(n => ({ href: n.href, text: (n.innerText || '').trim() }))
              .filter(x => x.href && x.text && x.text.length > 6)
            """
        )

        browser.close()

    products: list[ProductRecord] = []
    seen: set[str] = set()
    for item in links:
        href = item["href"].split("?")[0].rstrip("/")
        if href in seen:
            continue
        if "category" in href or "blog" in href:
            continue

        products.append(
            ProductRecord(
                site_id=site.site_id,
                market=site.market,
                product_key=href,
                name=item["text"],
                product_url=href,
            )
        )
        seen.add(href)

    return products
```

为什么只把 Element 单独放浏览器层：

- 2026-03-26 检查时，`/new-arrivals` 原始文本显示 `0 Display`。
- 这说明直接抓 HTML 风险很高。
- 把浏览器能力只给 Element，可以控制复杂度和 GitHub minutes 消耗。

## 11. 差异检测代码示例

### 文件：`E:\github\new_product_detection\src\new_product_detection\diff.py`

```python
from new_product_detection.models import ProductRecord


def detect_new_products(previous: list[ProductRecord], current: list[ProductRecord]) -> list[ProductRecord]:
    previous_keys = {item.product_key for item in previous}
    return [item for item in current if item.product_key not in previous_keys]


def detect_review_growth(previous: list[ProductRecord], current: list[ProductRecord]) -> list[tuple[ProductRecord, int]]:
    previous_map = {item.product_key: item for item in previous}
    growth: list[tuple[ProductRecord, int]] = []

    for item in current:
        old = previous_map.get(item.product_key)
        if not old:
            continue
        if item.review_count is None or old.review_count is None:
            continue
        if item.review_count > old.review_count:
            growth.append((item, item.review_count - old.review_count))

    return growth
```

## 12. 主入口脚本示例

### 文件：`E:\github\new_product_detection\scripts\run_us_monitor.py`

```python
from datetime import datetime, timezone

from new_product_detection.config_loader import load_sites
from new_product_detection.diff import detect_new_products
from new_product_detection.fetch import fetch_html
from new_product_detection.report import write_market_report
from new_product_detection.storage import load_state, save_state
from new_product_detection.adapters.shopify_like import parse_shopify_like_list
from new_product_detection.adapters.vapesourcing import parse_vapesourcing_list
from new_product_detection.adapters.elementvape_browser import parse_elementvape_with_browser


def run() -> None:
    sites = [site for site in load_sites("config/sites/us_retailers.yaml") if site.enabled]
    previous = load_state("data/state/us_products.json")
    current = []

    for site in sites:
        if site.platform == "shopify_like":
            html = fetch_html(site.list_url)
            records = parse_shopify_like_list(html, site)
        elif site.platform == "vapesourcing_html":
            html = fetch_html(site.list_url)
            records = parse_vapesourcing_list(html, site)
        elif site.platform == "elementvape_browser":
            records = parse_elementvape_with_browser(site)
        else:
            raise ValueError(f"Unsupported platform: {site.platform}")

        now = datetime.now(timezone.utc).isoformat()
        for record in records:
            record.last_seen_at = now
        current.extend(records)

    new_products = detect_new_products(previous, current)
    save_state("data/state/us_products.json", current)
    write_market_report("reports/us_latest.md", current, new_products)


if __name__ == "__main__":
    run()
```

## 13. GitHub Actions 示例

### 文件：`E:\github\new_product_detection\.github\workflows\us_monitor.yml`

```yaml
name: us-monitor

on:
  workflow_dispatch:
  schedule:
    - cron: "0 */6 * * *"

jobs:
  run-monitor:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          playwright install chromium

      - name: Run US monitor
        run: |
          python -m scripts.run_us_monitor

      - name: Commit updated reports and state
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          git add data/state/us_products.json reports/us_latest.md
          git diff --cached --quiet || git commit -m "chore: update us monitor outputs"
          git push
```

为什么先设成每 6 小时：

- 对免费方案更友好。
- 足够用于新品发现。
- 以后如果实际效果好，再把静态站点单独提到 1 小时或 2 小时。

## 14. 依赖建议

### 文件：`E:\github\new_product_detection\requirements.txt`

```txt
beautifulsoup4==4.12.3
lxml==5.3.0
playwright==1.53.0
pydantic==2.11.0
pyyaml==6.0.2
requests==2.32.3
```

如果你想更轻量：

- 第一轮可以先不装 `pydantic`。
- 如果暂时不做 Element Vape，也可以先不装 `playwright`。

## 15. 实施顺序

### 第一阶段：今天就能开始

1. 创建 `requirements.txt`。
2. 创建 `config/sites/us_retailers.yaml`。
3. 创建 `models.py`、`fetch.py`、`diff.py`、`storage.py`。
4. 先完成 VaporDNA、Vape City、Vapesourcing 3 个 adapter。
5. 输出第一份 `reports/us_latest.md`。

### 第二阶段：补上可选站点

1. 加入 Mega Vape USA。
2. 把评论数增长加入报告。
3. 把结果写入 `data/history/`，保留每日快照。

### 第三阶段：处理最难站点

1. 单独为 Element Vape 加浏览器 adapter。
2. 如果浏览器方案太重，再尝试接口逆向。
3. 必要时拆成第二个 workflow 单独跑。

## 16. 具体权衡

### 为什么不先把 Element Vape 做进去

- 它是当前最不稳定、最可能拖慢项目进度的站点。
- 如果一开始就要求 5 个站全部打通，MVP 会明显变慢。
- 先把 3 到 4 个易站跑通，能更快证明系统有价值。

### 为什么不用数据库起步

- 第一版的数据量很小。
- JSON state 更适合快速调试。
- 用户是小白，少一个数据库就少很多运维成本。

### 为什么暂时不直接用 Scrapy

- 当前站点数不多。
- 先把规则和配置跑顺，比先引入重框架更重要。
- 真正需要 Scrapy 时，说明系统已经经过验证。

### 为什么推荐把 Vapesourcing 入口从 `uswarehouse.html` 换到 `usa-new-disposable-kit.html`

- `uswarehouse.html` 更像美国仓总入口。
- `usa-new-disposable-kit.html` 更直接对应新品。
- 这样做能减少无关商品和页面噪音。

## 17. 我建议你下一步真的怎么做

如果下一步要开始动手，我建议按这个顺序实施：

1. 先只启用 `vapordna_us`、`vapecityusa_us`、`vapesourcing_us`。
2. 把 `elementvape_us` 保留在配置里，但先 `enabled: false`。
3. 先把 GitHub Actions 暂时放后面，本地手动跑通一次。
4. 本地跑通后，再补 `.github/workflows/us_monitor.yml`。

这条路线最稳，也最符合你现在“免费 + 小白 + 先把新品监测跑起来”的目标。

## 18. 新增评估：自动记录评论或评分 vs 手动点击提取特定产品页评论

### 先说结论

如果只比较“哪个更容易先做出来”，答案是：

- `更容易实现`：手动点击或手动提供多个站点的特定产品页面，然后提取评论数或评分数。
- `更有长期价值但更复杂`：让系统自动检测新品后，再自动记录这些新品的评论数或评分数。

### 为什么手动提取更容易

手动提取路线只需要解决“详情页解析”这一层问题，不需要先解决下面这些额外难题：

- 新品发现
- 列表页抓取
- 新老产品比对
- 历史状态维护
- 自动挑选哪些产品值得继续追踪

换句话说：

- 自动记录评论或评分 = `列表页发现新品` + `详情页提取评论` + `历史追踪`
- 手动提取特定产品页评论 = `详情页提取评论`

所以手动路线明显更短，也更适合先验证“多个站点的评论字段能不能稳定抓到”。

### 两种功能的实现难度对比

| 功能 | 输入 | 需要解决的问题 | 难度 | 适合当前阶段 |
| --- | --- | --- | --- | --- |
| 自动记录评论或评分 | 站点列表页 | 新品发现、去重、保存状态、追踪详情页、处理失败重试 | 中到高 | 第二阶段 |
| 手动提取多个站点特定产品页评论 | 你给产品 URL，或你手动点选目标产品 | 只做详情页解析和结果输出 | 低到中 | 第一阶段更容易落地 |

### 对当前 5 个美国站的影响

#### 手动提取路线

更适合先覆盖：

- VaporDNA
- Vape City USA
- Vapesourcing

原因：

- 这些站的产品页或列表页当前就能看到评论相关文本。
- 你只要提供产品页 URL，就能逐页提取，不依赖新品发现流程先完成。

需要单独观察：

- Mega Vape USA
原因：

- 当前站点公开提示不运营。
- 业务价值低于前 3 个站。

最难：

- Element Vape

原因：

- 列表页当前偏动态。
- 详情页是否稳定暴露评论字段，还需要单独验证。

#### 自动记录路线

这条路线只有在以下前提都稳定后才值得做：

1. 列表页新品发现已经稳定。
2. 新品对应的详情页解析已经稳定。
3. 你已经确定哪些站点的评论数确实有业务价值。

### 我对实施顺序的建议

建议把原来的“大一统自动追踪评论数”拆成两步：

1. `先做手动产品页评论提取工具`
2. `再把这个工具挂到新品检测结果后面，变成自动追踪`

这样做的好处：

- 你能先验证评论字段是否存在。
- 你能先知道不同站点的评论结构差异。
- 以后自动化时，详情页解析器可以直接复用，不会白做。

### 建议在项目里新增的文件

如果先走“手动提取特定产品页评论”路线，我建议额外新增这些文件：

| 路径 | 动作 | 作用 |
| --- | --- | --- |
| `E:\github\new_product_detection\config\manual_products.yaml` | 新增 | 手动维护要提取评论的产品页 URL 列表 |
| `E:\github\new_product_detection\src\new_product_detection\review_extractors.py` | 新增 | 详情页评论数和评分数解析逻辑 |
| `E:\github\new_product_detection\scripts\run_manual_reviews.py` | 新增 | 手动评论提取入口 |
| `E:\github\new_product_detection\reports\manual_reviews_latest.md` | 新增 | 手动提取结果报告 |

### 配置示例

#### 文件：`E:\github\new_product_detection\config\manual_products.yaml`

```yaml
products:
  - site_id: vapordna_us
    product_url: https://vapordna.com/products/example-product

  - site_id: vapecityusa_us
    product_url: https://vapecityusa.com/products/example-product

  - site_id: vapesourcing_us
    product_url: https://vapesourcing.com/example-product.html
```

### 代码示例

#### 文件：`E:\github\new_product_detection\src\new_product_detection\review_extractors.py`

```python
import re
from bs4 import BeautifulSoup

REVIEW_COUNT_RE = re.compile(r"(\d+)\s+reviews?", re.I)
RATING_VALUE_RE = re.compile(r"([0-5](?:\.\d)?)\s+out\s+of\s+5", re.I)


def extract_review_metrics(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    review_match = REVIEW_COUNT_RE.search(text)
    rating_match = RATING_VALUE_RE.search(text)

    return {
        "review_count": int(review_match.group(1)) if review_match else None,
        "rating_value": float(rating_match.group(1)) if rating_match else None,
    }
```

#### 文件：`E:\github\new_product_detection\scripts\run_manual_reviews.py`

```python
from new_product_detection.fetch import fetch_html
from new_product_detection.review_extractors import extract_review_metrics


def run(urls: list[str]) -> None:
    for url in urls:
        html = fetch_html(url)
        metrics = extract_review_metrics(html)
        print(url, metrics)
```

### 对原计划的影响

如果你选择先做手动提取，那么原 `plan.md` 里的阶段顺序我建议这样调整：

- `阶段 1`：先完成 VaporDNA、Vape City、Vapesourcing 的新品检测。
- `阶段 1.5`：新增手动产品页评论提取工具。
- `阶段 2`：确认评论字段可稳定提取后，再把评论提取挂到自动新品追踪后面。
- `阶段 3`：最后再处理 Element Vape 这种更难的动态站点。

### 最终建议

如果你现在只能先选一个功能做，我建议先做：

- `手动提取多个站点特定产品页面评论`

原因不是它更高级，而是它更容易、验证更快、还能直接为后面的自动化打基础。


## 19. 路线评估：新品监测 + 手动提取产品页评论数、评分、评论内容

### 19.1 先说结论

如果你的目标是：

- 先稳定发现新品
- 然后由你手动指定某些新品的产品页
- 系统再去提取评论数、评分、评论内容

那么这条路线是可行的，而且在当前阶段，依然明显比“新品监测 + 自动检测产品热度”更容易实现。

但这里要拆成两层看：

1. `手动提取评论数、评分`：难度较低，适合第一批就做。
2. `手动提取评论内容`：能做，但通常比评论数、评分更难，因为评论文本经常有分页、懒加载、第三方评论组件、查看更多按钮。

所以对这条路线更准确的判断是：

- `新品监测 + 手动提取评论数/评分`：容易实现。
- `新品监测 + 手动提取评论数/评分/评论内容`：整体仍比自动热度检测容易，但难度会高于只提评论数和评分。

### 19.2 和“自动检测产品热度”的难度对比

| 路线 | 需要解决的问题 | 难度 | 当前建议 |
| --- | --- | --- | --- |
| 新品监测 + 手动提取评论数/评分 | 列表页发现新品 + 详情页解析数值字段 | 中等 | 推荐先做 |
| 新品监测 + 手动提取评论数/评分/评论内容 | 列表页发现新品 + 详情页提取评论文本 | 中等偏上 | 可做，推荐拆阶段 |
| 新品监测 + 自动检测产品热度 | 列表页发现新品 + 自动决定追踪对象 + 周期性记录 + 热度计算 + 历史存储 | 高 | 后做 |

为什么“手动提取评论内容”仍然比“自动热度检测”容易：

- 你手动决定抓哪些产品，不需要系统自动筛选追踪对象。
- 你不需要先定义热度模型，比如 7 天评论增长、评分变化速度、加权得分等。
- 你不需要长期定时存储和计算每个产品的趋势曲线。

### 19.3 在当前技术方案下是否合适

当前选定方案是：

- `Python + requests` 为主
- `Playwright` 只兜底 Element Vape

我认为这套方案非常适合这条路线，原因如下：

#### 对新品监测部分

- VaporDNA、Vape City USA、Vapesourcing 当前都适合优先走 `requests + BeautifulSoup`。
- Mega Vape USA 技术上也可走 `requests`，只是业务优先级低。
- Element Vape 继续保留为 `Playwright` 特例，不影响主体开发。

#### 对手动评论提取部分

- 大多数站点的产品详情页可以先尝试直接用 `requests` 抓 HTML。
- 如果页面里已有评论数字段、评分字段或 JSON-LD，这一步会很轻。
- 只有当评论内容需要点击“Load More”或需要前端渲染时，再让 Playwright 接管。

也就是说，这条路线和当前技术选型是匹配的。

### 19.4 真正的难点在哪里

#### 最容易的部分

- 新品列表页监测
- 提取评论数
- 提取评分值

因为这些字段经常直接出现在：

- 页面文本
- JSON-LD
- `AggregateRating`
- 评论组件的初始化脚本里

#### 中等难度的部分

- 提取第一页的评论内容
- 提取评论作者、评论日期、评论标题、评论正文

因为这些内容可能：

- 在 HTML 里直接存在
- 也可能在页面初始化时一次性加载出来
- 也可能来自第三方评论组件

#### 最难的部分

- 提取全部评论内容
- 自动翻页抓所有评论
- 处理“查看更多评论”按钮
- 处理客户端渲染评论模块

这部分一旦进入交互型评论组件，就可能需要：

- 浏览器点击
- 等待异步接口
- 分页循环
- 接口逆向

所以我建议你把“评论内容提取”拆成两个层级：

1. `第一版`：提取评论数、评分，以及页面上首屏直接可见的评论内容。
2. `第二版`：再尝试翻页抓取更多评论内容。

### 19.5 各站点适配判断

| 站点 | 新品监测 | 手动提取评论数/评分 | 手动提取评论内容 | 建议 |
| --- | --- | --- | --- | --- |
| VaporDNA | 容易 | 容易到中等 | 中等 | 第一批纳入 |
| Vape City USA | 容易 | 容易到中等 | 中等 | 第一批纳入 |
| Vapesourcing | 容易 | 中等 | 中等偏上 | 第一批纳入 |
| Mega Vape USA | 可做 | 待验证 | 待验证 | 暂缓 |
| Element Vape | 难 | 中等偏上到高 | 高 | 单独排期 |

解释：

- `VaporDNA`：列表页当前能看到评论相关文本，详情页很值得优先验证。
- `Vape City USA`：详情页已有 `Customer Reviews` 等文本，适合尽快接入。
- `Vapesourcing`：已有评论相关文本，适合作为第三个评论提取站。
- `Mega Vape USA`：技术上不一定难，但当前站点状态让它不适合排在前面。
- `Element Vape`：保留 `Playwright` 兜底，不要让它阻塞前 3 个站。

### 19.6 这条路线的推荐执行形态

我建议把这条路线拆成一条明确的工作流：

1. 系统先跑新品监测。
2. 你从新品报告里手动挑选想看的产品。
3. 你把这些产品页 URL 放进 `config/manual_products.yaml`。
4. 系统运行手动评论提取脚本。
5. 输出该批产品的评论数、评分、评论内容摘要。

这样做的好处是：

- 你仍然保留“新品监测”的自动化价值。
- 你把最复杂的“自动决定追踪哪些产品”留给人工判断。
- 代码结构很自然，后面也容易升级成自动追踪。

### 19.7 需要新增或调整的文件

如果确认走这条路线，我建议在前面计划基础上新增或调整以下文件：

| 路径 | 动作 | 作用 |
| --- | --- | --- |
| `E:\github\new_product_detection\config\manual_products.yaml` | 新增 | 手动维护要提取评论的产品页 URL |
| `E:\github\new_product_detection\src\new_product_detection\review_extractors.py` | 新增 | 提取评论数、评分、评论内容 |
| `E:\github\new_product_detection\src\new_product_detection\manual_review_pipeline.py` | 新增 | 统一调度 requests 与 Playwright 提取逻辑 |
| `E:\github\new_product_detection\scripts\run_manual_reviews.py` | 新增 | 手动评论提取入口 |
| `E:\github\new_product_detection\reports\manual_reviews_latest.md` | 新增 | 提取结果报告 |
| `E:\github\new_product_detection\data\state\manual_reviews.json` | 新增 | 手动提取结果缓存，可选 |

### 19.8 配置示例

#### 文件：`E:\github\new_product_detection\config\manual_products.yaml`

```yaml
products:
  - site_id: vapordna_us
    product_url: https://vapordna.com/products/example-product
    extract_mode: http

  - site_id: vapecityusa_us
    product_url: https://vapecityusa.com/products/example-product
    extract_mode: http

  - site_id: vapesourcing_us
    product_url: https://vapesourcing.com/example-product.html
    extract_mode: http

  - site_id: elementvape_us
    product_url: https://www.elementvape.com/example-product
    extract_mode: browser
```

### 19.9 评论提取代码示例

#### 文件：`E:\github\new_product_detection\src\new_product_detection\review_extractors.py`

```python
from __future__ import annotations

import re
from bs4 import BeautifulSoup

REVIEW_COUNT_RE = re.compile(r"(\d+)\s+reviews?", re.I)
RATING_VALUE_RE = re.compile(r"([0-5](?:\.\d+)?)\s+out\s+of\s+5", re.I)


def extract_review_metrics_and_content(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    review_match = REVIEW_COUNT_RE.search(text)
    rating_match = RATING_VALUE_RE.search(text)

    comments: list[str] = []
    for node in soup.select(".review, .reviews-content, .jdgm-rev, .spr-review"):
        snippet = node.get_text(" ", strip=True)
        if snippet and len(snippet) >= 20:
            comments.append(snippet[:500])

    return {
        "review_count": int(review_match.group(1)) if review_match else None,
        "rating_value": float(rating_match.group(1)) if rating_match else None,
        "comments": comments[:20],
    }
```

这段代码的定位不是“覆盖所有站”，而是提供一个第一版通用入口：

- 优先抓评论数
- 再抓评分
- 最后尝试抓首屏可见评论内容

#### 文件：`E:\github\new_product_detection\src\new_product_detection\manual_review_pipeline.py`

```python
from new_product_detection.fetch import fetch_html
from new_product_detection.review_extractors import extract_review_metrics_and_content
from new_product_detection.adapters.elementvape_browser import parse_elementvape_with_browser


def extract_manual_product_reviews(product_url: str, extract_mode: str) -> dict:
    if extract_mode == "http":
        html = fetch_html(product_url)
        return extract_review_metrics_and_content(html)

    if extract_mode == "browser":
        # 第二版可以替换成真正的浏览器详情页评论提取函数
        raise NotImplementedError("Browser-based review extraction is not implemented yet")

    raise ValueError(f"Unsupported extract mode: {extract_mode}")
```

### 19.10 方案取舍

#### 为什么这条路线适合当前阶段

- 它保留了新品监测这个主目标。
- 它把评论分析简化成“人工挑选 + 程序提取”。
- 它比自动热度检测更容易验证和迭代。

#### 为什么仍然不建议一开始就追求“完整评论内容全量抓取” 

- 评论内容比评论数、评分更不稳定。
- 很多站点的评论区是第三方插件，不同站点 DOM 结构差异大。
- 有些评论需要翻页或点击后才出现，首版就全量抓取容易把项目变重。

#### 为什么 `requests` 仍应作为主线

- 绝大多数工作仍然是静态 HTML 抓取。
- requests 更快、更简单、更省资源。
- 后续上 GitHub Actions 或本地定时都更轻。

#### 为什么只让 Playwright 兜底 Element Vape

- 这是当前 5 个站里最明确需要浏览器兜底的站。
- 如果把浏览器能力扩散到所有站，会增加实现复杂度和运行成本。
- 让浏览器能力只服务最难站点，符合 MVP 原则。

### 19.11 最终判断

如果你现在要确定主路线，我建议定成：

- `新品监测 + 手动提取产品页评论数、评分、首屏评论内容`
- 技术方案采用：`Python + requests 为主，Playwright 只兜底 Element Vape`

这是一个比“新品监测 + 自动热度检测”更容易落地、也更适合当前阶段的方案。

如果后面这条路线跑顺了，再升级成：

- 自动把新品加入待评论提取列表
- 定时抓同一产品的评论数变化
- 最后再形成真正的热度模型
