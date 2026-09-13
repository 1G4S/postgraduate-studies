from etl.SalesPipeline import SalesPipeline

if __name__ == "__main__":
    pipeline = SalesPipeline(
        customers_path='data/customers.json',
        sales_path='data/sales.csv',
        api_url='https://fakestoreapi.com/products'
    )
    pipeline.run()