# FinBook 技术架构文档

**版本**: v0.1.0  
**创建时间**: 2026-03-10  
**状态**: 草稿

---

## 一、架构概述

### 1.1 设计原则

| 原则 | 说明 |
|------|------|
| **文本优先** | .beancount 文件为唯一权威数据源 |
| **最终一致性** | 数据库异步更新，定期校验 |
| **模块化** | 核心引擎、业务系统、入口层分离 |
| **可扩展** | OpenClaw 技能插件化 |
| **合规第一** | 符合财政部 2025 规范 |

### 1.2 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **入口层** | OpenClaw | Telegram/企业微信/钉钉 |
| **业务层** | Python 3.10+ | 自研业务系统 |
| **引擎层** | Beancount v3 | 双式记账核心 |
| **存储层** | SQLite/PostgreSQL | 灵活部署 |

---

## 二、核心模块

### 2.1 模块结构

```
src/finbook/
├── core/                    # 核心引擎
│   ├── beancount_engine.py  # Beancount 封装
│   ├── compliance.py        # 中国化合规层
│   └── __init__.py
├── skills/                  # OpenClaw 技能
│   ├── invoice_upload/      # 发票上传
│   ├── bank_reconciliation/ # 银行对账
│   └── asset_management/    # 资产管理
├── utils/                   # 工具函数
│   ├── ocr.py              # OCR 服务集成
│   ├── logger.py           # 日志工具
│   └── __init__.py
└── __init__.py
```

### 2.2 数据流

```
用户消息 (Telegram/企业微信/钉钉)
    ↓
OpenClaw Gateway
    ↓
FinBook 技能处理
    ↓
业务逻辑（资产/银行/进销存）
    ↓
生成会计分录
    ↓
中国化合规层验证
    ↓
Beancount 记账
    ↓
文本存储 (.beancount) + SQLite 缓存
```

---

## 三、数据一致性保障

### 3.1 双存储架构

| 存储 | 用途 | 特点 |
|------|------|------|
| **文本文件** | 唯一数据源 | Git 友好，审计追踪 |
| **SQLite** | 查询缓存 | 快速查询，报表生成 |

### 3.2 写入流程

```
1. 获取文件锁
   ↓
2. 写入文本文件（原子操作）
   ↓
3. 发布事件
   ↓
4. 异步更新 SQLite
   ↓
5. 释放文件锁
```

### 3.3 一致性校验

```bash
# 定期校验脚本
python -m finbook.utils.verify_consistency
    ↓
对比文本和数据库记录数
    ↓
如不一致 → 告警 + 自动修复
```

---

## 四、OpenClaw 技能集成

### 4.1 技能接口

```python
from openclaw import ChannelAdapter, Skill

class InvoiceUploadSkill(Skill):
    async def handle_message(self, message):
        # 处理发票上传
        pass
```

### 4.2 配置示例

```yaml
# config/telegram.yaml
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"
  limits:
    max_file_size_mb: 10
    allowed_mime_types:
      - image/jpeg
      - image/png
      - application/pdf
```

---

## 五、部署架构

### 5.1 自托管部署

```
┌─────────────────────────────────────┐
│         用户服务器                   │
│  ┌──────────────────────────────┐   │
│  │  Docker Container            │   │
│  │  ┌────────────────────────┐  │   │
│  │  │  FinBook + OpenClaw    │  │   │
│  │  └────────────────────────┘  │   │
│  │  ┌────────────────────────┐  │   │
│  │  │  SQLite Database       │  │   │
│  │  └────────────────────────┘  │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 5.2 部署脚本

```bash
# 一键部署脚本
docker run -d \
  --name finbook \
  -v ./data:/data \
  -e TELEGRAM_BOT_TOKEN=xxx \
  readapt/finbook:latest
```

---

## 六、安全设计

### 6.1 数据安全

| 措施 | 说明 |
|------|------|
| **存储加密** | SQLite 数据库加密（可选） |
| **传输加密** | TLS 1.3 |
| **访问控制** | Telegram 用户 ID 验证 |
| **审计日志** | 完整操作记录 |

### 6.2 合规安全

| 要求 | 实现 |
|------|------|
| **不可逆记账** | 凭证只追加，不修改 |
| **操作留痕** | 审计日志表 |
| **数据导出** | CSV/Excel 标准格式 |
| **备份机制** | 自动备份脚本 |

---

## 七、性能优化

### 7.1 查询优化

| 场景 | 优化策略 |
|------|----------|
| **凭证查询** | SQLite 索引 |
| **报表生成** | 预计算 + 缓存 |
| **大数据量** | 分页 + 异步 |

### 7.2 并发控制

```python
from filelock import FileLock

with FileLock('ledger.beancount.lock'):
    # 原子写入
    append_to_beancount(transaction)
```

---

## 八、监控与日志

### 8.1 日志配置

```python
from loguru import logger

logger.add("logs/finbook.log", rotation="10 MB")
```

### 8.2 监控指标

| 指标 | 说明 |
|------|------|
| **API 响应时间** | P95 < 500ms |
| **OCR 识别率** | > 95% |
| **数据库一致性** | 100% |
| **系统可用性** | > 99% |

---

**文档版本历史**:

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1.0 | 2026-03-10 | 初始版本 |
