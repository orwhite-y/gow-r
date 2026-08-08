char __fastcall sub_1405E5700(__int64 a1, __int64 a2, __int64 a3, __int64 a4)
{
  unsigned int v6; // ebx
  int v8; // ecx
  int v9; // ebx
  __int64 v11; // rdx
  char v12; // al
  __int64 v13; // rax
  int v14; // r9d
  unsigned int v15; // esi
  unsigned __int8 n2; // r8
  int v17; // ecx
  unsigned int v18; // ecx
  __int64 v19; // rcx
  signed int v20; // edx
  int v22; // eax
  int v23; // r8d
  __int64 v24; // rcx
  __int64 v25; // rdx
  int v27; // eax
  __int64 v28; // rcx
  __int64 v29; // rdx
  int v30; // ebx
  int v32; // r8d
  int v33; // r10d
  __int64 v34; // r9
  __int64 v35; // rdx
  __int64 v37; // r8
  __int64 v38; // r15
  __int64 v39; // r8
  __int64 v40; // r15
  unsigned int v41; // eax
  unsigned __int8 *v42; // r8
  __int64 v43; // r9
  int n4; // edx
  _DWORD *v45; // rcx
  int v46; // eax
  unsigned __int8 n0xF; // bl
  unsigned __int8 v48; // si
  int v49; // r8d
  __int64 v50; // rcx
  __int64 v51; // rdx
  int v52; // eax
  char v53; // al
  _OWORD v55[3]; // [rsp+20h] [rbp-88h] BYREF
  __int64 v56; // [rsp+50h] [rbp-58h]
  int v57; // [rsp+58h] [rbp-50h]

  v6 = 0xFC3333u >> (4 * *(_BYTE *)(a1 + 131)); /*0x1405e5733*/
  v8 = *(unsigned __int8 *)(a1 + 129); /*0x1405e5738*/
  v9 = *(_DWORD *)(a1 + 72) * (v6 & 0xF); /*0x1405e5742*/
  if ( v8 ) /*0x1405e574b*/
    v11 = a2 + *(unsigned int *)(a1 + 48); /*0x1405e5750*/
  else
    v11 = 0; /*0x1405e5755*/
  *(_QWORD *)a3 = v11; /*0x1405e5759*/
  *(_DWORD *)(a3 + 12) = v8; /*0x1405e575f*/
  *(_DWORD *)(a3 + 17) = 1073742336; /*0x1405e5763*/
  *(_BYTE *)(a3 + 16) = 0; /*0x1405e576b*/
  *(_DWORD *)(a3 + 8) = v8 * v9; /*0x1405e5770*/
  if ( a4 ) /*0x1405e5777*/
    v12 = sub_1403A00A0(a4, a3); /*0x1405e577f*/
  else
    v12 = sub_140EA2240(a3, v11, v8 * v9); /*0x1405e578c*/
  if ( !v12 ) /*0x1405e5798*/
    return 0; /*0x1405e5798*/
  v13 = *(_QWORD *)(a3 + 48); /*0x1405e579e*/
  if ( v13 )
  {
    v14 = *(_DWORD *)(a1 + 72); /*0x1405e57b7*/
    v15 = v14 * ((0xFC3333u >> (4 * *(_BYTE *)(a1 + 131))) & 0xF); /*0x1405e57c5*/
    if ( ((0x9600u >> (4 * *(_BYTE *)(a1 + 131))) & 0xF) != 0 && *(_BYTE *)(a1 + 129) == 2 ) /*0x1405e57d5*/
    {
      n2 = 2; /*0x1405e57d9*/
      v17 = v15 & 1; /*0x1405e57dc*/
    }
    else
    {
      n2 = *(_BYTE *)(a1 + 129); /*0x1405e57e1*/
      v17 = 0; /*0x1405e57e9*/
    }
    v18 = v15 + v17; /*0x1405e57eb*/
    v19 = n2 ? a2 + *(_DWORD *)(a1 + 48) + n2 * v18 : 0LL;
    v20 = n2 * v14 * ((0x9600u >> (4 * *(_BYTE *)(a1 + 131))) & 0xF); /*0x1405e5808*/
    *(_QWORD *)v13 = v19; /*0x1405e580c*/
    *(_DWORD *)(v13 + 12) = n2; /*0x1405e580f*/
    *(_DWORD *)(v13 + 17) = 1073742080; /*0x1405e5813*/
    *(_BYTE *)(v13 + 16) = 0; /*0x1405e581a*/
    *(_DWORD *)(v13 + 8) = v20; /*0x1405e581e*/
    if ( !(a4 ? sub_1403A00A0(a4, v13) : (unsigned __int8)sub_140EA2240(v13, v19, v20)) )
      return 0; /*0x1405e5843*/
  }
  v22 = *(unsigned __int16 *)(a1 + 82); /*0x1405e5849*/
  if ( (_WORD)v22 )
  {
    v23 = *(unsigned __int8 *)(a1 + 88); /*0x1405e5856*/
    v24 = *(_QWORD *)(a3 + 56); /*0x1405e585e*/
    v25 = *(_BYTE *)(a1 + 88) ? a2 + *(unsigned int *)(a1 + 52) : 0LL;
    *(_QWORD *)v24 = v25; /*0x1405e5874*/
    *(_DWORD *)(v24 + 12) = v23; /*0x1405e587b*/
    *(_DWORD *)(v24 + 17) = 1073742080; /*0x1405e587f*/
    *(_BYTE *)(v24 + 16) = 0; /*0x1405e5886*/
    *(_DWORD *)(v24 + 8) = v22 * v23; /*0x1405e588a*/
    if ( !(a4 ? sub_1403A00A0(a4, v24) : (unsigned __int8)sub_140EA2240(v24, v25, (unsigned int)(v22 * v23))) )
      return 0; /*0x1405e58a9*/
    v27 = *(unsigned __int8 *)(a1 + 129); /*0x1405e58b3*/
    v28 = *(_QWORD *)(a3 + 56) + 40LL; /*0x1405e58ba*/
    v29 = *(_BYTE *)(a1 + 129) ? a2 + *(unsigned int *)(a1 + 48) : 0LL;
    v30 = v27 * v9; /*0x1405e58cc*/
    *(_QWORD *)v28 = v29; /*0x1405e58cf*/
    *(_DWORD *)(v28 + 12) = v27; /*0x1405e58d2*/
    *(_DWORD *)(v28 + 17) = 1073742080; /*0x1405e58d5*/
    *(_BYTE *)(v28 + 16) = 0; /*0x1405e58dc*/
    *(_DWORD *)(v28 + 8) = v30; /*0x1405e58e0*/
    if ( !(a4 ? sub_1403A00A0(a4, v28) : (unsigned __int8)sub_140EA2240(v28, v29, v30)) )
      return 0; /*0x1405e58ff*/
    v32 = *(unsigned __int8 *)(a1 + 89); /*0x1405e5905*/
    v33 = *(unsigned __int16 *)(a1 + 82); /*0x1405e590a*/
    v34 = *(_QWORD *)(a3 + 56); /*0x1405e590f*/
    v35 = *(_BYTE *)(a1 + 89)
        ? a2 + ((v33 * *(unsigned __int8 *)(a1 + 88) + *(_DWORD *)(a1 + 52) + 15) & 0xFFFFFFF0)
        : 0LL;
    *(_QWORD *)(v34 + 80) = v35; /*0x1405e593a*/
    *(_DWORD *)(v34 + 92) = v32; /*0x1405e5942*/
    *(_DWORD *)(v34 + 97) = 1073743360; /*0x1405e5946*/
    *(_BYTE *)(v34 + 96) = 0; /*0x1405e594e*/
    *(_DWORD *)(v34 + 88) = v33 * v32; /*0x1405e5953*/
    if ( !(a4 ? sub_1403A00A0(a4, v34 + 80) : (unsigned __int8)sub_140EA2240(v34 + 80, v35, (unsigned int)(v33 * v32))) )
      return 0; /*0x1405e5a8c*/
  }
  v37 = *(unsigned int *)(a1 + 96); /*0x1405e597e*/
  v38 = *(unsigned int *)(a1 + 100); /*0x1405e5984*/
  v56 = 0; /*0x1405e598b*/
  v39 = v37 + 4; /*0x1405e5990*/
  v57 = 0; /*0x1405e5994*/
  v40 = a1 + v38; /*0x1405e5998*/
  v41 = *(unsigned __int8 *)(a1 + 132); /*0x1405e599b*/
  memset(v55, 0, sizeof(v55)); /*0x1405e59a2*/
  if ( (_BYTE)v41 ) /*0x1405e59b3*/
  {
    v42 = (unsigned __int8 *)(a1 + v39); /*0x1405e59b5*/
    v43 = v41; /*0x1405e59bf*/
    do /*0x1405e5a0d*/
    {
      n4 = 0; /*0x1405e59c7*/
      switch ( *(v42 - 3) ) /*0x1405e59d9*/
      {
        case 0u: /*0x1405e59d9*/
        case 2u: /*0x1405e59d9*/
        case 3u: /*0x1405e59d9*/
          n4 = 4; /*0x1405e59db*/
          break; /*0x1405e59e0*/
        case 1u: /*0x1405e59d9*/
        case 4u: /*0x1405e59d9*/
        case 5u: /*0x1405e59d9*/
        case 6u: /*0x1405e59d9*/
        case 7u: /*0x1405e59d9*/
          n4 = 2; /*0x1405e59e2*/
          break; /*0x1405e59e7*/
        case 8u: /*0x1405e59d9*/
        case 9u: /*0x1405e59d9*/
        case 0xAu: /*0x1405e59d9*/
        case 0xBu: /*0x1405e59d9*/
          n4 = 1; /*0x1405e59e9*/
          break; /*0x1405e59e9*/
        default:
          break;
      }
      v45 = (_DWORD *)v55 + *v42; /*0x1405e59ee*/
      v46 = n4 * *(v42 - 2); /*0x1405e5a00*/
      v42 += 8; /*0x1405e5a03*/
      *v45 += v46; /*0x1405e5a07*/
      --v43; /*0x1405e5a09*/
    }
    while ( v43 ); /*0x1405e5a0d*/
  }
  n0xF = 0; /*0x1405e5a0f*/
  v48 = 0; /*0x1405e5a11*/
  do /*0x1405e5a86*/
  {
    v49 = *((_DWORD *)v55 + n0xF); /*0x1405e5a23*/
    if ( v49 ) /*0x1405e5a2b*/
    {
      v50 = *(_QWORD *)(a3 + 40) + 40LL * v48; /*0x1405e5a3d*/
      v51 = a2 + *(unsigned int *)(v40 + 4LL * v48); /*0x1405e5a41*/
      v52 = *(_DWORD *)(a1 + 68) * v49; /*0x1405e5a47*/
      *(_QWORD *)v50 = v51; /*0x1405e5a4b*/
      *(_DWORD *)(v50 + 12) = v49; /*0x1405e5a4e*/
      *(_DWORD *)(v50 + 17) = 1073742080; /*0x1405e5a52*/
      *(_BYTE *)(v50 + 16) = 0; /*0x1405e5a59*/
      *(_DWORD *)(v50 + 8) = v52; /*0x1405e5a5d*/
      if ( a4 ) /*0x1405e5a63*/
        v53 = sub_1403A00A0(a4, v50); /*0x1405e5a6b*/
      else
        v53 = sub_140EA2240(v50, v51, v52); /*0x1405e5a75*/
      if ( !v53 ) /*0x1405e5a7c*/
        return 0; /*0x1405e5a7c*/
      ++v48; /*0x1405e5a7e*/
    }
    ++n0xF; /*0x1405e5a81*/
  }
  while ( n0xF < 0xFu ); /*0x1405e5a86*/
  return 1; /*0x1405e5a8e*/
}
