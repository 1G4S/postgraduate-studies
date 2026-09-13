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

    def transform(self, data: dict) -> dict:
        """Cleaning data and building star schema"""
        logging.info("Transformacja i modelowanie danych")
        df_sales = data['sales']
        df_sales['date'] = pd.to_datetime(df_sales['date'])

        df_date = pd.DataFrame({'date_id': df_sales['date'].unique()})
        df_date['year'] = df_date['date_id'].dt.year
        df_date['month'] = df_date['date_id'].dt.month
        df_date['day'] = df_date['date_id'].dt.day

        df_fact = df_sales.merge(data['products'], on='product_id', how='left')
        df_fact['total_amount'] = df_fact['qty'] * df_fact['price']
        df_fact = df_fact[['sale_id', 'customer_id', 'product_id', 'date', 'qty', 'total_amount']].rename(
            columns={'date': 'date_id'})

        return {
            'dim_customer': data['customers'],
            'dim_product': data['products'],
            'dim_date': df_date,
            'fact_sales': df_fact
        }
