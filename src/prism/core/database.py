import duckdb
from pathlib import Path
from typing import Optional, Any, List, Dict
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.conn: Optional[duckdb.DuckDBPyConnection] = None

    def connect(self) -> duckdb.DuckDBPyConnection:
        if self.conn is None:
            self.conn = duckdb.connect(str(self.db_path))
            logger.info(f"Connected to database: {self.db_path}")
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Database connection closed")

    def execute(
        self, sql: str, params: Optional[tuple] = None
    ) -> duckdb.DuckDBPyConnection:
        conn = self.connect()
        if params:
            return conn.execute(sql, params)
        return conn.execute(sql)

    def execute_script(self, sql_script: str):
        conn = self.connect()
        for statement in self._split_sql_statements(sql_script):
            if statement.strip():
                conn.execute(statement)
        logger.info("SQL script executed successfully")

    def query_df(self, sql: str, params: Optional[tuple] = None) -> Any:
        result = self.execute(sql, params)
        return result.df()

    def query_one(self, sql: str, params: Optional[tuple] = None) -> Optional[tuple]:
        result = self.execute(sql, params)
        rows = result.fetchall()
        return rows[0] if rows else None

    def query_all(self, sql: str, params: Optional[tuple] = None) -> List[tuple]:
        result = self.execute(sql, params)
        return result.fetchall()

    def table_exists(self, table_name: str, schema: str = "main") -> bool:
        sql = """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = ? AND table_name = ?
        """
        result = self.query_one(sql, (schema, table_name))
        return result[0] > 0 if result else False

    def schema_exists(self, schema_name: str) -> bool:
        sql = """
            SELECT COUNT(*) FROM information_schema.schemata
            WHERE schema_name = ?
        """
        result = self.query_one(sql, (schema_name,))
        return result[0] > 0 if result else False

    def create_schema(self, schema_name: str, if_not_exists: bool = True):
        if_not_exists_clause = "IF NOT EXISTS" if if_not_exists else ""
        sql = f"CREATE SCHEMA {if_not_exists_clause} {schema_name}"
        self.execute(sql)
        logger.info(f"Schema '{schema_name}' created")

    def list_tables(self, schema: str = "main") -> List[str]:
        sql = """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = ?
            ORDER BY table_name
        """
        results = self.query_all(sql, (schema,))
        return [r[0] for r in results]

    def list_schemas(self) -> List[str]:
        sql = """
            SELECT schema_name FROM information_schema.schemata
            ORDER BY schema_name
        """
        results = self.query_all(sql)
        return [r[0] for r in results]

    def get_table_info(
        self, table_name: str, schema: str = "main"
    ) -> List[Dict[str, Any]]:
        sql = f"DESCRIBE {schema}.{table_name}"
        df = self.query_df(sql)
        return df.to_dict("records")

    def _split_sql_statements(self, sql_script: str) -> List[str]:
        statements = []
        current = []
        in_string = False

        for line in sql_script.split("\n"):
            if line.strip().startswith("--"):
                continue

            current.append(line)

            if ";" in line and not in_string:
                statements.append("\n".join(current))
                current = []

        if current:
            statements.append("\n".join(current))

        return statements

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def init_database(db_path: str, sql_script_path: Optional[str] = None) -> Database:
    db = Database(db_path)

    if sql_script_path:
        script_path = Path(sql_script_path)
        if script_path.exists():
            with open(script_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
            db.execute_script(sql_script)
            logger.info(f"Database initialized with script: {sql_script_path}")

    return db


def get_connection(db_path: str) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(db_path))
