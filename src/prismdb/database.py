"""
PRISM-DB Database Connection Manager
管理DuckDB连接和基础操作
"""
import duckdb
from pathlib import Path
from typing import Optional, Any, List, Dict
import logging

logger = logging.getLogger(__name__)


class Database:
    """DuckDB数据库连接管理器"""
    
    def __init__(self, db_path: str):
        """
        初始化数据库连接
        
        Args:
            db_path: DuckDB数据库文件路径
        """
        self.db_path = Path(db_path)
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
        
    def connect(self) -> duckdb.DuckDBPyConnection:
        """建立数据库连接"""
        if self.conn is None:
            self.conn = duckdb.connect(str(self.db_path))
            logger.info(f"Connected to database: {self.db_path}")
        return self.conn
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")
    
    def execute(self, sql: str, params: Optional[tuple] = None) -> duckdb.DuckDBPyConnection:
        """
        执行SQL语句
        
        Args:
            sql: SQL语句
            params: 参数（可选）
            
        Returns:
            DuckDB connection对象
        """
        conn = self.connect()
        if params:
            return conn.execute(sql, params)
        return conn.execute(sql)
    
    def execute_script(self, sql_script: str):
        """
        执行SQL脚本（多条语句）
        
        Args:
            sql_script: SQL脚本
        """
        conn = self.connect()
        for statement in self._split_sql_statements(sql_script):
            if statement.strip():
                conn.execute(statement)
        logger.info("SQL script executed successfully")
    
    def query_df(self, sql: str, params: Optional[tuple] = None) -> Any:
        """
        查询并返回pandas DataFrame
        
        Args:
            sql: SQL查询语句
            params: 参数（可选）
            
        Returns:
            pandas DataFrame
        """
        result = self.execute(sql, params)
        return result.df()
    
    def query_one(self, sql: str, params: Optional[tuple] = None) -> Optional[tuple]:
        """
        查询单行结果
        
        Args:
            sql: SQL查询语句
            params: 参数（可选）
            
        Returns:
            单行结果或None
        """
        result = self.execute(sql, params)
        rows = result.fetchall()
        return rows[0] if rows else None
    
    def query_all(self, sql: str, params: Optional[tuple] = None) -> List[tuple]:
        """
        查询所有结果
        
        Args:
            sql: SQL查询语句
            params: 参数（可选）
            
        Returns:
            结果列表
        """
        result = self.execute(sql, params)
        return result.fetchall()
    
    def table_exists(self, table_name: str, schema: str = 'main') -> bool:
        """
        检查表是否存在
        
        Args:
            table_name: 表名
            schema: Schema名称
            
        Returns:
            True if exists
        """
        sql = """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = ? AND table_name = ?
        """
        result = self.query_one(sql, (schema, table_name))
        return result[0] > 0 if result else False
    
    def schema_exists(self, schema_name: str) -> bool:
        """
        检查schema是否存在
        
        Args:
            schema_name: Schema名称
            
        Returns:
            True if exists
        """
        sql = """
            SELECT COUNT(*) FROM information_schema.schemata
            WHERE schema_name = ?
        """
        result = self.query_one(sql, (schema_name,))
        return result[0] > 0 if result else False
    
    def create_schema(self, schema_name: str, if_not_exists: bool = True):
        """
        创建schema
        
        Args:
            schema_name: Schema名称
            if_not_exists: 如果存在则忽略
        """
        if_not_exists_clause = "IF NOT EXISTS" if if_not_exists else ""
        sql = f"CREATE SCHEMA {if_not_exists_clause} {schema_name}"
        self.execute(sql)
        logger.info(f"Schema '{schema_name}' created")
    
    def list_tables(self, schema: str = 'main') -> List[str]:
        """
        列出schema中的所有表
        
        Args:
            schema: Schema名称
            
        Returns:
            表名列表
        """
        sql = """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = ?
            ORDER BY table_name
        """
        results = self.query_all(sql, (schema,))
        return [r[0] for r in results]
    
    def list_schemas(self) -> List[str]:
        """
        列出所有schema
        
        Returns:
            Schema名称列表
        """
        sql = """
            SELECT schema_name FROM information_schema.schemata
            ORDER BY schema_name
        """
        results = self.query_all(sql)
        return [r[0] for r in results]
    
    def get_table_info(self, table_name: str, schema: str = 'main') -> List[Dict[str, Any]]:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            schema: Schema名称
            
        Returns:
            列信息列表
        """
        sql = f"DESCRIBE {schema}.{table_name}"
        df = self.query_df(sql)
        return df.to_dict('records')
    
    def _split_sql_statements(self, sql_script: str) -> List[str]:
        """
        分割SQL脚本为单独的语句
        
        Args:
            sql_script: SQL脚本
            
        Returns:
            语句列表
        """
        # 简单的分割逻辑，按分号分割
        # 注意：不处理字符串内的分号
        statements = []
        current = []
        in_string = False
        
        for line in sql_script.split('\n'):
            # 跳过注释
            if line.strip().startswith('--'):
                continue
            
            current.append(line)
            
            # 检查是否到达语句结尾
            if ';' in line and not in_string:
                statements.append('\n'.join(current))
                current = []
        
        if current:
            statements.append('\n'.join(current))
        
        return statements
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


def init_database(db_path: str, sql_script_path: Optional[str] = None) -> Database:
    """
    初始化数据库
    
    Args:
        db_path: 数据库文件路径
        sql_script_path: SQL初始化脚本路径（可选）
        
    Returns:
        Database对象
    """
    db = Database(db_path)
    
    # 如果提供了SQL脚本，执行初始化
    if sql_script_path:
        script_path = Path(sql_script_path)
        if script_path.exists():
            with open(script_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            db.execute_script(sql_script)
            logger.info(f"Database initialized with script: {sql_script_path}")
    
    return db


# 便捷函数
def get_connection(db_path: str) -> duckdb.DuckDBPyConnection:
    """
    获取DuckDB连接（便捷函数）
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        DuckDB连接
    """
    return duckdb.connect(str(db_path))
