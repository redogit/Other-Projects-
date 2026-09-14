#!/usr/bin/env python3
"""Canonical Boolean decision fields: ANF coordinates, compact ASCII, and tagged float carriers."""
from __future__ import annotations
from itertools import product
import struct

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
INV = {c:i for i,c in enumerate(ALPHABET)}
TAGS = {'A4':1, 'A5':2, 'B4':3, 'T4':4}
REV_TAGS = {v:k for k,v in TAGS.items()}


def _check_int(v, lo, hi, name):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(f"{name} must be an integer in {lo}..{hi}")


def mobius(mask:int, n:int) -> int:
    """Truth-table <-> ANF coefficient transform over GF(2); self-inverse."""
    _check_int(n,0,5,'n')
    width = 1 << n
    _check_int(mask,0,(1<<width)-1,'mask')
    a = [(mask>>i)&1 for i in range(width)]
    for bit in range(n):
        b = 1 << bit
        for s in range(width):
            if s & b:
                a[s] ^= a[s ^ b]
    out = 0
    for i,v in enumerate(a): out |= v << i
    return out


def eval_anf(coeff:int, n:int, row:int) -> int:
    width=1<<n
    _check_int(coeff,0,(1<<width)-1,'coeff')
    _check_int(row,0,width-1,'row')
    value=0
    sub=row
    while True:
        value ^= (coeff >> sub) & 1
        if sub==0: return value
        sub=(sub-1)&row


def truth_from_anf(coeff:int,n:int) -> int:
    width=1<<n
    return sum(eval_anf(coeff,n,row)<<row for row in range(width))


def algebraic_degree(coeff:int,n:int) -> int:
    if coeff==0: return -1
    return max(s.bit_count() for s in range(1<<n) if (coeff>>s)&1)


def _encode_fixed(value:int, chars:int) -> str:
    _check_int(value,0,(1<<(6*chars))-1,'payload')
    out=['A']*chars
    for i in range(chars-1,-1,-1):
        out[i]=ALPHABET[value&63]; value >>= 6
    return ''.join(out)


def _decode_fixed(text:str) -> int:
    if not text or any(c not in INV for c in text): raise ValueError('noncanonical alphabet')
    value=0
    for c in text: value=(value<<6)|INV[c]
    return value


def encode_A(n:int, truth:int) -> str:
    if n not in (4,5): raise ValueError('A format supports n=4 or 5')
    width=1<<n
    _check_int(truth,0,(1<<width)-1,'truth')
    coeff=mobius(truth,n)
    chars=(width+5)//6
    return f'A{n}'+_encode_fixed(coeff,chars)


def decode_A(text:str) -> tuple[int,int]:
    if len(text)<3 or text[0]!='A' or text[1] not in '45': raise ValueError('bad A format')
    n=int(text[1]); width=1<<n; chars=(width+5)//6
    if len(text)!=2+chars: raise ValueError('wrong A length')
    coeff=_decode_fixed(text[2:])
    if coeff >= 1<<width: raise ValueError('noncanonical high payload bits')
    return n, truth_from_anf(coeff,n)


def pack_two(f0:int,f1:int) -> int:
    _check_int(f0,0,0xffff,'output0 truth'); _check_int(f1,0,0xffff,'output1 truth')
    return mobius(f0,4) | (mobius(f1,4)<<16)


def unpack_two(rank:int) -> tuple[int,int]:
    _check_int(rank,0,0xffffffff,'two-output rank')
    return truth_from_anf(rank&0xffff,4), truth_from_anf((rank>>16)&0xffff,4)


def encode_B4(f0:int,f1:int) -> str:
    return 'B4'+_encode_fixed(pack_two(f0,f1),6)


def decode_B4(text:str) -> tuple[int,int]:
    if len(text)!=8 or not text.startswith('B4'): raise ValueError('bad B4 format')
    rank=_decode_fixed(text[2:])
    if rank >= 1<<32: raise ValueError('noncanonical high payload bits')
    return unpack_two(rank)


def transition_to_outputs(rank:int) -> tuple[int,int]:
    _check_int(rank,0,0xffffffff,'transition rank')
    f0=f1=0
    for context in range(4):
        byte=(rank>>(8*context))&0xff
        for state in range(4):
            nxt=(byte>>(2*state))&3
            row=(context<<2)|state
            f0 |= (nxt&1)<<row
            f1 |= ((nxt>>1)&1)<<row
    return f0,f1


def outputs_to_transition(f0:int,f1:int) -> int:
    _check_int(f0,0,0xffff,'f0'); _check_int(f1,0,0xffff,'f1')
    rank=0
    for context in range(4):
        byte=0
        for state in range(4):
            row=(context<<2)|state
            nxt=((f0>>row)&1) | (((f1>>row)&1)<<1)
            byte |= nxt<<(2*state)
        rank |= byte<<(8*context)
    return rank


def encode_T4(rank:int) -> str:
    _check_int(rank,0,0xffffffff,'transition rank')
    return 'T4'+_encode_fixed(rank,6)


def decode_T4(text:str) -> int:
    if len(text)!=8 or not text.startswith('T4'): raise ValueError('bad T4 format')
    rank=_decode_fixed(text[2:])
    if rank >= 1<<32: raise ValueError('noncanonical high payload bits')
    return rank


def to_float(format_name:str, payload:int) -> float:
    if format_name not in TAGS: raise ValueError('unknown format tag')
    _check_int(payload,0,(1<<48)-1,'payload')
    frac=(TAGS[format_name]<<48)|payload
    bits=(1023<<52)|frac
    return struct.unpack('>d',bits.to_bytes(8,'big'))[0]


def from_float(value:float) -> tuple[str,int]:
    if type(value) is not float: raise ValueError('expected float')
    bits=int.from_bytes(struct.pack('>d',value),'big')
    if (bits>>63) or ((bits>>52)&0x7ff)!=1023: raise ValueError('outside tagged carrier')
    frac=bits&((1<<52)-1); tag=(frac>>48)&15; payload=frac&((1<<48)-1)
    if tag not in REV_TAGS: raise ValueError('unknown carrier tag')
    return REV_TAGS[tag],payload


def identity_transition() -> int:
    byte=sum(s<<(2*s) for s in range(4))
    return sum(byte<<(8*c) for c in range(4))


def get_next(rank:int,context:int,state:int) -> int:
    _check_int(context,0,3,'context'); _check_int(state,0,3,'state')
    return (rank>>(8*context+2*state))&3


def set_next(rank:int,context:int,state:int,nxt:int) -> int:
    _check_int(rank,0,0xffffffff,'rank'); _check_int(context,0,3,'context'); _check_int(state,0,3,'state'); _check_int(nxt,0,3,'next state')
    shift=8*context+2*state
    return (rank & ~(3<<shift)) | (nxt<<shift)


def local_cycles(byte:int) -> tuple[int,...]:
    _check_int(byte,0,255,'local map')
    f=[(byte>>(2*s))&3 for s in range(4)]
    global_seen=set(); lengths=[]
    for start in range(4):
        if start in global_seen: continue
        path=[]; pos={}; x=start
        while x not in pos and x not in global_seen:
            pos[x]=len(path); path.append(x); x=f[x]
        if x in pos: lengths.append(len(path[pos[x]:]))
        global_seen.update(path)
    return tuple(sorted(lengths))
