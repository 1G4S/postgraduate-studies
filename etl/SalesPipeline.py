import os
import urllib
import logging
import pandas as pd
import requests
from sqlalchemy import create_engine

class SalesPipeline:
    def __init__(self, customers_path: str, sales_path: str, api_url: str):
        self.customers_path = customers_path
        self.sales_path = sales_path
        self.api_url = api_url
        self.engine = self._create_db_engine()

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

    def extract(self) -> dict:
        """Extracting data from varius sources."""
        logging.info("Rozpoczęcie ekstrakcji danych z plików i API...")
        api_data = requests.get(self.api_url).json()

        return {
            'customers': pd.read_json(self.customers_path),
            'sales': pd.read_csv(self.sales_path),
            'products': pd.DataFrame(api_data)[['id', 'title', 'price']].rename(columns={'id': 'product_id'})
        }
