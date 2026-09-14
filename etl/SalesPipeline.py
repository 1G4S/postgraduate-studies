import os
import urllib
import logging
import pandas as pd
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm.sync import clear


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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(self.api_url, headers=headers)

        if response.status_code != 200:
            logging.error(f"Błąd poł. z API. Status: {response.status_code}, Odpowiedź: {response.text}")
            response.raise_for_status()

        api_data = response.json()['products']

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

        df_fact = df_sales.merge(data['products'], on='product_id', how='inner')
        df_fact['total_amount'] = df_fact['qty'] * df_fact['price']
        df_fact = df_fact[['sale_id', 'customer_id', 'product_id', 'date', 'qty', 'total_amount']].rename(
            columns={'date': 'date_id'})

        return {
            'dim_customer': data['customers'],
            'dim_product': data['products'],
            'dim_date': df_date,
            'fact_sales': df_fact
        }

    def load(self, transformed_data: dict):
        """Loading data to DWH"""
        logging.info("Ładowanie danych do Azure")
        for table_name, df in transformed_data.items():
            df.to_sql(table_name, self.engine, if_exists='append', index=False)
            logging.info(f"Załadowano tabelę: {table_name}")

    def clear_tables(self):
        """Clean tables"""
        logging.info("Usuwanie danych")

        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM fact_sales;"))

            conn.execute(text("DELETE FROM dim_customer;"))
            conn.execute(text("DELETE FROM dim_product;"))
            conn.execute(text("DELETE FROM dim_date;"))

        logging.info("Sukces. Dane usunięte!")

    def run(self):
        """Full pipeline"""
        try:
            self.clear_tables()
            raw_data = self.extract()
            final_data = self.transform(raw_data)
            self.load(final_data)
            logging.info("ETL zakończony sukcesem")
        except Exception as e:
            logging.error(f"Błąd w ETL: {e}")
            raise