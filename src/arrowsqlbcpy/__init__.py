import os
import platform
import pyarrow as pa
import pandas as pd
import ctypes
from ctypes import c_int, c_wchar_p, create_unicode_buffer, c_char_p

is_win = platform.system() == "Windows"
is_mac = platform.system() == "Darwin"

libpath = os.path.join(os.path.dirname(__file__), "lib")
if is_win:
    libname = "ArrowSqlBulkCopyNet.dll"
    sqllibname = "Microsoft.Data.SqlClient.SNI.dll"
elif is_mac:
    libname = "ArrowSqlBulkCopyNet.dylib"
    sqllibname = None
else:
    libname = "ArrowSqlBulkCopyNet.so"
    sqllibname = None

func_name = "write"
error_size = 1000

# Check for required dlls
if is_win:
    if not os.path.exists(os.path.join(libpath, sqllibname)):
        raise RuntimeError(f"Missing {sqllibname} in {libpath}")
    sqllib = ctypes.windll.LoadLibrary(os.path.join(libpath, sqllibname))

if is_win:
    lib = ctypes.windll.LoadLibrary(os.path.join(libpath, libname))
else:
    lib = ctypes.cdll.LoadLibrary(os.path.join(libpath, libname))
if not hasattr(lib, func_name):
    raise RuntimeError(f"Missing {func_name} in {libname}")

# Setup the dll function using ctypes
func_handle = getattr(lib, func_name)
func_handle.argtypes = [c_char_p, c_int, c_char_p, c_char_p, c_int, c_wchar_p, c_int]


class PyArrowSqlBulkCopyException(Exception):
    pass


def bulkcopy_from_pandas(
    df: pd.DataFrame,
    connection_string: str,
    tablename: str,
    max_chunksize: int = None,
    timeout: int = 0,
) -> None:
    ctypes_connection_string = c_char_p(connection_string.encode())
    ctypes_tablename = c_char_p(tablename.encode())
    ctypes_exception = create_unicode_buffer(init=" " * error_size, size=error_size)

    # Convert from pandas to Arrow
    table = pa.Table.from_pandas(df)
    # Getting batches is zero copy
    for batch in table.to_batches(max_chunksize):
        sink = pa.BufferOutputStream()
        with pa.ipc.new_stream(sink, table.schema) as writer:
            writer.write_batch(batch)

        buf = sink.getvalue().to_pybytes()

        # Call the dll function that will
        # write the df to SQL Server using SqlBulkCopy
        res = func_handle(
            buf,
            len(buf),
            ctypes_connection_string,
            ctypes_tablename,
            timeout,
            ctypes_exception,
            error_size,
        )
        if res != 0:
            raise PyArrowSqlBulkCopyException(ctypes_exception.value)
