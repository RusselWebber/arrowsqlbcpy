import pytest
import pandas as pd
from arrowsqlbcpy import bulkcopy_from_pandas
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

@pytest.mark.skip(reason="This needs a local SQL Server setup")
def test_load():
    cn = r"Server=localhost,14333;Database=test;UID=<user>;PWD=<pwd>;Encrypt=false;"
    tablename = "test"
    max_chunksize = None
    df = pd.read_parquet(r"/mnt/c/Users/russe/Downloads/yellow_tripdata_2024-01.parquet")

    connection_url = URL.create(
        "mssql+pyodbc",
        username="",
        password="",
        host="127.0.0.1",
        port=14333,
        database="test",
        query={
            "driver": "ODBC Driver 18 for SQL Server",
            "Encrypt": "yes",
            "TrustServerCertificate": "yes",
        },
    )
    engine = create_engine(connection_url)

    # Create the table if necessary
    df.head(1).to_sql(name=tablename, con=engine, index=False, if_exists="replace")

    # Arrow bulk copy
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {tablename}"))
    bulkcopy_from_pandas(df, cn, tablename, max_chunksize)

    # Verify the load worked
    with engine.begin() as conn:
        assert conn.execute(text(f"SELECT COUNT(*) FROM {tablename}")).scalar() == df.shape[0]