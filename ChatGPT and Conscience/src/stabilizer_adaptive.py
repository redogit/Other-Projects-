"""Delay subgroup bookkeeping until a nonzero preserving translation is verified.

An odd-sized label class proves that no nonzero translation can preserve the
table; that case needs no candidate scans. Otherwise start with plain anchor
checks, then activate verified-subgroup reuse upon the first positive witness.
"""
from stabilizer_matched import prepare,output

def adaptive_stabilizers(points,n):
    anchors,ceiling=prepare(points,n)
    if not anchors:return output(n)
    if ceiling==1:return output(n,[])
    root=anchors[0];remaining=iter(anchors[1:])
    for y in remaining:
        t=root^y
        for x,b in points.items():
            if points.get(x^t,2)!=b:break
        else:
            group={0,t}
            break
    else:return output(n,[])
    for y in remaining:
        if len(group)==ceiling:break
        t=root^y
        if t in group:continue
        for x,b in points.items():
            if points.get(x^t,2)!=b:break
        else:group.update([h^t for h in group])
    return output(n,group-{0})
