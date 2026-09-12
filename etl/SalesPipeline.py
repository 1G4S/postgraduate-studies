import os
import urllib
from sqlalchemy import create_engine

class SalesPipeline:
    def __init__(self, customers_path: str, sales_path: str, api_url: str):
        self.customers_path = customers_path
        self.sales_path = sales_path
        self.api_url = api_url
        self.engine = self._create_db_engine()

    def _create_db_engine(self):
        def _create_db_engine(self):
            """Connecting to database"""
            params = urllib.parse.quote_plus(
                f"Driver={{ODBC Driver 18 for SQL Server}};"
                f"Server=tcp:{os.environ.get('DB_SERVER')},1433;"
                f"Database={os.environ.get('DB_NAME')};"
                f"Uid={os.environ.get('DB_USER')};"
                f"Pwd={os.environ.get('DB_PASS')};"
                f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
            )
            return create_engine(f"mssql+pyodbc:///?odbc_connect={params}")