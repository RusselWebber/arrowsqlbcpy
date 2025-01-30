import pandas as pd
from arrowsqlbcpy import bulkcopy_from_pandas
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from bcpandas import SqlCreds, to_sql
from functools import partial

cn = r"Server=PC\SQLEXPRESS;Database=test;Trusted_Connection=True;Encrypt=false;"
tablename = "test"
max_chunksize = None
df = pd.read_parquet(r"C:\Users\russe\Downloads\yellow_tripdata_2024-01.parquet")

connection_url = URL.create(
    "mssql+pyodbc",
    host=r"PC\SQLEXPRESS",
    database="test",
    query={
        "driver": "SQL Server Native Client 11.0",
        "Encrypt": "yes",
        "TrustServerCertificate": "yes",
    },
)
engine = create_engine(connection_url)
fast_executemany_engine = create_engine(connection_url, echo=False, fast_executemany=True)
creds = SqlCreds.from_engine(engine)

# Create the table
df.head(1).to_sql(name=tablename, con=engine, index=False, if_exists="replace")

def default_to_sql(nrows=None):
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {tablename}"))    
    local_df = df.iloc[:nrows] if nrows else df
    with engine.begin() as conn:
        local_df.to_sql(name=tablename, con=conn, index=False, chunksize=max_chunksize, if_exists="append")

def fast_executemany__to_sql(nrows=None):
    with fast_executemany_engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {tablename}"))    
    local_df = df.iloc[:nrows] if nrows else df
    with engine.begin() as conn:
        local_df.to_sql(name=tablename, con=conn, index=False, chunksize=max_chunksize, if_exists="append")

def arrow_to_sql(nrows=None):
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {tablename}"))    
    local_df = df.iloc[:nrows] if nrows else df
    bulkcopy_from_pandas(local_df, cn, tablename)

def bcpandas_to_sql(nrows=None):
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {tablename}"))    
    local_df = df.iloc[:nrows] if nrows else df
    to_sql(local_df, tablename, creds, index=False, if_exists="append")

default_to_sql_1000 = partial(default_to_sql, 1_000)
fast_executemany__to_sql_1000 = partial(fast_executemany__to_sql, 1_000)
arrow_to_sql_1000 = partial(arrow_to_sql, 1_000)
bcpandas_to_sql_1000 = partial(bcpandas_to_sql, 1_000)
default_to_sql_10000 = partial(default_to_sql, 10_000)
fast_executemany__to_sql_10000 = partial(fast_executemany__to_sql, 10_000)
arrow_to_sql_10000 = partial(arrow_to_sql, 10_000)
bcpandas_to_sql_10000 = partial(bcpandas_to_sql, 10_000)
default_to_sql_100000 = partial(default_to_sql, 100_000)
fast_executemany__to_sql_100000 = partial(fast_executemany__to_sql, 100_000)
arrow_to_sql_100000 = partial(arrow_to_sql, 100_000)
bcpandas_to_sql_100000 = partial(bcpandas_to_sql, 100_000)
default_to_sql_1000000 = partial(default_to_sql, 1_000_000)
fast_executemany__to_sql_1000000 = partial(fast_executemany__to_sql, 1_000_000)
arrow_to_sql_1000000 = partial(arrow_to_sql, 1_000_000)
bcpandas_to_sql_1000000 = partial(bcpandas_to_sql, 1_000_000)

__benchmarks__ = [
    (default_to_sql_1000, fast_executemany__to_sql_1000, "1e3 rows - fast_executemany=True"),
    (default_to_sql_1000, bcpandas_to_sql_1000, "1e3 rows - bcpandas"),
    (default_to_sql_1000, arrow_to_sql_1000, "1e3 rows - pyArrow SQLBulkCopy"),
    (default_to_sql_10000, fast_executemany__to_sql_10000, "1e4 rows - fast_executemany=True"),
    (default_to_sql_10000, bcpandas_to_sql_10000, "1e4 rows - bcpandas"),
    (default_to_sql_10000, arrow_to_sql_10000, "1e4 rows - pyArrow SQLBulkCopy"),        
    (default_to_sql_100000, fast_executemany__to_sql_100000, "1e5 rows - fast_executemany=True"),
    (default_to_sql_100000, bcpandas_to_sql_100000, "1e5 rows - bcpandas"),
    (default_to_sql_100000, arrow_to_sql_100000, "1e5 rows - pyArrow SQLBulkCopy"),    
    (default_to_sql_1000000, fast_executemany__to_sql_1000000, "1e6 rows - fast_executemany=True"),
    (default_to_sql_1000000, bcpandas_to_sql_1000000, "1e6 rows - bcpandas"),
    (default_to_sql_1000000, arrow_to_sql_1000000, "1e6 rows - pyArrow SQLBulkCopy"),        
    (default_to_sql, fast_executemany__to_sql, "3e6 rows - fast_executemany=True"),
    (default_to_sql, bcpandas_to_sql, "3e6 rows - bcpandas"),
    (default_to_sql, arrow_to_sql, "3e6 rows - pyArrow SQLBulkCopy")            
]