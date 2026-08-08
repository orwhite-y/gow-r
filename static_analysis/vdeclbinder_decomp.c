__int64 __fastcall sub_1405E5090(__int64 a1, __int64 a2, int a3, __int64 a4, int a5, __int64 a6)
{
  __int64 v6; // r14
  unsigned __int64 v7; // r9
  __int64 v11; // r10
  int v12; // ecx
  int v13; // ebx
  __int64 v14; // r10
  int v15; // ecx
  int v16; // ebx
  __int64 v17; // r10
  __int64 v18; // r10
  __int64 v19; // r10
  __int64 v20; // r10
  __int64 v21; // r10
  __int64 v22; // r10
  __int64 v23; // r10
  __int64 v24; // r10
  __int64 v25; // r10
  __int64 v26; // r10
  int v27; // r9d
  int v28; // eax
  __int64 v29; // r10
  __int64 v30; // r10
  __int64 v31; // r10
  unsigned __int64 n15; // r9
  __int64 v33; // rcx
  __int64 v34; // r10
  __int64 v35; // r8
  __int64 v36; // r10
  unsigned __int8 n15_1; // r8
  __int64 v38; // r10
  __int64 result; // rax
  __int64 v40; // [rsp+50h] [rbp+8h] BYREF

  v6 = *(_QWORD *)(a4 + 40); /*0x1405e509e*/
  v7 = *(_QWORD *)(a2 + 112); /*0x1405e50a5*/
  if ( (v7 & 0xF) != 0xF ) /*0x1405e50c4*/
  {
    v11 = a2 + *(unsigned int *)(a2 + 96) + 8 * (*(_QWORD *)(a2 + 112) & 0xFLL); /*0x1405e50cf*/
    if ( v11 ) /*0x1405e50d6*/
    {
      v12 = 5 * *(unsigned __int8 *)(v11 + 4); /*0x1405e50f1*/
      v13 = v6 + 40 * *(unsigned __int8 *)(v11 + 4); /*0x1405e50f8*/
      v40 = *(_QWORD *)v11; /*0x1405e50fc*/
      LOBYTE(v40) = 18; /*0x1405e5104*/
      sub_140EBC430(a1 + 4, a1, a1 + 376, v6 + 8 * v12, v11, 0); /*0x1405e510d*/
      sub_140EBC430(a1 + 76, a1 + 72, a1 + 592, v13, (__int64)&v40, 0); /*0x1405e5133*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e5138*/
    }
  }
  if ( (unsigned __int8)v7 >> 4 != 15 ) /*0x1405e5147*/
  {
    v14 = a2 + *(unsigned int *)(a2 + 96) + 8LL * ((unsigned __int8)v7 >> 4); /*0x1405e5152*/
    if ( v14 ) /*0x1405e5159*/
    {
      v15 = 5 * *(unsigned __int8 *)(v14 + 4); /*0x1405e5175*/
      v16 = v6 + 40 * *(unsigned __int8 *)(v14 + 4); /*0x1405e517c*/
      v40 = *(_QWORD *)v14; /*0x1405e5180*/
      LOBYTE(v40) = 19; /*0x1405e5188*/
      sub_140EBC430(a1 + 52, a1 + 48, a1 + 520, v6 + 8 * v15, v14, 0); /*0x1405e5191*/
      sub_140EBC430(a1 + 84, a1 + 80, a1 + 616, v16, (__int64)&v40, 0); /*0x1405e51b7*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e51bc*/
    }
  }
  if ( (BYTE1(v7) & 0xF) != 0xF ) /*0x1405e51d0*/
  {
    v17 = a2 + *(unsigned int *)(a2 + 96) + 8LL * (BYTE1(v7) & 0xF); /*0x1405e51db*/
    if ( v17 ) /*0x1405e51e2*/
    {
      sub_140EBC430(a1 + 44, a1 + 40, a1 + 496, v6 + 40 * *(unsigned __int8 *)(v17 + 4), v17, 0); /*0x1405e520a*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e520f*/
    }
  }
  if ( ((v7 >> 12) & 0xF) != 0xF ) /*0x1405e521e*/
  {
    v18 = a2 + *(unsigned int *)(a2 + 96) + 8LL * ((unsigned __int16)v7 >> 12); /*0x1405e5229*/
    if ( v18 ) /*0x1405e5230*/
    {
      sub_140EBC430(a1 + 12, a1 + 8, a1 + 400, v6 + 40 * *(unsigned __int8 *)(v18 + 4), v18, 0); /*0x1405e5258*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e525d*/
    }
  }
  if ( (BYTE2(v7) & 0xF) != 0xF ) /*0x1405e526c*/
  {
    v19 = a2 + *(unsigned int *)(a2 + 96) + 8LL * (BYTE2(v7) & 0xF); /*0x1405e5277*/
    if ( v19 ) /*0x1405e527e*/
    {
      sub_140EBC430(a1 + 20, a1 + 16, a1 + 424, v6 + 40 * *(unsigned __int8 *)(v19 + 4), v19, 0); /*0x1405e52a6*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e52ab*/
    }
  }
  if ( ((v7 >> 20) & 0xF) != 0xF ) /*0x1405e52ba*/
  {
    v20 = a2 + *(unsigned int *)(a2 + 96) + 8 * ((v7 >> 20) & 0xF); /*0x1405e52c5*/
    if ( v20 ) /*0x1405e52cc*/
    {
      sub_140EBC430(a1 + 28, a1 + 24, a1 + 448, v6 + 40 * *(unsigned __int8 *)(v20 + 4), v20, 0); /*0x1405e52f4*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e52f9*/
    }
  }
  if ( (BYTE3(v7) & 0xF) != 0xF ) /*0x1405e5308*/
  {
    v21 = a2 + *(unsigned int *)(a2 + 96) + 8LL * (BYTE3(v7) & 0xF); /*0x1405e5313*/
    if ( v21 ) /*0x1405e531a*/
    {
      sub_140EBC430(a1 + 36, a1 + 32, a1 + 472, v6 + 40 * *(unsigned __int8 *)(v21 + 4), v21, 0); /*0x1405e5342*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e5347*/
    }
  }
  if ( ((v7 >> 28) & 0xF) != 0xF ) /*0x1405e5356*/
  {
    v22 = a2 + *(unsigned int *)(a2 + 96) + 8LL * ((unsigned int)v7 >> 28); /*0x1405e5361*/
    if ( v22 ) /*0x1405e5368*/
    {
      sub_140EBC430(a1 + 60, a1 + 56, a1 + 544, v6 + 40 * *(unsigned __int8 *)(v22 + 4), v22, 0); /*0x1405e5390*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e5395*/
    }
  }
  if ( (BYTE4(v7) & 0xF) != 0xF ) /*0x1405e53a4*/
  {
    v23 = a2 + *(unsigned int *)(a2 + 96) + 8LL * (BYTE4(v7) & 0xF); /*0x1405e53af*/
    if ( v23 ) /*0x1405e53b6*/
    {
      sub_140EBC430(a1 + 68, a1 + 64, a1 + 568, v6 + 40 * *(unsigned __int8 *)(v23 + 4), v23, 0); /*0x1405e53de*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e53e3*/
    }
  }
  if ( ((v7 >> 36) & 0xF) != 0xF ) /*0x1405e53f2*/
  {
    v24 = a2 + *(unsigned int *)(a2 + 96) + 8 * ((v7 >> 36) & 0xF); /*0x1405e53fd*/
    if ( v24 ) /*0x1405e5404*/
    {
      sub_140EBC430(a1 + 100, a1 + 96, a1 + 664, v6 + 40 * *(unsigned __int8 *)(v24 + 4), v24, 0); /*0x1405e542c*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e5431*/
    }
  }
  if ( (BYTE5(v7) & 0xF) != 0xF ) /*0x1405e5440*/
  {
    v25 = a2 + *(unsigned int *)(a2 + 96) + 8LL * (BYTE5(v7) & 0xF); /*0x1405e544b*/
    if ( v25 ) /*0x1405e5452*/
    {
      sub_140EBC430(a1 + 92, a1 + 88, a1 + 640, v6 + 40 * *(unsigned __int8 *)(v25 + 4), v25, 0); /*0x1405e547a*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e547f*/
    }
  }
  if ( ((v7 >> 44) & 0xF) != 0xF ) /*0x1405e548e*/
  {
    v26 = a2 + *(unsigned int *)(a2 + 96) + 8 * ((v7 >> 44) & 0xF); /*0x1405e5499*/
    if ( v26 ) /*0x1405e54a0*/
    {
      v27 = 0; /*0x1405e54a5*/
      if ( a3 == -1 ) /*0x1405e54a8*/
      {
        v28 = v6 + 40 * *(unsigned __int8 *)(v26 + 4); /*0x1405e54be*/
      }
      else
      {
        v27 = a3; /*0x1405e54a8*/
        v28 = a6; /*0x1405e54ae*/
      }
      sub_140EBC430(a1 + 108, a1 + 104, a1 + 688, v28, v26, v27); /*0x1405e54de*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e54e3*/
    }
  }
  if ( (BYTE6(v7) & 0xF) != 0xF ) /*0x1405e54f7*/
  {
    v29 = a2 + *(unsigned int *)(a2 + 96) + 8LL * (BYTE6(v7) & 0xF); /*0x1405e5502*/
    if ( v29 ) /*0x1405e5509*/
    {
      sub_140EBC430(a1 + 116, a1 + 112, a1 + 712, v6 + 40 * *(unsigned __int8 *)(v29 + 4), v29, 0); /*0x1405e5531*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e5536*/
    }
  }
  if ( ((v7 >> 52) & 0xF) != 0xF ) /*0x1405e5545*/
  {
    v30 = a2 + *(unsigned int *)(a2 + 96) + 8 * ((v7 >> 52) & 0xF); /*0x1405e5550*/
    if ( v30 ) /*0x1405e5557*/
    {
      sub_140EBC430(a1 + 124, a1 + 120, a1 + 736, v6 + 40 * *(unsigned __int8 *)(v30 + 4), v30, 0); /*0x1405e557f*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e5584*/
    }
  }
  if ( (HIBYTE(v7) & 0xF) != 0xF ) /*0x1405e5593*/
  {
    v31 = a2 + *(unsigned int *)(a2 + 96) + 8LL * (HIBYTE(v7) & 0xF); /*0x1405e559e*/
    if ( v31 ) /*0x1405e55a5*/
    {
      sub_140EBC430(a1 + 132, a1 + 128, a1 + 760, v6 + 40 * *(unsigned __int8 *)(v31 + 4), v31, 0); /*0x1405e55d3*/
      v7 = *(_QWORD *)(a2 + 112); /*0x1405e55d8*/
    }
  }
  n15 = v7 >> 60; /*0x1405e55dc*/
  if ( (_BYTE)n15 != 15 ) /*0x1405e55e4*/
  {
    v33 = a2 + *(unsigned int *)(a2 + 96); /*0x1405e55e9*/
    v34 = v33 + 8 * n15; /*0x1405e55ec*/
    if ( v34 ) /*0x1405e55f3*/
      sub_140EBC430(a1 + 140, a1 + 136, a1 + 784, v6 + 40 * *(unsigned __int8 *)(v34 + 4), v33 + 8 * n15, 0); /*0x1405e5621*/
  }
  v35 = *(_QWORD *)(a2 + 120); /*0x1405e5626*/
  if ( (v35 & 0xF) != 0xF ) /*0x1405e5632*/
  {
    v36 = a2 + *(unsigned int *)(a2 + 96) + 8 * (*(_QWORD *)(a2 + 120) & 0xFLL); /*0x1405e563d*/
    if ( v36 ) /*0x1405e5644*/
    {
      sub_140EBC430(a1 + 148, a1 + 144, a1 + 808, v6 + 40 * *(unsigned __int8 *)(v36 + 4), v36, 0); /*0x1405e5672*/
      v35 = *(_QWORD *)(a2 + 120); /*0x1405e5677*/
    }
  }
  n15_1 = (unsigned __int8)v35 >> 4; /*0x1405e567f*/
  if ( n15_1 != 15 ) /*0x1405e5687*/
  {
    v38 = a2 + *(unsigned int *)(a2 + 96) + 8LL * n15_1; /*0x1405e5693*/
    if ( v38 ) /*0x1405e569a*/
      sub_140EBC430(a1 + 156, a1 + 152, a1 + 832, v6 + 40 * *(unsigned __int8 *)(v38 + 4), v38, 0); /*0x1405e56c8*/
  }
  *(_DWORD *)(a1 + 184) = *(_DWORD *)(a2 + 84); /*0x1405e56d0*/
  result = *(unsigned __int16 *)(a2 + 82); /*0x1405e56d6*/
  *(_DWORD *)(a1 + 188) = result; /*0x1405e56da*/
  return result; /*0x1405e56e0*/
}
