"""
中国化合规层

实现财政部 2025 规范要求的合规功能:
- 中国会计科目映射
- 凭证编号（连续、不可逆）
- 审计日志
- 数据导出
"""

from datetime import datetime
from typing import Dict, List, Optional
import sqlite3
import os


class ComplianceLayer:
    """中国化合规层"""
    
    def __init__(self, db_path: str):
        """
        初始化合规层
        
        Args:
            db_path: SQLite 数据库路径
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 凭证表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vouchers (
                id TEXT PRIMARY KEY,
                date DATE NOT NULL,
                summary TEXT NOT NULL,
                payee TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                is_reversed BOOLEAN DEFAULT FALSE,
                reversed_by TEXT,
                reversed_at TIMESTAMP
            )
        ''')
        
        # 凭证分录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voucher_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                voucher_id TEXT NOT NULL,
                account_code TEXT NOT NULL,
                account_name TEXT NOT NULL,
                direction TEXT CHECK(direction IN ('debit', 'credit')),
                amount DECIMAL(18,2) NOT NULL,
                FOREIGN KEY (voucher_id) REFERENCES vouchers(id)
            )
        ''')
        
        # 审计日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                voucher_id TEXT,
                user_id TEXT,
                user_ip TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
        ''')
        
        # 凭证编号序列
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voucher_sequence (
                id INTEGER PRIMARY KEY,
                date DATE UNIQUE NOT NULL,
                last_number INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_voucher_id(self, date: str = None) -> str:
        """
        生成连续凭证编号
        
        Args:
            date: 日期 (YYYY-MM-DD)，默认今天
        
        Returns:
            凭证编号 (格式：VCH-YYYYMMDD-000001)
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取或创建序列
        cursor.execute('''
            INSERT OR IGNORE INTO voucher_sequence (date, last_number)
            VALUES (?, 0)
        ''', (date,))
        
        # 更新序列
        cursor.execute('''
            UPDATE voucher_sequence 
            SET last_number = last_number + 1 
            WHERE date = ?
            RETURNING last_number
        ''', (date,))
        
        last_number = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        
        # 生成凭证 ID
        date_str = date.replace('-', '')
        return f"VCH-{date_str}-{last_number:06d}"
    
    def create_voucher(
        self,
        date: str,
        summary: str,
        lines: List[Dict],
        payee: Optional[str] = None,
        created_by: Optional[str] = None,
        user_ip: Optional[str] = None
    ) -> str:
        """
        创建凭证（符合财政部规范）
        
        Args:
            date: 日期 (YYYY-MM-DD)
            summary: 摘要
            lines: 分录列表
            payee: 收款人
            created_by: 创建人
            user_ip: 用户 IP
        
        Returns:
            凭证 ID
        """
        # 生成凭证 ID
        voucher_id = self.generate_voucher_id(date)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 插入凭证
        cursor.execute('''
            INSERT INTO vouchers (id, date, summary, payee, created_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (voucher_id, date, summary, payee, created_by))
        
        # 插入分录
        for line in lines:
            cursor.execute('''
                INSERT INTO voucher_lines (voucher_id, account_code, account_name, direction, amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (voucher_id, line['account_code'], line['account_name'], 
                  line['direction'], line['amount']))
        
        # 记录审计日志
        self._log_action('create_voucher', voucher_id, created_by, user_ip, {
            'date': date,
            'summary': summary,
            'lines_count': len(lines)
        })
        
        conn.commit()
        conn.close()
        
        return voucher_id
    
    def reverse_voucher(self, voucher_id: str, reason: str, reversed_by: str = None) -> bool:
        """
        红字冲销凭证（不可删除，只能冲销）
        
        Args:
            voucher_id: 原凭证 ID
            reason: 冲销原因
            reversed_by: 操作人
        
        Returns:
            是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 检查凭证是否存在
        cursor.execute('SELECT * FROM vouchers WHERE id = ?', (voucher_id,))
        if not cursor.fetchone():
            conn.close()
            return False
        
        # 标记为已冲销
        cursor.execute('''
            UPDATE vouchers 
            SET is_reversed = TRUE, reversed_by = ?, reversed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (reversed_by, voucher_id))
        
        # 记录审计日志
        self._log_action('reverse_voucher', voucher_id, reversed_by, None, {
            'reason': reason
        })
        
        conn.commit()
        conn.close()
        
        return True
    
    def _log_action(self, action: str, voucher_id: str = None, 
                    user_id: str = None, user_ip: str = None, 
                    details: Dict = None):
        """记录审计日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        import json
        cursor.execute('''
            INSERT INTO audit_log (action, voucher_id, user_id, user_ip, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (action, voucher_id, user_id, user_ip, json.dumps(details or {})))
        
        conn.commit()
        conn.close()
    
    def export_vouchers(self, start_date: str, end_date: str) -> List[Dict]:
        """
        导出凭证（符合财政部数据导出要求）
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            凭证列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT v.*, GROUP_CONCAT(
                vl.account_code || '|' || vl.account_name || '|' || 
                vl.direction || '|' || vl.amount, ';'
            ) as lines
            FROM vouchers v
            LEFT JOIN voucher_lines vl ON v.id = vl.voucher_id
            WHERE v.date BETWEEN ? AND ?
            GROUP BY v.id
            ORDER BY v.date, v.id
        ''', (start_date, end_date))
        
        vouchers = []
        for row in cursor.fetchall():
            vouchers.append({
                'id': row[0],
                'date': row[1],
                'summary': row[2],
                'payee': row[3],
                'created_at': row[4],
                'created_by': row[5],
                'is_reversed': row[6],
                'lines': self._parse_lines(row[7])
            })
        
        conn.close()
        return vouchers
    
    def _parse_lines(self, lines_str: str) -> List[Dict]:
        """解析分录字符串"""
        if not lines_str:
            return []
        
        lines = []
        for line in lines_str.split(';'):
            parts = line.split('|')
            if len(parts) == 4:
                lines.append({
                    'account_code': parts[0],
                    'account_name': parts[1],
                    'direction': parts[2],
                    'amount': float(parts[3])
                })
        return lines
    
    def get_audit_log(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """获取审计日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM audit_log'
        params = []
        
        if start_date and end_date:
            query += ' WHERE timestamp BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        
        query += ' ORDER BY timestamp DESC'
        
        cursor.execute(query, params)
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row[0],
                'action': row[1],
                'voucher_id': row[2],
                'user_id': row[3],
                'user_ip': row[4],
                'timestamp': row[5],
                'details': row[6]
            })
        
        conn.close()
        return logs
