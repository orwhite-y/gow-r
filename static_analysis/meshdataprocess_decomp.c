__int64 __fastcall sub_1405E4920(__int64 a1, __int64 a2, __int64 a3, __int64 a4)
{
  unsigned __int64 v4; // rbx
  _DWORD *v7; // r11
  int v8; // ebx
  int v9; // edi
  int v10; // edx
  __int64 v11; // r9
  unsigned __int16 v12; // r8
  int v13; // r10d
  __int64 result; // rax
  int v15; // [rsp+20h] [rbp-18h]

  v4 = *(unsigned __int16 *)(a3 + 80); /*0x1405e493a*/
  v7 = (_DWORD *)(*(_QWORD *)(a1 + 208) + 4 * (v4 >> 5)); /*0x1405e495e*/
  *v7 &= ~(1 << (*(_WORD *)(a3 + 80) & 0x1F)); /*0x1405e496e*/
  *(_DWORD *)(a1 + 8) &= 0xFFFFFFF3; /*0x1405e4971*/
  *(_QWORD *)(*(_QWORD *)(a1 + 224) + 8 * v4) = a2; /*0x1405e497c*/
  sub_1405E5700(a3, a4, *(_QWORD *)(a1 + 16) + ((unsigned __int64)*(unsigned __int16 *)(a3 + 80) << 6), a2); /*0x1405e4990*/
  v8 = -1; /*0x1405e49a5*/
  v9 = (unsigned __int16)(*(unsigned int *)(a1 + 88) / (unsigned __int64)*(int *)(a1 + 24)); /*0x1405e49aa*/
  do /*0x1405e4a2b*/
  {
    if ( v8 < 0 ) /*0x1405e49ba*/
    {
      v12 = *(_WORD *)(a3 + 80); /*0x1405e49ed*/
      v13 = -1; /*0x1405e49f2*/
      v11 = v12; /*0x1405e49f8*/
    }
    else
    {
      v10 = *(unsigned __int16 *)(a3 + 80); /*0x1405e49bc*/
      v11 = *(unsigned __int16 *)(a3 + 80); /*0x1405e49c3*/
      v12 = *(_WORD *)(*(_QWORD *)(a1 + 80) + 8LL * (v10 + v8 * *(_DWORD *)(a1 + 24)) + 4); /*0x1405e49d2*/
      v13 = *(_DWORD *)(*(_QWORD *)(a1 + 80) + 8LL * (v10 + v8 * *(_DWORD *)(a1 + 24))); /*0x1405e49e7*/
    }
    LOBYTE(v15) = *(_BYTE *)(a3 + 131); /*0x1405e4a1d*/
    result = sub_1405E5090(*(_QWORD *)(a1 + 48) + 960LL * v12, a3, v13, *(_QWORD *)(a1 + 16) + (v11 << 6), v15, a1 + 96); /*0x1405e4a22*/
    ++v8; /*0x1405e4a27*/
  }
  while ( v8 < v9 ); /*0x1405e4a2b*/
  *(_DWORD *)(a3 + 76) |= 4u; /*0x1405e4a2d*/
  return result; /*0x1405e4a31*/
}
