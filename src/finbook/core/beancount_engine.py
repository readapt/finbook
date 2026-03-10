"""
Beancount 引擎封装

提供 Beancount 双式记账核心的 Python 封装
"""

from beancount import loader
from beancount.core import data, flags
from datetime import datetime
from typing import List, Dict, Optional
import os


class BeancountEngine:
    """Beancount 记账引擎"""
    
    def __init__(self, ledger_path: str):
        """
        初始化 Beancount 引擎
        
        Args:
            ledger_path: .beancount 文件路径
        """
        self.ledger_path = ledger_path
        self.entries = []
        self.errors = []
        self.options_map = {}
        
        # 确保文件存在
        self._ensure_ledger_file()
    
    def _ensure_ledger_file(self):
        """确保账本文件存在"""
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        if not os.path.exists(self.ledger_path):
            with open(self.ledger_path, 'w') as f:
                f.write(";; FinBook 账本文件\n")
                f.write(f";; 创建时间：{datetime.now().isoformat()}\n\n")
    
    def load(self):
        """加载账本文件"""
        self.entries, self.errors, self.options_map = loader.load_file(self.ledger_path)
        return self.entries, self.errors, self.options_map
    
    def add_transaction(self, entry: data.Transaction):
        """
        添加交易记录
        
        Args:
            entry: Beancount Transaction 对象
        """
        # 追加到文件
        with open(self.ledger_path, 'a') as f:
            f.write(self._entry_to_string(entry))
    
    def _entry_to_string(self, entry: data.Transaction) -> str:
        """将 Transaction 对象转换为文本"""
        lines = []
        lines.append(f"{entry.date} * \"{entry.payee or ''}\" \"{entry.narration}\"")
        
        for posting in entry.postings:
            lines.append(f"  {posting.account:40s} {posting.units}")
        
        lines.append("")
        return "\n".join(lines)
    
    def create_transaction(
        self,
        date: str,
        narration: str,
        postings: List[Dict],
        payee: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> data.Transaction:
        """
        创建交易记录
        
        Args:
            date: 日期 (YYYY-MM-DD)
            narration: 摘要
            postings: 分录列表 [{'account': 'Assets:Bank', 'amount': '100.00 CNY'}]
            payee: 收款人
            tags: 标签列表
        
        Returns:
            data.Transaction 对象
        """
        # 解析日期
        from datetime import datetime
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        
        # 创建分录
        posting_objects = []
        for p in postings:
            account = p['account']
            amount = p['amount']
            # 解析金额
            number, currency = amount.split(' ')
            posting_objects.append(
                data.Posting(account, data.Amount(float(number), currency), None, None, None, None)
            )
        
        # 创建交易
        transaction = data.Transaction(
            meta={'filename': self.ledger_path, 'lineno': 0},
            date=date_obj,
            flag=flags.FLAG_OKAY,
            payee=payee or '',
            narration=narration,
            tags=set(tags or []),
            links=set(),
            postings=posting_objects
        )
        
        return transaction
    
    def query(self, query_string: str):
        """
        执行 BQL 查询
        
        Args:
            query_string: BQL 查询语句
        
        Returns:
            查询结果
        """
        from beancount.query import query
        return query.run_query(self.entries, self.options_map, query_string)
    
    def get_balance_sheet(self):
        """获取资产负债表"""
        from beancount.core import realize
        real_root = realize.realize(self.entries)
        return real_root
    
    def verify(self) -> bool:
        """
        验证账本
        
        Returns:
            是否有错误
        """
        self.load()
        return len(self.errors) == 0
