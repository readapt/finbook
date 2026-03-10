# FinBook 合规层设计文档

**版本**: v0.1.0  
**创建时间**: 2026-03-11  
**状态**: 设计中

---

## 一、合规需求分析

### 1.1 财政部 2025 规范要求

| 要求 | 实现方案 | 状态 |
|------|----------|------|
| **凭证不可逆** | 只追加，不修改；红字冲销 | ✅ 已设计 |
| **凭证连续编号** | 按日生成序列号 | ✅ 已实现 |
| **凭证审核流程** | 制单→审核→记账 | 🟡 设计中 |
| **权限分离** | 管理员/会计/出纳/只读 | 🟡 设计中 |
| **操作留痕** | 审计日志表 | ✅ 已实现 |
| **数据导出** | CSV/Excel 标准格式 | ✅ 已实现 |

### 1.2 必须补充的合规功能

1. **凭证审核流程** - 财政部规范强制要求
2. **角色权限系统** - 制单/审核/记账分离
3. **科目体系** - 内置小企业会计准则科目表
4. **自动备份** - 定时备份到本地/云存储

---

## 二、角色权限系统设计

### 2.1 角色定义

| 角色 | 权限 | 说明 |
|------|------|------|
| **管理员** | 全部权限 | 系统配置、用户管理 |
| **会计主管** | 审核 + 记账 | 凭证审核、过账 |
| **会计** | 制单 + 查询 | 凭证录入、查询 |
| **出纳** | 资金相关 | 银行对账、资金查询 |
| **只读** | 仅查询 | 老板/审计查看 |

### 2.2 权限矩阵

| 功能 | 管理员 | 会计主管 | 会计 | 出纳 | 只读 |
|------|--------|----------|------|------|------|
| 凭证制单 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 凭证审核 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 凭证记账 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 凭证查询 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 银行对账 | ✅ | ✅ | ❌ | ✅ | ❌ |
| 报表查询 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 用户管理 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 系统配置 | ✅ | ❌ | ❌ | ❌ | ❌ |

### 2.3 数据库设计

```sql
-- 用户表
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'supervisor', 'accountant', 'cashier', 'readonly')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- 角色权限表
CREATE TABLE role_permissions (
    role TEXT NOT NULL,
    permission TEXT NOT NULL,
    PRIMARY KEY (role, permission)
);

-- 操作日志表（已有）
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    voucher_id TEXT,
    user_id TEXT,
    user_ip TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT
);
```

---

## 三、凭证审核流程设计

### 3.1 状态机

```
草稿 → 待审核 → 已审核 → 已记账
        ↓
       驳回 → 草稿
```

### 3.2 状态定义

| 状态 | 说明 | 可操作角色 |
|------|------|------------|
| **草稿** | 会计录入中，未提交 | 制单人 |
| **待审核** | 已提交，等待审核 | 会计主管 |
| **已审核** | 审核通过，等待记账 | 会计主管 |
| **已记账** | 已过账，不可修改 | 系统 |
| **已驳回** | 审核不通过 | 制单人 |

### 3.3 凭证表扩展

```sql
ALTER TABLE vouchers ADD COLUMN status TEXT DEFAULT 'draft' 
    CHECK(status IN ('draft', 'pending', 'approved', 'posted', 'rejected'));

ALTER TABLE vouchers ADD COLUMN auditor_id TEXT;
ALTER TABLE vouchers ADD COLUMN audited_at TIMESTAMP;
ALTER TABLE vouchers ADD COLUMN reject_reason TEXT;
```

### 3.4 审核流程

```python
def submit_voucher(voucher_id: str, user_id: str) -> bool:
    """提交凭证审核"""
    # 检查权限：制单人
    # 状态变更：draft → pending
    
def approve_voucher(voucher_id: str, user_id: str) -> bool:
    """审核通过"""
    # 检查权限：会计主管
    # 状态变更：pending → approved
    
def reject_voucher(voucher_id: str, user_id: str, reason: str) -> bool:
    """驳回凭证"""
    # 检查权限：会计主管
    # 状态变更：pending → rejected
    
def post_voucher(voucher_id: str, user_id: str) -> bool:
    """记账（过账）"""
    # 检查权限：会计主管
    # 状态变更：approved → posted
    # 写入 Beancount 账本
```

---

## 四、会计科目体系

### 4.1 内置科目表（小企业会计准则）

```yaml
# 资产类 (1000-1999)
1001: 库存现金
1002: 银行存款
1012: 其他货币资金
1101: 短期投资
1122: 应收账款
1123: 预付账款
1132: 其他应收款
1401: 材料采购
1402: 在途物资
1403: 原材料
1405: 库存商品
1411: 周转材料
1501: 固定资产
1502: 累计折旧
1511: 固定资产清理
1521: 在建工程
1601: 工程物资
1602: 累计摊销
1603: 无形资产
1701: 长期待摊费用

# 负债类 (2000-2999)
2001: 短期借款
2201: 应付票据
2202: 应付账款
2203: 预收账款
2211: 应付职工薪酬
2221: 应交税费
222101: 应交增值税 - 进项税额
222102: 应交增值税 - 销项税额
2231: 应付利息
2232: 应付股利
2241: 其他应付款

# 所有者权益类 (3000-3999)
3001: 实收资本
3002: 资本公积
3101: 盈余公积
3103: 本年利润
3104: 利润分配

# 成本类 (4000-4999)
4001: 生产成本
4101: 制造费用

# 损益类 (5000-5999)
5001: 主营业务收入
5051: 其他业务收入
5111: 投资收益
5301: 营业外收入
5401: 主营业务成本
5402: 其他业务成本
5403: 税金及附加
5601: 销售费用
5602: 管理费用
5603: 财务费用
5711: 营业外支出
5801: 所得税费用
```

