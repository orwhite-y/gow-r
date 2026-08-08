// VERIFIED(IDA): Per-entry processor. handler=WadTypeHandlerLookup(entry[0]). Calls handler(entry) via vtable. entry+0=u16 type,entry+2=u16 flags(0x400),entry+0x70=byte(0x7F),entry+0x6F=subtype. type19->sub_1405AF720,type21->skip,type33->clear. v6+=72(u16*)=144B per entry.
char __fastcall WadBatchProcessInner(__int64 a1, int n64, unsigned __int64 n64_2)
{
  int n64_1; // ebp
  __int64 v5; // r15
  unsigned __int16 *v6; // rbx
  __int64 TlsIndex; // r12
  unsigned __int16 n33; // di
  __int64 v9; // rdx
  __int64 v10; // r8
  __int64 v11; // r9
  char n2; // al
  char v13; // al
  char v14; // cl
  char v15; // al
  void (__fastcall *v16)(unsigned __int16 *); // rax
  char result; // al

  n64_1 = n64;
  v5 = a1;
  if ( n64 < n64_2 )
  {
    v6 = (unsigned __int16 *)(*(_QWORD *)(a1 + 72) + 144LL * n64);
    TlsIndex = (unsigned int)::TlsIndex;
    do
    {
      n33 = *v6;
      if ( (unsigned __int8)sub_1403B40E0(v6) )
      {
        n2 = v6[56] & 0x7F;
        if ( n2 == 1 || n2 == 2 && (unsigned __int8)sub_1403B2820() )
        {
          if ( !*(_BYTE *)(*((_QWORD *)NtCurrentTeb()->ThreadLocalStoragePointer + TlsIndex) + 5412LL) )
            _dyn_tls_on_demand_init(5412, v9, v10, v11);
          *(_BYTE *)(*((_QWORD *)NtCurrentTeb()->ThreadLocalStoragePointer + TlsIndex) + 4432LL) = 1;
        }
      }
      v13 = sub_1403B3930(n33);
      v14 = byte_143A1EE1E;
      if ( v13 )
        v14 = 1;
      byte_143A1EE1E = v14;
      if ( n33 == 19 )
      {
        sub_1405AF720(v6);
        qword_143A1EE38 = sub_140391420();
      }
      else if ( n33 != 21 )
      {
        v15 = v14;
        if ( n33 == 33 )
          v15 = 0;
        byte_143A1EE1E = v15;
        if ( ((v6[1] & 0x400) == 0 || !(unsigned __int8)sub_1403B2820())
          && (unsigned __int8)(*((_BYTE *)v6 + 111) - 5) > 2u )
        {
          v16 = (void (__fastcall *)(unsigned __int16 *))WadTypeHandlerLookup(*v6);
          if ( v16 )
          {
            if ( !byte_143A1EE1E )
              v16(v6);
          }
        }
      }
      if ( (unsigned __int8)sub_1403B40B0(v6) )
      {
        while ( (unsigned __int8)sub_1403B4040(v6) )
          ;
      }
      ++n64_1;
      v6 += 72;
    }
    while ( n64_1 < n64_2 );
    v5 = a1;
  }
  result = 1;
  if ( n64_2 == *(_DWORD *)(v5 + 16) )
    n10 = 4;
  return result;
}
