// VERIFIED(frida+IDA): WAD multi-entry handler. Called from WadAsyncLoadingThread. frida: 188 calls. Calls WadWtocParser internally.
char __fastcall sub_140393E20(const char *a1, unsigned int a2, __int64 n16, __int64 *a4)
{
  __int64 *v4; // r13
  __int64 *v5; // rdi
  unsigned int n16_1; // esi
  int v9; // eax
  unsigned int v10; // r14d
  unsigned int v11; // ebx
  __int64 v12; // rax
  __int64 v13; // rax
  unsigned int n0x600; // esi
  __int64 v15; // r15
  unsigned __int16 *v16; // r12
  __int64 n2; // rax
  unsigned __int64 v18; // rbx
  unsigned int n0x16000; // esi
  __int64 v20; // rax
  __int64 v21; // rax
  int v22; // ebx
  int v23; // r11d
  __int64 n2_1; // r10
  int v25; // r9d
  int v26; // r8d
  unsigned int v27; // eax
  __int64 v28; // rax
  int n4; // r14d
  __int64 *v30; // r12
  __int64 v31; // r13
  __int64 v32; // rbx
  __int64 v33; // rax
  __int64 v34; // r12
  int v35; // esi
  __int64 n0x600_2; // r14
  unsigned int *v37; // rax
  unsigned __int16 *p_Src; // r12
  __int64 *v39; // r13
  unsigned int v40; // r8d
  __int64 v41; // rdx
  int v42; // eax
  unsigned int v43; // ebx
  int v44; // esi
  unsigned int v45; // edi
  __int64 v46; // rdx
  int v47; // eax
  __int64 v48; // rdx
  char v49; // r14
  unsigned int n11; // esi
  __int16 n32; // bx
  unsigned int n32_1; // r13d
  __int64 v53; // rcx
  __int64 v54; // rax
  char v55; // cl
  unsigned int n0x600_1; // [rsp+50h] [rbp-B0h]
  unsigned int v57; // [rsp+54h] [rbp-ACh]
  __int64 v58; // [rsp+58h] [rbp-A8h] BYREF
  unsigned int v59; // [rsp+60h] [rbp-A0h]
  __int64 *v60; // [rsp+68h] [rbp-98h]
  __int64 v61; // [rsp+70h] [rbp-90h]
  __int64 *v62; // [rsp+78h] [rbp-88h]
  __int64 v63; // [rsp+80h] [rbp-80h]
  unsigned int *v64; // [rsp+88h] [rbp-78h]
  unsigned __int16 *v65; // [rsp+90h] [rbp-70h]
  _DWORD v66[2]; // [rsp+98h] [rbp-68h] BYREF
  __int64 *v67; // [rsp+A0h] [rbp-60h]
  _DWORD v68[2]; // [rsp+A8h] [rbp-58h] BYREF
  __int64 *v69; // [rsp+B0h] [rbp-50h]
  __int64 v70; // [rsp+C0h] [rbp-40h] BYREF
  _BYTE v71[3072]; // [rsp+C8h] [rbp-38h] BYREF
  __int16 n0x600_3; // [rsp+CC8h] [rbp+BC8h]
  __int64 *v73; // [rsp+CD0h] [rbp+BD0h]
  int v74; // [rsp+CD8h] [rbp+BD8h]
  __int128 v75; // [rsp+CE0h] [rbp+BE0h]
  __int128 v76; // [rsp+CF0h] [rbp+BF0h]
  int v77; // [rsp+D00h] [rbp+C00h]
  _OWORD v78[2]; // [rsp+D08h] [rbp+C08h] BYREF
  int v79; // [rsp+D28h] [rbp+C28h]
  _WORD Src[1536]; // [rsp+D30h] [rbp+C30h] BYREF

  v4 = a4 + 14;
  v61 = *a4;
  v5 = a4;
  v60 = a4;
  n16_1 = n16;
  if ( !WadWtocParser((__int64)a1, a2, n16, a4) )
  {
    sub_1408FB650("loading of TOC failed for %s of type = %d", a1, n16_1);
    return 0;
  }
  if ( !(unsigned __int8)sub_140393C00(v5, a1, n16_1) )
  {
    sub_1408FB650("AllocateMemory failed for %s of type = % d", a1, n16_1);
    return 0;
  }
  v9 = sub_1403B3FE0(v5);
  v10 = 0;
  if ( v9 )
  {
    v11 = 264 * v9;
    v12 = sub_1403B38D0();
    qword_143A1CE10 = sub_140365450(v12, v11, 8);
    dword_143A1CE18 = 0;
  }
  v13 = *((unsigned int *)v5 + 4);
  n0x600_1 = 0;
  v57 = 0;
  n0x600 = 0;
  v77 = 0;
  v79 = 0;
  v15 = 144 * v13 + 64;
  v59 = 0;
  v75 = 0;
  v76 = 0;
  memset(v78, 0, sizeof(v78));
  if ( (_DWORD)v13 )
  {
    while ( 1 )
    {
      v16 = (unsigned __int16 *)(v5[9] + 144LL * (int)v10);
      v65 = v16;
      n2 = *((unsigned __int8 *)v16 + 111);
      if ( (_BYTE)n2 == 2 )
      {
        v18 = *((unsigned int *)v16 + 5) | ((unsigned __int64)*((unsigned int *)v16 + 4) << 32);
        if ( v18 )
        {
          n0x16000 = *((_DWORD *)v16 + 1);
          if ( n0x16000 <= 0x16000 )
          {
            v20 = sub_140390CD0(25);
            v21 = sub_1404DAF50(v20, 0, n0x16000, v18, (__int64)(v16 + 12), 0, &v58);
            if ( !v21 )
              v21 = sub_140365540(v5[11], n0x16000, 4096);
            *((_QWORD *)v16 + 15) = v21;
          }
          n0x600 = n0x600_1;
        }
      }
      else if ( *((_DWORD *)v16 + 1) )
      {
        *((_QWORD *)v16 + 15) += v4[n2];
      }
      v22 = *((_DWORD *)v16 + 24);
      if ( v22 )
        *((_QWORD *)v16 + 16) += v4[5];
      v23 = *((_DWORD *)v16 + 25);
      if ( v23 )
        *((_QWORD *)v16 + 17) += v4[8];
      n2_1 = *((unsigned __int8 *)v16 + 111);
      v25 = *((_DWORD *)&v75 + n2_1);
      v26 = (-*((_DWORD *)v16 + 26) & (*((_DWORD *)v16 + 26) + v25 + *((_DWORD *)v78 + n2_1) - 1))
          - (v25
           + *((_DWORD *)v78 + n2_1));
      v27 = *((_DWORD *)v16 + 1);
      if ( *v16 != 25 )
        v27 = v57;
      v57 = v27;
      if ( *v16 != 25 )
        v26 += *((_DWORD *)v16 + 1);
      *((_DWORD *)&v75 + n2_1) = v25 + v26;
      DWORD1(v76) += v22;
      v77 += v23;
      if ( (_BYTE)n2_1 == 2 )
      {
        if ( n0x600 >= 0x600 )
          __debugbreak();
        v28 = n0x600++;
        n0x600_1 = n0x600;
        Src[v28] = v10;
      }
      if ( (v16[57] & 1) != 0 )
        break;
LABEL_49:
      if ( (unsigned __int8)sub_1403B3930(*v16) )
      {
        switch ( *v16 )
        {
          case 0x1Fu:
            v49 = 0;
            goto LABEL_61;
          case 0x20u:
            n11 = 11;
            v49 = 0;
            goto LABEL_62;
          case 0x34u:
            n32 = 32;
            n11 = 15;
            n32_1 = 32;
            v49 = 0;
            goto LABEL_63;
          case 0x35u:
            n32 = 32;
            n11 = 14;
            n32_1 = 32;
            v49 = 0;
            goto LABEL_63;
          case 0x36u:
            n11 = 16;
            v49 = 0;
            goto LABEL_62;
          case 0x39u:
            n11 = 11;
            goto LABEL_56;
          case 0x3Au:
            n11 = 16;
LABEL_56:
            v49 = 1;
            n32 = 0;
            n32_1 = 0;
            if ( !sub_1403B2840() )
              goto LABEL_63;
            goto LABEL_72;
          default:
            v49 = 0;
LABEL_61:
            n11 = 10;
LABEL_62:
            n32 = 0;
            n32_1 = 0;
LABEL_63:
            *(_QWORD *)(264LL * (unsigned int)dword_143A1CE18 + qword_143A1CE10 + 80) = v5[10];
            *(_QWORD *)(264LL * (unsigned int)dword_143A1CE18 + qword_143A1CE10 + 88) = v5[11];
            *(_QWORD *)(264LL * (unsigned int)dword_143A1CE18 + qword_143A1CE10 + 96) = v5[12];
            v53 = 264LL * (unsigned int)dword_143A1CE18;
            v54 = qword_143A1CE10;
            *(_BYTE *)(v53 + qword_143A1CE10 + 256) &= ~1u;
            *(_BYTE *)(v53 + v54 + 256) |= v49;
            *(_QWORD *)(264LL * (unsigned int)dword_143A1CE18 + qword_143A1CE10) = &unk_143A1D8F0;
            if ( (unsigned __int8)WadMultiEntryHandler(
                                    v16 + 12,
                                    n32_1,
                                    n11,
                                    qword_143A1CE10 + 264LL * (unsigned int)dword_143A1CE18) )
            {
              v55 = dword_143A1CE18++;
            }
            else
            {
              if ( n32 )
                n10 = 2;
              v55 = -1;
            }
            *((_BYTE *)v16 + 108) = v55;
            break;
        }
      }
      if ( *((_QWORD *)v16 + 15) )
      {
        if ( *((_BYTE *)v16 + 111) != 8 )
          v16[1] |= 0x2000u;
      }
LABEL_72:
      v4 = v5 + 14;
      n0x600 = n0x600_1;
      v10 = v59 + 1;
      v59 = v10;
      if ( v10 >= *((_DWORD *)v5 + 4) )
        goto LABEL_73;
    }
    n4 = 0;
    v62 = v4;
    v30 = v4;
    HIDWORD(v58) = 0;
    v31 = 0;
    v63 = 0;
    while ( 1 )
    {
      v32 = *(unsigned int *)((char *)&v75 + v31);
      if ( n4 == 2 )
      {
        if ( n0x600 )
        {
          v33 = sub_1403B38E0();
          v34 = sub_140365450(v33, (unsigned int)v32, 8);
          if ( !v34 )
          {
            v66[0] = 2;
            v67 = v5;
            n0x600_2 = n0x600;
            v37 = (unsigned int *)((char *)v78 + v31);
            p_Src = Src;
            v39 = v60;
            v64 = v37;
            v40 = *v37;
            do
            {
              v41 = v39[9] + 144LL * *p_Src;
              v42 = *(_DWORD *)(v41 + 104);
              v43 = *(_DWORD *)(v41 + 4);
              v66[1] = *p_Src;
              v44 = -v42 & (v42 + v40 - 1);
              v45 = v44 - v40;
              (*(void (__fastcall **)(__int64, _QWORD, __int64, _QWORD, unsigned int, _QWORD, __int64 (__fastcall *)(), _DWORD *, int))(*(_QWORD *)v61 + 96LL))(
                v61,
                *(_QWORD *)(v41 + 120),
                v15 + v44 - v40,
                v43,
                v43,
                0,
                WadReadCallback1,
                v66,
                16);
              v15 += v43 + v45;
              v40 = v44 + v43;
              ++p_Src;
              --n0x600_2;
            }
            while ( n0x600_2 );
            n4 = HIDWORD(v58);
            v31 = v63;
            v5 = v60;
            *v64 = v40;
            goto LABEL_47;
          }
          v74 = *(_DWORD *)((char *)v78 + v31);
          v35 = v74;
          n0x600_3 = n0x600_1;
          v73 = v5;
          memcpy(v71, Src, sizeof(v71));
          v70 = v34;
          (*(void (__fastcall **)(__int64, __int64, __int64, _QWORD, _DWORD, _QWORD, __int64 (__fastcall *)(), __int64 *, int))(*(_QWORD *)v61 + 96LL))(
            v61,
            v34,
            v15,
            (unsigned int)v32,
            v32,
            0,
            WadReadCallbackCopy,
            &v70,
            3104);
          v5 = v60;
          *(_DWORD *)((char *)v78 + v31) = v35 + v32;
          goto LABEL_46;
        }
      }
      else
      {
        v69 = v5;
        v68[0] = n4;
        if ( (_DWORD)v32 )
        {
          if ( n4 == 5 )
          {
            sub_1403B2830();
          }
          else if ( (!(unsigned __int8)sub_1403B2820() || (unsigned int)(n4 - 6) > 1) && n4 != 4 )
          {
            v46 = *(unsigned int *)((char *)v78 + v31);
            v47 = v46 + v32;
            v48 = *v30 + v46;
            v68[1] = v47;
            (*(void (__fastcall **)(__int64, __int64, __int64, __int64, _DWORD, _QWORD, __int64 (__fastcall *)(), _DWORD *, int))(*(_QWORD *)v61 + 96LL))(
              v61,
              v48,
              v15,
              v32,
              v32,
              0,
              WadReadCallback1,
              v68,
              16);
          }
          *(_DWORD *)((char *)v78 + v31) += v32;
LABEL_46:
          v15 += v32;
        }
      }
LABEL_47:
      ++v62;
      ++n4;
      n0x600 = n0x600_1;
      v31 += 4;
      v30 = v62;
      HIDWORD(v58) = n4;
      v63 = v31;
      if ( n4 >= 9 )
      {
        v16 = v65;
        v77 = 0;
        n0x600_1 = 0;
        v15 += v57;
        v57 = 0;
        v75 = 0;
        v76 = 0;
        goto LABEL_49;
      }
    }
  }
LABEL_73:
  qword_143AC6EB8 = (*(__int64 (__fastcall **)(__int64))(*(_QWORD *)*v5 + 56LL))(*v5);
  (*(void (__fastcall **)(__int64))(*(_QWORD *)*v5 + 48LL))(*v5);
  nullsub_64(v5);
  return 1;
}
