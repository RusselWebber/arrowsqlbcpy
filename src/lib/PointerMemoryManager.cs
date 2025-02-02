﻿using System.Buffers;

namespace ArrowSqlBulkCopyNet;

internal sealed unsafe class PointerMemoryManager<T> : MemoryManager<T> where T : struct
{
    private readonly int _length;
    private readonly void* _pointer;

    internal PointerMemoryManager(void* pointer, int length)
    {
        _pointer = pointer;
        _length = length;
    }

    protected override void Dispose(bool disposing)
    {
    }

    public override Span<T> GetSpan()
    {
        return new Span<T>(_pointer, _length);
    }

    public override MemoryHandle Pin(int elementIndex = 0)
    {
        throw new NotSupportedException();
    }

    public override void Unpin()
    {
    }
}