### 4.2 科目配置

```python
# config/accounts.yaml
chart_of_accounts:
  standard: "小企业会计准则"  # 或"企业会计准则"
  version: "2025"
  
  # 科目扩展
  custom_accounts:
    - code: "100201"
      name: "工商银行 XX 支行"
      parent: "1002"
      
  # 禁用科目
  disabled_accounts:
    - "1001"  # 如不使用现金
```

---

## 五、自动备份设计

### 5.1 备份策略

| 备份类型 | 频率 | 保留期限 | 内容 |
|----------|------|----------|------|
| **完整备份** | 每日 | 30 天 | 全部数据 |
| **增量备份** | 每小时 | 7 天 | 变更数据 |
| **归档备份** | 每月 | 10 年 | 月度账套 |

### 5.2 备份内容

```
backups/
├── daily/
│   ├── 2026-03-10/
│   │   ├── ledger.beancount    # 账本文件
│   │   ├── finance.db          # 数据库
│   │   ├── invoices/           # 发票原件
│   │   └── manifest.json       # 备份清单
│   └── ...
└── monthly/
    ├── 2026-02/
    └── ...
```

### 5.3 备份配置

```yaml
# config/backup.yaml
backup:
  enabled: true
  
  # 完整备份（每日凌晨 2 点）
  daily:
    schedule: "0 2 * * *"
    retention_days: 30
    destination: "./storage/backups/daily"
    
  # 增量备份（每小时）
  hourly:
    schedule: "0 * * * *"
    retention_days: 7
    destination: "./storage/backups/hourly"
    
  # 归档备份（每月 1 号）
  monthly:
    schedule: "0 0 1 * *"
    retention_months: 120  # 10 年
    destination: "./storage/backups/monthly"
    
  # 云存储备份（可选）
  cloud:
    enabled: false
    provider: "aliyun_oss"  # 或 tencent_cos
    bucket: "finbook-backups"
    region: "cn-shanghai"
```

### 5.4 恢复验证

```python
def verify_backup(backup_path: str) -> bool:
    """验证备份完整性"""
    # 1. 检查 manifest.json
    # 2. 校验文件哈希
    # 3. 尝试恢复数据库
    # 4. 验证账本文件
    
def restore_backup(backup_path: str, target_path: str) -> bool:
    """恢复备份"""
    # 1. 停止服务
    # 2. 解压备份文件
    # 3. 恢复数据库
    # 4. 恢复账本文件
    # 5. 启动服务
    # 6. 验证恢复结果
```

---

## 六、合规检查清单

### 6.1 每日检查

- [ ] 凭证连续编号检查
- [ ] 借贷平衡检查
- [ ] 未审核凭证提醒
- [ ] 备份完整性验证

### 6.2 每月检查

- [ ] 科目余额表平衡
- [ ] 银行对账完成
- [ ] 纳税申报表生成
- [ ] 月度归档备份

### 6.3 每年检查

- [ ] 年度账套归档
- [ ] 会计档案整理
- [ ] 系统安全审计
- [ ] 合规性自查报告

---

## 七、实施计划

| 任务 | 优先级 | 预计工时 |
|------|--------|----------|
| 角色权限系统 | 🔴 P0 | 3-5 天 |
| 凭证审核流程 | 🔴 P0 | 3-5 天 |
| 会计科目体系 | 🔴 P0 | 2-3 天 |
| 自动备份机制 | 🟡 P1 | 2-3 天 |
| 合规检查清单 | 🟡 P1 | 1-2 天 |

---

## 八、与现有代码集成

### 8.1 ComplianceLayer 扩展

```python
# src/finbook/core/compliance.py

class ComplianceLayer:
    # 新增方法
    def create_user(self, username: str, password: str, role: str) -> str:
        """创建用户"""
        
    def check_permission(self, user_id: str, permission: str) -> bool:
        """检查权限"""
        
    def submit_voucher(self, voucher_id: str, user_id: str) -> bool:
        """提交凭证审核"""
        
    def approve_voucher(self, voucher_id: str, user_id: str) -> bool:
        """审核凭证"""
        
    def schedule_backup(self, config: dict):
        """调度备份任务"""
```

### 8.2 配置更新

```yaml
# config/default.yaml

# 新增
compliance:
  # 凭证审核
  voucher_approval:
    enabled: true
    require_approval: true  # 强制审核
    
  # 角色权限
  roles:
    enabled: true
    default_role: "accountant"
    
  # 科目体系
  chart_of_accounts:
    standard: "小企业会计准则"
    version: "2025"
    
  # 备份
  backup:
    enabled: true
    # ... 如上配置
```

---

**文档版本历史**:

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1.0 | 2026-03-11 | 初始版本 |
