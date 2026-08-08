// Dispatch to handlers via vtable. v3=(u8)type_code=handler index. Handler from TLS[TlsIndex+4464+8*v3] or global qword_143A0CD58+8*v3. Calls handler vtable+120(handler_obj, entry_struct, type_code, data_ptr).
__int64 __fastcall WadDispatch(__int64 a1, unsigned int a2, __int64 a3)
{
  __int64 v3; // rdi
  __int64 v8; // rcx

  v3 = (unsigned __int8)a2;
  if ( !(unsigned __int8)sub_140392650((unsigned __int8)a2) )
    return 0;
  v8 = *(_QWORD *)(*((_QWORD *)NtCurrentTeb()->ThreadLocalStoragePointer + (unsigned int)TlsIndex) + 4464LL + 8 * v3);
  if ( !v8 )
  {
    if ( qword_143A0CD58 )
      v8 = *(_QWORD *)(8 * v3 + qword_143A0CD58);
  }
  return (*(__int64 (__fastcall **)(__int64, __int64, _QWORD, __int64))(*(_QWORD *)v8 + 120LL))(v8, a1, a2, a3);
}
