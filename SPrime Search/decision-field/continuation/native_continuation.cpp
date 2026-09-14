#include <array>
#include <cstdint>
#include <iostream>
#include <map>
#include <queue>
#include <tuple>
#include <vector>
using namespace std;
array<int,4> mt(int b){array<int,4>f{};for(int s=0;s<4;s++)f[s]=(b>>(2*s))&3;return f;}
array<int,4> quotient(const vector<array<int,4>>&acts){array<int,4>lab{0,1,1,1};while(true){map<tuple<int,vector<int>>,int>d;array<int,4>nw{};for(int s=0;s<4;s++){vector<int>v;for(auto&a:acts)v.push_back(lab[a[s]]);auto key=make_tuple(s==0?1:0,v);if(!d.count(key))d[key]=d.size();nw[s]=d[key];}if(nw==lab)return lab;lab=nw;}}
bool refines(const array<int,4>&f,const array<int,4>&c){for(int i=0;i<4;i++)for(int j=0;j<4;j++)if(f[i]==f[j]&&c[i]!=c[j])return false;return true;}
int classes(const array<int,4>&q){int m=0;for(int x:q)m=max(m,x);return m+1;}
int distword(const vector<array<int,4>>&acts,int s,int t){if((s==0)!=(t==0))return 0;bool seen[4][4]{};queue<tuple<int,int,int>>q;q.push({s,t,0});seen[s][t]=1;while(!q.empty()){auto[a,b,d]=q.front();q.pop();for(auto&m:acts){int na=m[a],nb=m[b];if((na==0)!=(nb==0))return d+1;if(!seen[na][nb]){seen[na][nb]=1;q.push({na,nb,d+1});}}}return -1;}
int main(){map<pair<int,int>,uint64_t>dist;uint64_t split=0,pairs=0;map<int,uint64_t>wdist;int maxd=0;bool witness=false;array<int,4>wa{},wb{},wo{},wn{};int ws=0,wt=0;
for(int a=0;a<256;a++){auto A=mt(a);auto oldq=quotient({A});for(int b=0;b<256;b++){auto B=mt(b);auto newq=quotient({A,B});int co=classes(oldq),cn=classes(newq);dist[{co,cn}]++;if(!refines(newq,oldq))return 2;if(cn>co)split++;for(int s=0;s<4;s++)for(int t=s+1;t<4;t++){int d=distword({A,B},s,t);bool eq=newq[s]==newq[t];if((d<0)!=eq)return 3;if(d>=0){wdist[d]++;maxd=max(maxd,d);if(d==2&&!witness){witness=true;wa=A;wb=B;wo=oldq;wn=newq;ws=s;wt=t;}}pairs++;}}}
if(split!=31488||pairs!=393216||maxd!=2)return 4;
cout<<"{\n  \"status\":\"PASS\",\n  \"systems\":65536,\n  \"state_pairs_checked\":"<<pairs<<",\n  \"action_expansion_strict_splits\":"<<split<<",\n  \"class_count_distribution\":{";bool first=true;for(auto&[k,v]:dist){if(!first)cout<<",";first=false;cout<<"\""<<k.first<<"->"<<k.second<<"\":"<<v;}cout<<"},\n  \"distinguishing_word_length_distribution\":{";first=true;for(auto&[k,v]:wdist){if(!first)cout<<",";first=false;cout<<"\""<<k<<"\":"<<v;}cout<<"},\n  \"maximum_shortest_distinguishing_word\":"<<maxd<<",\n  \"depth2_witness\":{\"action0\":[";for(int i=0;i<4;i++){if(i)cout<<",";cout<<wa[i];}cout<<"],\"action1\":[";for(int i=0;i<4;i++){if(i)cout<<",";cout<<wb[i];}cout<<"],\"old_quotient\":[";for(int i=0;i<4;i++){if(i)cout<<",";cout<<wo[i];}cout<<"],\"new_quotient\":[";for(int i=0;i<4;i++){if(i)cout<<",";cout<<wn[i];}cout<<"],\"states\":["<<ws<<","<<wt<<"],\"word\":[1,1]}\n}\n";}
