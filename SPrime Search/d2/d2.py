#!/usr/bin/env python3
"""D2v1: <=7-byte register programs with NAND/XOR and exact float64 rank carrier."""
from __future__ import annotations
import argparse,json,struct
LEAVES=(0xf0,0xcc,0xaa)
HEADER=b'D2'; MAX_GATES=5
DEPTH_TOTALS=[3]
p=1
for j in range(MAX_GATES):
    p*=2*(3+j)*(3+j); DEPTH_TOTALS.append(p)
TOTAL=sum(DEPTH_TOTALS)

def _payload(word):
    if not isinstance(word,(bytes,bytearray)) or not bytes(word).startswith(HEADER): raise ValueError('bad D2 header')
    payload=bytes(word)[2:]
    if len(payload)==1 and payload in (b'x',b'y',b'z'): return payload,True
    if not 1<=len(payload)<=MAX_GATES: raise ValueError('D2v1 requires terminal or 1..5 instructions')
    return payload,False

def instructions(word):
    payload,terminal=_payload(word)
    if terminal:
        i=b'xyz'.index(payload); return i,()
    result=[]
    for j,t in enumerate(payload):
        if t & 0x80: raise ValueError('reserved high bit must be zero in D2v1')
        op=(t>>6)&1;a=(t>>3)&7;b=t&7;n=3+j
        if a>=n or b>=n: raise ValueError('forward/absent register reference')
        result.append((op,a,b))
    return None,tuple(result)

def decode(word):
    terminal,ops=instructions(word)
    if terminal is not None:return LEAVES[terminal],[('TERMINAL',terminal,terminal,LEAVES[terminal])]
    regs=list(LEAVES);steps=[]
    for op,a,b in ops:
        v=(0xff^(regs[a]&regs[b])) if op==0 else (regs[a]^regs[b]);regs.append(v);steps.append(('NAND' if op==0 else 'XOR',a,b,v))
    return regs[-1],steps

def eval_row(word,row):
    if type(row) is not int or not 0<=row<8:raise ValueError('row 0..7')
    terminal,ops=instructions(word);regs=[bool(row&4),bool(row&2),bool(row&1)]
    if terminal is not None:return int(regs[terminal])
    for op,a,b in ops:regs.append((not(regs[a] and regs[b])) if op==0 else (regs[a]!=regs[b]))
    return int(regs[-1])

def rank(word):
    terminal,ops=instructions(word)
    if terminal is not None:return terminal
    k=len(ops);value=0
    for j,(op,a,b) in enumerate(ops):
        n=3+j;radix=2*n*n;digit=op*n*n+a*n+b;value=value*radix+digit
    return sum(DEPTH_TOTALS[:k])+value

def unrank(index):
    if type(index) is not int or not 0<=index<TOTAL:raise ValueError('rank outside D2v1')
    if index<3:return HEADER+b'xyz'[index:index+1]
    for k in range(1,MAX_GATES+1):
        offset=sum(DEPTH_TOTALS[:k])
        if index<offset+DEPTH_TOTALS[k]:
            value=index-offset;digits=[]
            for j in range(k-1,-1,-1):
                n=3+j;radix=2*n*n;value,d=divmod(value,radix);digits.append(d)
            payload=[]
            for j,d in enumerate(reversed(digits)):
                n=3+j;op,rem=divmod(d,n*n);a,b=divmod(rem,n);payload.append((op<<6)|(a<<3)|b)
            return HEADER+bytes(payload)
    raise RuntimeError('rank escaped')

def to_float(word):
    r=rank(word);bits=(1023<<52)|r;return struct.unpack('>d',bits.to_bytes(8,'big'))[0]

def from_float(value):
    if type(value) is not float:raise ValueError('float required')
    bits=int.from_bytes(struct.pack('>d',value),'big')
    if bits>>63 or ((bits>>52)&0x7ff)!=1023:raise ValueError('outside D2 float carrier exponent')
    return unrank(bits&((1<<52)-1))

def main():
    p=argparse.ArgumentParser();p.add_argument('--hex');p.add_argument('--rank',type=int);a=p.parse_args()
    w=bytes.fromhex(a.hex) if a.hex else unrank(a.rank if a.rank is not None else 3)
    table,steps=decode(w);f=to_float(w)
    print(json.dumps({'word_hex':w.hex(),'bytes':len(w),'rank':rank(w),'float_hex':f.hex(),'table':hex(table),'rows':[eval_row(w,r) for r in range(8)],'steps':steps},indent=2))
if __name__=='__main__':main()
