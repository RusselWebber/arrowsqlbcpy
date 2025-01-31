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

The benchmarks have a baseline of using pandas `to_sql()` and SQLAlchemy with pyodbc and pymssql. This is a common solution for loading pandas dataframes into SQL Server. A batch size of 10 000 rows was used in the benchmarks.

The benchmarks show the time taken to load using various alternative strategies:

| Label                 | Description                                                                                                                                                                                                                    |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| fast_executemany=True | Use pandas `to_sql()`, SQLAlchemy, pyodbc, pymssql with the fast_executemany=True option as discussed [here](https://stackoverflow.com/questions/48006551/speeding-up-pandas-dataframe-to-sql-with-fast-executemany-of-pyodbc) |
| bcpandas              | Use the [bcpandas](https://github.com/yehoshuadimarsky/bcpandas) package to load the dataframes. The package writes temp files and spawns bcp processes to load them                                                           |
| arrowsqlbcpy          | This package using .Net SqlBulkCopy                                                                                                                                                                                            |

The richbench tables show the min, max and mean time in seconds for the baseline in the left three columns; then the min, max, mean time in seconds for the alternative strategy.

For example this row:

| Benchmark                          | Min | Max | Mean | Min (+)  | Max (+)  | Mean (+) |
| ---------------------------------- | --- | --- | ---- | -------- | -------- | -------- |
| 1 000 rows - fast_executemany=True | 1.0 | 1.0 | 1.0  | 0.5 (2x) | 0.5 (2x) | 0.5 (2x) |

should be interpreted as: the strategy of setting fast_executemany=True resulted in a 2x speedup over the baseline when loading 1000 rows, so fast_executemany=True reduced the average time in seconds to load 1000 rows from 1.0 to 0.5, a 2x speedup.

### Windows 11 (local db)

**Summary results**

| Label                 | # rows    | Avg Speedup | Avg Time (s) |
| --------------------- | --------- | ----------- | ------------ |
| **arrowsqlbcpy**      | 1 000     | **-1.9x**   | 0.106        |
| **arrowsqlbcpy**      | 10 000    | **4.9x**    | 0.101        |
| **arrowsqlbcpy**      | 100 000   | **4.9x**    | 0.933        |
| **arrowsqlbcpy**      | 1 000 000 | **5.3x**    | 8.864        |
| **arrowsqlbcpy**      | 3 000 000 | **7.6x**    | 26.048       |
| bcpandas              | 1 000     | -3.6x       | 0.156        |
| bcpandas              | 10 000    | 1.5x        | 0.336        |
| bcpandas              | 100 000   | 1.8x        | 2.567        |
| bcpandas              | 1 000 000 | 1.9x        | 24.627       |
| bcpandas              | 3 000 000 | 2.7x        | 72.353       |
| fast_executemany=True | 1 000     | 2.4x        | 0.035        |
| fast_executemany=True | 10 000    | 2.3x        | 0.235        |
| fast_executemany=True | 100 000   | 2.3x        | 2.246        |
| fast_executemany=True | 1 000 000 | 2.1x        | 22.044       |
| fast_executemany=True | 3 000 000 | 3.0x        | 65.344       |

**Detailed richbench results**

| Benchmark                              | Min     | Max     | Mean    | Min (+)       | Max (+)       | Mean (+)      |
| -------------------------------------- | ------- | ------- | ------- | ------------- | ------------- | ------------- |
| 1 000 - arrowsqlbcp                    | 0.053   | 0.056   | 0.055   | 0.015 (3.6x)  | 0.198 (-3.5x) | 0.106 (-1.9x) |
| 10 000 rows - arrowsqlbcp              | 0.489   | 0.502   | 0.495   | 0.099 (4.9x)  | 0.103 (4.9x)  | 0.101 (4.9x)  |
| 100 000 rows - arrowsqlbcp             | 4.587   | 4.616   | 4.601   | 0.922 (5.0x)  | 0.944 (4.9x)  | 0.933 (4.9x)  |
| 1 000 000 rows - arrowsqlbcp           | 46.558  | 46.738  | 46.648  | 8.842 (5.3x)  | 8.886 (5.3x)  | 8.864 (5.3x)  |
| 3 000 000 rows - arrowsqlbcp           | 198.464 | 198.676 | 198.570 | 26.016 (7.6x) | 26.079 (7.6x) | 26.048 (7.6x) |
| 1 000 - bcpandas                       | 0.051   | 0.052   | 0.052   | 0.121 (-2.4x) | 0.190 (-3.6x) | 0.156 (-3.0x) |
| 10 000 rows - bcpandas                 | 0.499   | 0.500   | 0.500   | 0.333 (1.5x)  | 0.339 (1.5x)  | 0.336 (1.5x)  |
| 100 000 rows - bcpandas                | 4.543   | 4.547   | 4.545   | 2.565 (1.8x)  | 2.570 (1.8x)  | 2.567 (1.8x)  |
| 1 000 000 rows - bcpandas              | 45.298  | 46.443  | 45.871  | 24.581 (1.8x) | 24.674 (1.9x) | 24.627 (1.9x) |
| 3 000 000 rows - bcpandas              | 197.292 | 197.699 | 197.496 | 72.301 (2.7x) | 72.405 (2.7x) | 72.353 (2.7x) |
| 1 000 - fast_executemany=True          | 0.052   | 0.116   | 0.084   | 0.030 (1.7x)  | 0.041 (2.9x)  | 0.035 (2.4x)  |
| 10 000 rows - fast_executemany=True    | 0.513   | 0.550   | 0.531   | 0.233 (2.2x)  | 0.237 (2.3x)  | 0.235 (2.3x)  |
| 100 000 rows - fast_executemany=True   | 5.018   | 5.374   | 5.196   | 2.239 (2.2x)  | 2.253 (2.4x)  | 2.246 (2.3x)  |
| 1 000 000 rows - fast_executemany=True | 45.470  | 45.582  | 45.526  | 22.036 (2.1x) | 22.051 (2.1x) | 22.044 (2.1x) |
| 3 000 000 rows - fast_executemany=True | 194.152 | 194.523 | 194.337 | 65.153 (3.0x) | 65.534 (3.0x) | 65.344 (3.0x) |

### Ubuntu (WSL2) (local db in docker container)

**Summary results**

| Label                 | # rows    | Avg Speedup | Avg Time (s) |
| --------------------- | --------- | ----------- | ------------ |
| **arrowsqlbcpy**      | 1 000     | **-2.2x**   | 0.154        |
| **arrowsqlbcpy**      | 10 000    | **4.2x**    | 0.120        |
| **arrowsqlbcpy**      | 100 000   | **4.7x**    | 1.070        |
| **arrowsqlbcpy**      | 1 000 000 | **4.7x**    | 10.572       |
| **arrowsqlbcpy**      | 3 000 000 | **6.8x**    | 30.673       |
| bcpandas              | 1 000     | -2.4x       | 0.158        |
| bcpandas              | 10 000    | 1.2x        | 0.438        |
| bcpandas              | 100 000   | 1.5x        | 3.383        |
| bcpandas              | 1 000 000 | 1.5x        | 32.774       |
| bcpandas              | 3 000 000 | 2.2x        | 95.200       |
| fast_executemany=True | 1 000     | 1.6x        | 0.059        |
| fast_executemany=True | 10 000    | 1.7x        | 0.323        |
| fast_executemany=True | 100 000   | 1.6x        | 3.039        |
| fast_executemany=True | 1 000 000 | 1.7x        | 29.810       |
| fast_executemany=True | 3 000 000 | 2.4x        | 87.419       |

**Detailed richbench results**

| Benchmark                              | Min     | Max     | Mean    | Min (+)       | Max (+)       | Mean (+)      |
| -------------------------------------- | ------- | ------- | ------- | ------------- | ------------- | ------------- |
| 1 000 - arrowsqlbcp                    | 0.069   | 0.071   | 0.070   | 0.028 (2.4x)  | 0.280 (-3.9x) | 0.154 (-2.2x) |
| 10 000 rows - arrowsqlbcp              | 0.503   | 0.510   | 0.506   | 0.115 (4.4x)  | 0.126 (4.0x)  | 0.120 (4.2x)  |
| 100 000 rows - arrowsqlbcp             | 5.062   | 5.085   | 5.074   | 1.064 (4.8x)  | 1.076 (4.7x)  | 1.070 (4.7x)  |
| 1 000 000 rows - arrowsqlbcp           | 49.746  | 50.433  | 50.089  | 10.566 (4.7x) | 10.578 (4.8x) | 10.572 (4.7x) |
| 3 000 000 rows - arrowsqlbcp           | 208.669 | 208.953 | 208.811 | 30.364 (6.9x) | 30.982 (6.7x) | 30.673 (6.8x) |
| 1 000 - bcpandas                       | 0.066   | 0.068   | 0.067   | 0.149 (-2.2x) | 0.167 (-2.5x) | 0.158 (-2.4x) |
| 10 000 rows - bcpandas                 | 0.500   | 0.508   | 0.504   | 0.431 (1.2x)  | 0.444 (1.1x)  | 0.438 (1.2x)  |
| 100 000 rows - bcpandas                | 5.016   | 5.028   | 5.022   | 3.369 (1.5x)  | 3.397 (1.5x)  | 3.383 (1.5x)  |
| 1 000 000 rows - bcpandas              | 49.771  | 50.535  | 50.153  | 32.603 (1.5x) | 32.945 (1.5x) | 32.774 (1.5x) |
| 3 000 000 rows - bcpandas              | 208.104 | 208.350 | 208.227 | 95.057 (2.2x) | 95.343 (2.2x) | 95.200 (2.2x) |
| 1 000 - fast_executemany=True          | 0.068   | 0.116   | 0.092   | 0.049 (1.4x)  | 0.069 (1.7x)  | 0.059 (1.6x)  |
| 10 000 rows - fast_executemany=True    | 0.514   | 0.557   | 0.535   | 0.322 (1.6x)  | 0.324 (1.7x)  | 0.323 (1.7x)  |
| 100 000 rows - fast_executemany=True   | 4.934   | 4.961   | 4.948   | 3.023 (1.6x)  | 3.056 (1.6x)  | 3.039 (1.6x)  |
| 1 000 000 rows - fast_executemany=True | 49.298  | 50.658  | 49.978  | 29.783 (1.7x) | 29.836 (1.7x) | 29.810 (1.7x) |
| 3 000 000 rows - fast_executemany=True | 207.245 | 213.096 | 210.171 | 87.219 (2.4x) | 87.620 (2.4x) | 87.419 (2.4x) |

Benchmarks for the typical case of a remote DB still need to be added.

## Limitations

`bulkcopy_from_pandas()` will establish its own database connection to load the data, reusing existing connections and transactions are not supported.

Only basic MacOS testing has been done.
