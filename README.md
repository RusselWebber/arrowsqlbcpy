![GitHub Latest Tag](https://badgen.net/github/tag/RusselWebber/arrowsqlbcpy) ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/RusselWebber/arrowsqlbcpy/ci.yml) ![PyPI Python Versions](https://img.shields.io/pypi/pyversions/arrowsqlbcpy)

# arrowsqlbcpy

A tiny library that uses .Net SqlBulkCopy to enable fast data loading to Microsoft SQL Server. Apache Arrow is used to serialise data between Python and the native DLL. .Net Native Library AOT compilation is used to generate the native DLL.

This library is _much_ faster than any other Python solution, including bcpandas, pyodbc and pymssql. See the benchmark results below.

## Installation

Binary wheels are available from PyPi and can be installed using your preferred package manager:

> pip install arrowsqlbcpy

or

> uv add arrowsqlbcpy

## Requirements

Wheels are available for the latest versions of Windows 64 bit, MacOS ARM 64bit and Ubuntu 64 bit.

Wheels are available for Python 3.9-3.13.

### Linux support

The Ubuntu wheels _may_ work on other Linux distros. Building C# native libaries and then packaging appropriately for multiple Linux distros is not straightforward. The simplest solution for most Linux distros is to simply pull the source from Github and build locally. These are the high-level steps:

1. Install .net
   https://learn.microsoft.com/en-us/dotnet/core/install/linux
2. Clone the source
   > git clone https://github.com/RusselWebber/arrowsqlbcpy
3. Install uv
   https://docs.astral.sh/uv/getting-started/installation/
4. Build the wheel locally
   > uv build --wheel
5. Install the wheel
   > pip install dist/wheel_file.whl

## Usage

Connection strings for .Net are documented [here](https://www.connectionstrings.com/microsoft-data-sqlclient/)

```python

import pandas as pd
from arrowsqlbcpy import bulkcopy_from_pandas

# Create a connection string
cn = r"Server=myServerAddress;Database=myDataBase;Trusted_Connection=True;"
# The table to load into must exist and have the same column names and types as the pandas df
tablename = "test"

df = pd.DataFrame({"a":[1]*10000, "b":[2]*10000, "c":[3]*10000})

bulkcopy_from_pandas(df, cn, tablename)

```

When testing it can be useful to have pandas create the table for you, see [tests/test_load.py](https://github.com/RusselWebber/arrowsqlbcpy/blob/main/tests/test_load.py) for an example.

## Benchmarks

The benchmarks were run using the [richbench](https://github.com/tonybaloney/rich-bench) package. Tests were run repeatedly to get stable benchmarks.

> richbench ./benchmarks

The benchmarks load a 3m row parquet file of New York taxi data. Times are recorded for loading 1000 rows, 10 000 rows, 100 000 rows, 1 000 000 rows and finally all 3 000 000 rows.

The benchmarks have a baseline of using pandas `to_sql()` and SQLAlchemy with pyodbc and pymssql. This is a common solution for loading pandas dataframes into SQL Server.

The benchmarks then show the time taken to load using various alternative strategies:

| Label                 | Description                                                                                                                                                                                                                    |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| fast_executemany=True | Use pandas `to_sql()`, SQLAlchemy, pyodbc, pymssql with the fast_executemany=True option as discussed [here](https://stackoverflow.com/questions/48006551/speeding-up-pandas-dataframe-to-sql-with-fast-executemany-of-pyodbc) |
| bcpandas              | Use the [bcpandas](https://github.com/yehoshuadimarsky/bcpandas) package to load the dataframes. The package writes temp files and spawns bcp processes to load them                                                           |
| arrowsqlbcp           | This package using .Net SqlBulkCopy                                                                                                                                                                                            |

The richbench tables show the min, max and mean time in seconds for the baseline in the left three columns; then the min, max, mean time in seconds for the alternative strategy.

For example this row:

| Benchmark                        | Min | Max | Mean | Min (+)  | Max (+)  | Mean (+) |
| -------------------------------- | --- | --- | ---- | -------- | -------- | -------- |
| 1e3 rows - fast_executemany=True | 1.0 | 1.0 | 1.0  | 0.5 (2x) | 0.5 (2x) | 0.5 (2x) |

should be interpreted as: the strategy of setting fast_executemany=True resulted in a 2x speedup over the baseline when loading 1000 rows, so fast_executemany=True reduced the average time in seconds to load 1000 rows from 1.0 to 0.5, a 2x speedup.

### Windows 11 (local db)

tbc

### Ubuntu (WSL2) (local db)

tbc

Benchmarks for the typical case of a remote DB still need to be added.

## Limitations

`bulkcopy_from_pandas()` will establish its own database connection to load the data, reusing existing connections and transactions are not supported.

Only basic MacOS testing has been done.
