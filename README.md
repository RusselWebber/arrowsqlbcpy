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

| Benchmark                        | Min     | Max     | Mean    | Min (+)         | Max (+)         | Mean (+)        |
| -------------------------------- | ------- | ------- | ------- | --------------- | --------------- | --------------- |
| 1e3 rows - fast_executemany=True | 0.050   | 0.109   | 0.079   | 0.053 (-1.1x)   | 0.061 (1.8x)    | 0.057 (1.4x)    |
| 1e3 rows - bcpandas              | 0.054   | 0.058   | 0.056   | 0.142 (-2.6x)   | 0.196 (-3.4x)   | 0.169 (-3.0x)   |
| 1e3 rows - arrowsqlbcp           | 0.053   | 0.055   | 0.054   | 0.015 (3.6x)    | 0.089 (-1.6x)   | 0.052 (1.0x)    |
| 1e4 rows - fast_executemany=True | 0.482   | 0.541   | 0.512   | 0.471 (1.0x)    | 0.473 (1.1x)    | 0.472 (1.1x)    |
| 1e4 rows - bcpandas              | 0.460   | 0.468   | 0.464   | 0.356 (1.3x)    | 0.359 (1.3x)    | 0.358 (1.3x)    |
| 1e4 rows - arrowsqlbcp           | 0.463   | 0.474   | 0.468   | 0.094 (4.9x)    | 0.097 (4.9x)    | 0.096 (4.9x)    |
| 1e5 rows - fast_executemany=True | 4.795   | 4.879   | 4.837   | 4.777 (1.0x)    | 4.799 (1.0x)    | 4.788 (1.0x)    |
| 1e5 rows - bcpandas              | 4.689   | 4.759   | 4.724   | 2.574 (1.8x)    | 2.967 (1.6x)    | 2.771 (1.7x)    |
| 1e5 rows - arrowsqlbcp           | 4.754   | 4.914   | 4.834   | 0.855 (5.6x)    | 0.886 (5.5x)    | 0.870 (5.6x)    |
| 1e6 rows - fast_executemany=True | 54.914  | 56.384  | 55.649  | 54.161 (1.0x)   | 55.123 (1.0x)   | 54.642 (1.0x)   |
| 1e6 rows - bcpandas              | 54.626  | 55.933  | 55.279  | 23.751 (2.3x)   | 23.785 (2.4x)   | 23.768 (2.3x)   |
| 1e6 rows - arrowsqlbcp           | 54.733  | 55.558  | 55.145  | 8.307 (6.6x)    | 8.401 (6.6x)    | 8.354 (6.6x)    |
| 3e6 rows - fast_executemany=True | 253.726 | 253.917 | 253.821 | 255.076 (-1.0x) | 255.172 (-1.0x) | 255.124 (-1.0x) |
| 3e6 rows - bcpandas              | 255.342 | 259.436 | 257.389 | 69.842 (3.7x)   | 70.005 (3.7x)   | 69.923 (3.7x)   |
| 3e6 rows - arrowsqlbcp           | 254.980 | 258.550 | 256.765 | 24.767 (10.3x)  | 24.801 (10.4x)  | 24.784 (10.4x)  |

### Ubuntu (WSL2) (local db)

tbc

Benchmarks for the typical case of a remote DB still need to be added.

## Limitations

`bulkcopy_from_pandas()` will establish its own database connection to load the data, reusing existing connections and transactions are not supported.

Only basic MacOS testing has been done.
