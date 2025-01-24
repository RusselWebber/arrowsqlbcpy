using System.Diagnostics;
using System.Runtime.InteropServices;
using Apache.Arrow.Ipc;
using Microsoft.Data.Analysis;
using Microsoft.Data.SqlClient;

namespace ArrowSqlBulkCopyNet;

public static class ArrowSqlBulkCopyNet
{
    /// <summary>
    ///     Write Apache Arrow data to a SQL Server table using SqlBulkCopy
    ///     This function is intended for use by non .Net languages such as Python
    ///     .Net languages should simply use WriterAsync
    /// </summary>
    /// <param name="pBuffer">Pointer to an Apache Arrow Buffer</param>
    /// <param name="bufferLength">Length of the buffer</param>
    /// <param name="pConnectionString">Pointer to the SQL Server connection string</param>
    /// <param name="pDestinationTableName">Pointer to the destination table name</param>
    /// <param name="bulkCopyTimeout">Copy timeout in seconds</param>
    /// <param name="pException">Pointer to a string to store any exception messages</param>
    /// <param name="maxExceptionLength">
    ///     The maximum length of the exception message. This must be less than or equal to the length of the string pointed to
    ///     by pException.
    /// </param>
    /// <returns>0 on success, non-zero on failure. Failures will have an error message and traceback in pException</returns>
    /// <exception cref="ArgumentException"></exception>
    [UnmanagedCallersOnly(EntryPoint = "write")]
    public static int Write(IntPtr pBuffer, int bufferLength, IntPtr pConnectionString,
        IntPtr pDestinationTableName, int bulkCopyTimeout, IntPtr pException, int maxExceptionLength)
    {
        try
        {
            if (pBuffer == IntPtr.Zero)
                throw new ArgumentException("Value cannot be null or empty.", nameof(pBuffer));
            if (bufferLength == 0)
                throw new ArgumentException("Value cannot be null or empty.", nameof(bufferLength));
            var connectionString = Marshal.PtrToStringUTF8(pConnectionString);
            if (string.IsNullOrEmpty(connectionString))
                throw new ArgumentException("Value cannot be null or empty.", nameof(connectionString));
            var destinationTableName = Marshal.PtrToStringUTF8(pDestinationTableName);
            if (string.IsNullOrEmpty(destinationTableName))
                throw new ArgumentException(nameof(destinationTableName), nameof(destinationTableName));
            PointerMemoryManager<byte> buffer;
            unsafe
            {
                buffer = new PointerMemoryManager<byte>((void*) pBuffer, bufferLength);
            }

            Writer(buffer.Memory, connectionString, destinationTableName, bulkCopyTimeout);
        }
        catch (Exception e)
        {
            if (pException == IntPtr.Zero || maxExceptionLength <= 0) return -1;
            var error = $"{e.Message}\n{e.StackTrace}".ToCharArray();
            Marshal.Copy(error, 0, pException, int.Min(error.Length, maxExceptionLength));
            return -1;
        }

        return 0;
    }

    /// <summary>
    ///     Write Apache Arrow data to a SQL Server table using SqlBulkCopy
    /// </summary>
    /// <param name="buffer">The Arrow Buffer</param>
    /// <param name="connectionString">SQL Server connection string</param>
    /// <param name="destinationTableName">DB Table</param>
    /// <param name="bulkCopyTimeout">Timeout in seconds</param>
    /// <param name="cancellationToken"></param>
    public static void Writer(ReadOnlyMemory<byte> buffer, string connectionString,
        string destinationTableName, int bulkCopyTimeout = 0,
        CancellationToken cancellationToken = default)
    {
        var t = Task.Run(async () => await WriterAsync(buffer, connectionString,
                destinationTableName, bulkCopyTimeout, cancellationToken),
            cancellationToken);
        t.GetAwaiter().GetResult();
    }


    /// <summary>
    ///     Async write Apache Arrow data to a SQL Server table using SqlBulkCopy
    /// </summary>
    /// <param name="buffer">The Arrow Buffer</param>
    /// <param name="connectionString">SQL Server connection string</param>
    /// <param name="destinationTableName">DB Table</param>
    /// <param name="bulkCopyTimeout">Timeout in seconds</param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentException"></exception>
    public static async Task WriterAsync(ReadOnlyMemory<byte> buffer, string connectionString,
        string destinationTableName, int bulkCopyTimeout = 0,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(buffer);
        if (buffer.Length == 0) throw new ArgumentException("buffer is empty", nameof(buffer));
        if (string.IsNullOrEmpty(connectionString))
            throw new ArgumentException("Value cannot be null or empty.", nameof(connectionString));
        if (string.IsNullOrEmpty(destinationTableName))
            throw new ArgumentException("Value cannot be null or empty.", nameof(destinationTableName));

        await using var destinationConnection =
            new SqlConnection(connectionString);
        await destinationConnection.OpenAsync(cancellationToken);

        using var bulkCopy =
            new SqlBulkCopy(destinationConnection);
        bulkCopy.DestinationTableName = destinationTableName;
        bulkCopy.BulkCopyTimeout = bulkCopyTimeout;

        using var reader = new ArrowStreamReader(buffer);
        var recordBatch = await reader.ReadNextRecordBatchAsync(cancellationToken);
        Debug.WriteLine($"Read record batch, columns count: {recordBatch.ColumnCount}, length:{recordBatch.Length}");
        var df = DataFrame.FromArrowRecordBatch(recordBatch);
        var table = df.ToTable();
        await bulkCopy.WriteToServerAsync(table, cancellationToken);
        Debug.WriteLine("Bulk copy to server successful");
    }
}