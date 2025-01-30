![GitHub Latest Tag](https://badgen.net/github/tag/RusselWebber/arrowsqlbcpy) ![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/RusselWebber/arrowsqlbcpy/ci.yml) ![PyPI Python Versions](https://img.shields.io/pypi/pyversions/arrowsqlbcpy)

# arrowsqlbcpy

A tiny library that uses .Net SqlBulkCopy to enable fast data loading to Microsoft SQL Server. Apache Arrow is used to serialise data between Python and the native DLL. .Net Native Library AOT compilation is used to generate the native DLL.

This library is _much_ faster than any other Python solution, including bcpy, pyodbc and pymssql.

## Installation

Binary wheels are available from PyPi and can be installed using your preferred package manager:

> pip install arrowsqlbcpy

or

> uv add arrowsqlbcpy

## Requirements

Wheels are available for the latest versions of Windows 64 bit, MacOS ARM 64bit and Ubuntu 64 bit.

Wheels are available for Python 3.9-3.13.

## Usage

Connection strings for .Net are documented [here](https://www.connectionstrings.com/microsoft-data-sqlclient/)

````python

import pandas as pd
from arrowsqlbcpy import bulkcopy_from_pandas

# Create a connection string
cn = r"Server=myServerAddress;Database=myDataBase;Trusted_Connection=True;"
# The table to load into must exist and have the same column names and types as the pandas df
tablename = "test"

df = pd.DataFrame({"a":[1]*10000, "b":[2]*10000, "c":[3]*10000})

bulkcopy_from_pandas(df, cn, tablename)

```

When testing it can be useful to have pandas create the table for you, see  tests/test_load.py for an example.



## Benchmarks

### Windows

### Ubuntu (WSL2)


## Limitations

bulkcopy_from_pandas() will establish its own database connection to load the data, using existing connections and transactions are not not supported.

Only basic MacOS testing has been done.
````
