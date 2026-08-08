// Mesh lodpack resolver: hash from *(*(mesh_obj+40)+0x68), calls sub_1403A1820 for lodpack lookup. Mesh data structure has hash at +0x68.
__int64 __fastcall sub_1405FA610(__int64 a1)
{
  __int64 v2; // rdi
  char v3; // r12
  unsigned __int64 v4; // rbx
  __int64 v5; // rcx
  unsigned __int64 v6; // rdx
  _QWORD *v7; // rax
  __int64 result; // rax
  __int64 v9; // r8
  __int64 *v10; // rsi
  __int64 v11; // rsi
  __int64 v12; // r8
  _OWORD *v13; // rax
  __int64 v14; // r15
  unsigned int ***v15; // rbp
  __int64 v16; // r13
  __int64 *v17; // rcx
  __int64 v18; // rcx
  _QWORD *v19; // rax
  _QWORD *v20; // r15
  __int64 v21; // rsi
  unsigned int **v22; // r9
  __int64 v23; // rdi
  __int64 v24; // rax
  bool v25; // zf
  unsigned __int64 v26; // rdx
  _QWORD *v27; // rcx
  __int64 v28; // [rsp+20h] [rbp-C8h]
  __int128 v29; // [rsp+30h] [rbp-B8h]
  __int128 v30; // [rsp+40h] [rbp-A8h]
  __int64 v31; // [rsp+50h] [rbp-98h] BYREF
  __int64 v32; // [rsp+58h] [rbp-90h]
  __int128 v33; // [rsp+60h] [rbp-88h] BYREF
  __int64 v34; // [rsp+70h] [rbp-78h] BYREF
  _BYTE v35[16]; // [rsp+80h] [rbp-68h] BYREF
  __int64 v36; // [rsp+F0h] [rbp+8h]
  __int64 v37; // [rsp+F8h] [rbp+10h]
  __int64 v38; // [rsp+100h] [rbp+18h]
  __int64 v39; // [rsp+108h] [rbp+20h] BYREF

  v2 = sub_1403A60C0(); /*0x1405fa62c*/
  v37 = v2; /*0x1405fa62f*/
  sub_1403A1100(v2, *(_QWORD *)a1); /*0x1405fa637*/
  v3 = 1; /*0x1405fa63f*/
  v4 = 0; /*0x1405fa642*/
  if ( (*(_BYTE *)(a1 + 48) & 1) == 0 ) /*0x1405fa649*/
  {
    v5 = *(_QWORD *)(a1 + 40); /*0x1405fa64b*/
    v3 = 0; /*0x1405fa64f*/
    v6 = v5 + 1; /*0x1405fa655*/
    if ( !v5 ) /*0x1405fa659*/
      v6 = 0; /*0x1405fa659*/
    if ( v6 ) /*0x1405fa660*/
    {
      v7 = *(_QWORD **)(a1 + 56); /*0x1405fa662*/
      do /*0x1405fa675*/
      {
        if ( *v7 ) /*0x1405fa666*/
          break; /*0x1405fa669*/
        ++v4; /*0x1405fa66b*/
        ++v7; /*0x1405fa66e*/
      }
      while ( v4 < v6 ); /*0x1405fa675*/
    }
  }
  result = *(_QWORD *)(a1 + 40); /*0x1405fa677*/
  v9 = result + 1; /*0x1405fa696*/
  if ( !result ) /*0x1405fa6a2*/
    v9 = 0; /*0x1405fa6a2*/
  v36 = v9; /*0x1405fa6ae*/
  while ( v4 != v9 || v3 ) /*0x1405fa6be*/
  {
    if ( v3 ) /*0x1405fa6c7*/
      v10 = (__int64 *)(a1 + 72); /*0x1405fa6c9*/
    else
      v10 = (__int64 *)(*(_QWORD *)(a1 + 64) + 8 * v4); /*0x1405fa6d3*/
    v11 = *v10; /*0x1405fa6d7*/
    v12 = *(_QWORD *)a1; /*0x1405fa6e2*/
    v39 = *(_QWORD *)(*(_QWORD *)(v11 + 40) + 104LL); /*0x1405fa6fe*/
    v13 = (_OWORD *)sub_1403A1820(v2, v35, v12, &v39, v28); /*0x1405fa709*/
    v14 = *(_QWORD *)(v11 + 32); /*0x1405fa70e*/
    v15 = (unsigned int ***)(v11 + 16); /*0x1405fa712*/
    v16 = *(_QWORD *)(v11 + 40); /*0x1405fa716*/
    v38 = v14; /*0x1405fa720*/
    *(_OWORD *)(v11 + 16) = *v13; /*0x1405fa72e*/
    sub_1405E4550(v14, v16, v11 + 16); /*0x1405fa732*/
    if ( *(_QWORD *)(v11 + 16) || *(_DWORD *)(v11 + 24) ) /*0x1405fa73b*/
    {
      DWORD2(v29) = *(_DWORD *)(v11 + 24); /*0x1405fa743*/
      *(_QWORD *)&v29 = *(_QWORD *)(v11 + 16); /*0x1405fa73e*/
      v33 = v29; /*0x1405fa76f*/
      sub_1405FB980(a1 + 88, &v34, &v33); /*0x1405fa779*/
      if ( v34 < 0 ) /*0x1405fa786*/
        goto LABEL_24; /*0x1405fa786*/
      v17 = (__int64 *)(*(_QWORD *)(a1 + 120) + 8 * v34); /*0x1405fa78c*/
    }
    else
    {
      if ( (*(_BYTE *)(a1 + 104) & 1) == 0 ) /*0x1405fa755*/
        goto LABEL_24; /*0x1405fa755*/
      v17 = (__int64 *)(a1 + 128); /*0x1405fa757*/
    }
    if ( v17 ) /*0x1405fa793*/
    {
      v18 = *v17; /*0x1405fa795*/
      v19 = *(_QWORD **)(v18 + 8); /*0x1405fa798*/
      *(_QWORD *)(v18 + 8) = v11; /*0x1405fa79c*/
      *(_QWORD *)(v11 + 8) = v19; /*0x1405fa7a0*/
      *(_QWORD *)v11 = v18; /*0x1405fa7a4*/
      *v19 = v11; /*0x1405fa7a7*/
      goto LABEL_33; /*0x1405fa7aa*/
    }
LABEL_24:
    v20 = (_QWORD *)sub_140366310(**(_QWORD **)(a1 + 16)); /*0x1405fa7af*/
    v20[1] = v11; /*0x1405fa7be*/
    *(_QWORD *)(v11 + 8) = v20; /*0x1405fa7c2*/
    *(_QWORD *)v11 = v20; /*0x1405fa7c6*/
    *v20 = v11; /*0x1405fa7c9*/
    *(_QWORD *)&v30 = *v15; /*0x1405fa7d3*/
    DWORD2(v30) = *(_DWORD *)(v11 + 24); /*0x1405fa7d8*/
    if ( *v15 || *(_DWORD *)(v11 + 24) ) /*0x1405fa7d0*/
    {
      v33 = v30; /*0x1405fa802*/
      sub_1405FB980(a1 + 88, &v31, &v33); /*0x1405fa80c*/
      v21 = v31; /*0x1405fa811*/
      if ( v31 < 0 ) /*0x1405fa819*/
      {
        v21 = v32; /*0x1405fa81b*/
        if ( v32 < 0 ) /*0x1405fa823*/
          sub_141A9BF90("container overflow; request exceeds container capacity"); /*0x1405fa82c*/
        *(_OWORD *)(*(_QWORD *)(a1 + 112) + 16 * v32) = v30; /*0x1405fa83b*/
        ++*(_QWORD *)(a1 + 88); /*0x1405fa83f*/
      }
      *(_QWORD *)(*(_QWORD *)(a1 + 120) + 8 * v21) = v20; /*0x1405fa847*/
    }
    else
    {
      *(_BYTE *)(a1 + 104) |= 1u; /*0x1405fa7e5*/
      *(_QWORD *)(a1 + 128) = v20; /*0x1405fa7ea*/
    }
    v14 = v38; /*0x1405fa84b*/
LABEL_33:
    v22 = *v15; /*0x1405fa853*/
    if ( *v15 ) /*0x1405fa853*/
    {
      v23 = *(_QWORD *)&v22[131][2 * *((unsigned int *)v15 + 2)]; /*0x1405fa866*/
      if ( v23 ) /*0x1405fa86d*/
      {
        if ( (*(_BYTE *)(v23 + 24) & 2) != 0 ) /*0x1405fa877*/
        {
          v28 = *(_QWORD *)a1; /*0x1405fa89e*/
          sub_1405E4920( /*0x1405fa8a3*/
            v14,
            v23,
            v16,
            *(_QWORD *)(v23 + 80) + (*v22)[6 * **v22 + 5 + 6 * (unsigned __int64)*((unsigned int *)v15 + 3)]);
          sub_14039FC70(v23); /*0x1405fa8ab*/
        }
      }
    }
    if ( v3 ) /*0x1405fa8b3*/
      v3 = 0; /*0x1405fa8b5*/
    else
      ++v4; /*0x1405fa8ba*/
    v24 = *(_QWORD *)(a1 + 40); /*0x1405fa8bd*/
    v9 = v36; /*0x1405fa8c1*/
    v25 = v24 == 0; /*0x1405fa8c9*/
    v2 = v37; /*0x1405fa8cc*/
    v26 = v24 + 1; /*0x1405fa8d4*/
    result = 0; /*0x1405fa8d8*/
    if ( v25 ) /*0x1405fa8dd*/
      v26 = 0; /*0x1405fa8dd*/
    if ( v4 < v26 ) /*0x1405fa8e4*/
    {
      result = *(_QWORD *)(a1 + 56); /*0x1405fa8ea*/
      v27 = (_QWORD *)(result + 8 * v4); /*0x1405fa8ee*/
      do /*0x1405fa916*/
      {
        v9 = v36; /*0x1405fa8f6*/
        v2 = v37; /*0x1405fa8fe*/
        if ( *v27 ) /*0x1405fa8f2*/
          break; /*0x1405fa906*/
        ++v4; /*0x1405fa90c*/
        ++v27; /*0x1405fa90f*/
      }
      while ( v4 < v26 ); /*0x1405fa916*/
    }
  }
  return result; /*0x1405fa91d*/
}
