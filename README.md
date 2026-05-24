# 🎭 Opera Daily — 全球歌剧院演出日报

每日自动收集全球各大歌剧院的演出排期与艺术家信息，生成结构化日报。

## 覆盖剧院 (10家)

| 剧院 | 城市 | 国家 |
|------|------|------|
| 🏛️ 纽约大都会歌剧院 | 纽约 | 🇺🇸 美国 |
| 🏛️ 米兰斯卡拉歌剧院 | 米兰 | 🇮🇹 意大利 |
| 🏛️ 维也纳国家歌剧院 | 维也纳 | 🇦🇹 奥地利 |
| 🏛️ 巴黎歌剧院 | 巴黎 | 🇫🇷 法国 |
| 🏛️ 英国皇家歌剧院 | 伦敦 | 🇬🇧 英国 |
| 🏛️ 拜罗伊特节日剧院 | 拜罗伊特 | 🇩🇪 德国 |
| 🏛️ 悉尼歌剧院 | 悉尼 | 🇦🇺 澳大利亚 |
| 🏛️ 中国国家大剧院 | 北京 | 🇨🇳 中国 |
| 🏛️ 萨尔茨堡音乐节 | 萨尔茨堡 | 🇦🇹 奥地利 |
| 🏛️ 马德里皇家剧院 | 马德里 | 🇪🇸 西班牙 |

## 功能特性

- ✅ **10 家顶级歌剧院** — 覆盖欧洲、美洲、亚洲、大洋洲
- ✅ **每日自动更新** — 通过 GitHub Actions 定时运行
- ✅ **结构化数据** — JSON 原始数据 + Markdown 日报
- ✅ **免费部署** — 完全基于 GitHub 免费服务
- ✅ **GitHub Pages 展示** — 可在线阅读日报
- ✅ **手动触发** — 支持 workflow_dispatch 手动运行
- ✅ **艺术家追踪** — 记录指挥、导演、主要演员信息

## 技术栈

| 组件 | 技术 |
|------|------|
| 数据采集 | Python + requests + BeautifulSoup |
| 数据存储 | JSON 文件 |
| 日报生成 | Jinja2 + Markdown |
| 自动部署 | GitHub Actions |
| 前端展示 | GitHub Pages |

## 快速开始

### 在本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/lishw/opera-daily.git
cd opera-daily

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行爬虫
python orchestrator.py

# 4. 查看生成的数据
cat data/raw/_summary.json
cat docs/daily/latest.md
```

### 部署到 GitHub

1. Fork 此仓库
2. 进入仓库 Settings → Pages，将 Source 设为 **GitHub Actions**
3. 前往 Actions 标签页，手动运行 "🎭 Opera Daily Report" 工作流
4. 之后每天 UTC 00:00 自动更新

## 日报内容

每日生成的日报包含：

1. **📅 近期上演剧目** — 未来7天内的演出列表
2. **🏛️ 各剧院演出排期** — 按剧院分组的完整排期
3. **⭐ 艺术家动态** — 活跃的指挥、导演、歌唱家信息
4. **📊 统计概览** — 覆盖数量、总演出数等

## 项目结构

```
opera-daily/
├── .github/workflows/
│   └── daily-report.yml    # GitHub Actions 工作流
├── crawlers/
│   ├── base.py              # 爬虫基类
│   ├── operadeparis.py      # 巴黎歌剧院
│   ├── wienerstaatsoper.py  # 维也纳国家歌剧院
│   ├── lascala.py           # 斯卡拉歌剧院
│   ├── metopera.py          # 大都会歌剧院
│   ├── royaloperahouse.py   # 英国皇家歌剧院
│   ├── bayreuth.py          # 拜罗伊特节日剧院
│   ├── sydneyoperahouse.py  # 悉尼歌剧院
│   ├── nationalgrandtheater.py # 中国国家大剧院
│   ├── salzburg.py          # 萨尔茨堡音乐节
│   └── teatroreal.py        # 马德里皇家剧院
├── data/
│   └── raw/                 # 爬取的原数据 (JSON)
├── docs/
│   ├── index.html           # GitHub Pages 首页
│   └── daily/               # 每日日报 (Markdown)
├── models.py                # 数据模型
├── orchestrator.py          # 协调器
├── report_generator.py      # 日报生成器
├── run_local.py             # 本地运行脚本
├── requirements.txt         # Python 依赖
└── README.md                # 本文件
```

## 自定义

### 添加新的歌剧院

1. 在 `models.py` 的 `OPERA_HOUSES_CONFIG` 中添加配置
2. 在 `crawlers/` 下创建新爬虫文件，继承 `BaseCrawler`
3. 在 `orchestrator.py` 的 `CRAWLER_MAP` 中注册

### 修改日报时间

编辑 `.github/workflows/daily-report.yml` 中的 cron 表达式：
```yaml
- cron: '0 0 * * *'  # UTC 00:00 = 北京时间 08:00
```

### 推送通知

可以扩展日报发送到：
- 📧 邮件 (通过 SMTP)
- 💬 微信 (通过 Server酱 / 企业微信机器人)
- 📱 Telegram Bot
- 🔗 Discord Webhook

## 免责声明

- 数据来源于各歌剧院官网，仅供个人参考
- 请以各剧院官方渠道为准进行购票
- 本工具遵守 robots.txt，适度爬取

## 许可证

MIT License

---

<p align="center">Built with ❤️ for opera lovers worldwide</p>