# FinBook

> 🧾 开源自托管财务系统 - 专为中小微企业设计

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-yellow.svg)](https://opensource.org/licenses/AGPL-3.0)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://telegram.org/)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://openclaw.ai/)

---

## 📖 简介

FinBook 是一个基于 OpenClaw 的开源财务系统，通过 Telegram Bot 提供完整的财务管理能力。

**核心特点**:
- ✅ **开源自托管** - 数据完全自主掌控
- ✅ **零订阅费** - 一次性部署，无持续费用
- ✅ **Telegram 入口** - 无需安装新 App，手机即用
- ✅ **合规设计** - 符合财政部 2025 新规范
- ✅ **AI 增强** - 自动识别发票、智能记账

---

## 🎯 适用场景

| 场景 | 说明 |
|------|------|
| **小微企业** | <50 人，需要简单可靠的财务系统 |
| **个体工作室** | 自由职业者、独立开发者记账 |
| **初创公司** | 早期团队，成本敏感 |
| **代理记账** | 多客户管理，批量处理 |

---

## 🚀 快速开始

### 前置要求

- OpenClaw Gateway 已安装
- Telegram Bot Token（从 [@BotFather](https://t.me/BotFather) 获取）
- Python 3.10+
- SQLite（默认）或 PostgreSQL

### 一键安装

```bash
# 1. 克隆仓库
git clone https://github.com/readapt/finbook.git
cd finbook

# 2. 安装依赖
pip install -e .

# 3. 配置 Telegram Bot
nano config/telegram.yaml
# 填入你的 Bot Token

# 4. 启动 OpenClaw
openclaw gateway start

# 5. 验证安装
openclaw skills list
```

---

## 📦 MVP 功能清单

### v0.1 - 凭证管理

- [ ] Telegram 发票上传
- [ ] OCR 识别（用户自选服务）
- [ ] 自动记账（Beancount + 中国化合规层）
- [ ] 凭证查询
- [ ] 文本存储 + SQLite 缓存

### v0.2 - 银行对账

- [ ] CSV 流水导入
- [ ] 手动匹配
- [ ] 余额调节表

### v0.3 - 资产管理

- [ ] 资产卡片
- [ ] 折旧计算（平均年限法/工作量法/一次性扣除）
- [ ] 资产处置
- [ ] 折旧凭证自动生成

### v0.4 - 财务报表

- [ ] 资产负债表
- [ ] 利润表
- [ ] 科目余额表

---

## 💰 许可策略

| 使用场景 | 许可证 | 费用 |
|----------|--------|------|
| **个人/企业自用** | AGPL v3 | 免费 |
| **SaaS 服务** | 商业许可 | 阶梯定价 |
| **代账公司** | 商业许可 | <5 客户免费，超出收费 |
| **OEM 集成** | 商业许可 | 协商定价 |

---

## 🛠️ 技术架构

| 组件 | 选型 |
|------|------|
| **记账引擎** | Beancount + 中国化合规层 |
| **数据源** | 文本文件（.beancount） |
| **数据库** | SQLite（默认）+ PostgreSQL（可选） |
| **开发语言** | Python |
| **入口** | Telegram（验证期）→ 企业微信/钉钉（正式） |

---

## 📋 开发路线图

| 版本 | 功能 | 周期 |
|------|------|------|
| **v0.1** | 凭证管理 | 2-3 周 |
| **v0.2** | 银行对账 | 2 周 |
| **v0.3** | 资产管理 | 2-3 周 |
| **v0.4** | 财务报表 | 2 周 |
| **v1.0** | 正式发布 | 第 12 周 |

---

## 🤝 贡献指南

欢迎贡献！请查看：

1. [贡献指南](docs/CONTRIBUTING.md)
2. [代码规范](docs/CODE_STYLE.md)
3. [提交 PR](https://github.com/readapt/finbook/pulls)

---

## 📄 许可证

- **核心技能**: AGPL v3
- **商业许可**: 单独授权

详见 [LICENSE](LICENSE) 文件。

---

## 📞 支持

| 渠道 | 链接 |
|------|------|
| **GitHub Issues** | https://github.com/readapt/finbook/issues |
| **Telegram 群组** | 待创建 |
| **文档** | https://readapt.github.io/finbook |

---

**Made with ❤️ for small businesses**
