#!/usr/bin/env python3
import argparse,json
from urllib.request import Request,urlopen
def call(base,method,path,body=None):
    data=None if body is None else json.dumps(body).encode()
    req=Request(base.rstrip('/')+path,data=data,method=method,headers={"Content-Type":"application/json"})
    with urlopen(req) as r:return json.load(r)
def main():
    p=argparse.ArgumentParser();p.add_argument("--base",default="http://127.0.0.1:8765")
    s=p.add_subparsers(dest="cmd",required=True);s.add_parser("health");s.add_parser("w114");src=s.add_parser("sources");src.add_argument("q",nargs="?",default="");src.add_argument("--limit",type=int,default=100)
    q=s.add_parser("search");q.add_argument("q");q.add_argument("--limit",type=int,default=20)
    o=s.add_parser("object");o.add_argument("id");a=p.parse_args()
    if a.cmd=="health":x=call(a.base,"GET","/v1/health")
    elif a.cmd=="w114":x=call(a.base,"GET","/v1/hodge/w114")
    elif a.cmd=="search":x=call(a.base,"POST","/v1/search",{"q":a.q,"limit":a.limit})
    elif a.cmd=="sources":x=call(a.base,"POST","/v1/hodge/sources/search",{"q":a.q,"limit":a.limit})
    else:x=call(a.base,"GET","/v1/objects/"+a.id)
    print(json.dumps(x,indent=2,sort_keys=True))
if __name__=="__main__":main()
