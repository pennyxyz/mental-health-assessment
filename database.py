import sqlite3
import pandas as pd
from datetime import datetime

class Database:
    def __init__(self, db_name="mental_health.db"):
        """初始化数据库连接"""
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()
    
    def create_table(self):
        """创建评估记录表"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT,
                department TEXT,
                assessment_date TEXT,
                resilience_score REAL,
                coping_score REAL,
                stress_score REAL,
                scl90_score REAL,
                risk_level TEXT
            )
        """)
        self.conn.commit()
        print("✅ 数据表已创建/已存在")
    
    def add_assessment(self, employee_id, department, 
                       resilience_score, coping_score, 
                       stress_score, scl90_score, risk_level):
        """添加一条评估记录"""
        assessment_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute("""
            INSERT INTO assessments 
            (employee_id, department, assessment_date, 
             resilience_score, coping_score, stress_score, scl90_score, risk_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (employee_id, department, assessment_date,
              resilience_score, coping_score, stress_score, scl90_score, risk_level))
        self.conn.commit()
        print(f"✅ 已保存评估记录：{employee_id}")
    
    def get_all_assessments(self):
        """获取所有评估记录"""
        query = "SELECT * FROM assessments ORDER BY assessment_date DESC"
        return pd.read_sql_query(query, self.conn)
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()

# 测试代码（当直接运行此文件时执行）
if __name__ == "__main__":
    db = Database()
    # 添加一条测试数据
    db.add_assessment(
        employee_id="TEST001",
        department="测试部",
        resilience_score=75.5,
        coping_score=68.2,
        stress_score=42.3,
        scl90_score=35.8,
        risk_level="中风险"
    )
    
    # 查询并显示所有数据
    df = db.get_all_assessments()
    print("📊 数据库中的所有记录：")
    print(df)
    
    db.close()