#include <array>
#include <cstdint>
#include <iostream>
#include <vector>
#include <map>
#include <tuple>
#include <algorithm>
using Map=std::array<int,4>;
struct Part{std::array<int,4> p; int profile;};
Map mt(int b){Map f{}; for(int s=0;s<4;s++) f[s]=(b>>(2*s))&3; return f;}
std::vector<Part> parts2(){
 std::vector<Part> out; std::array<int,4>a{0,0,0,0};
 auto rec=[&](auto&& self,int i,int mx)->void{ if(i==4){ if(mx==1){int c0=0; for(int x:a)c0+=x==0; int c1=4-c0; out.push_back({a,std::max(c0,c1)==3?31:22});} return;} for(int x=0;x<=mx+1;x++){a[i]=x;self(self,i+1,std::max(mx,x));}};
 rec(rec,1,0); return out;
}
bool win_q1(const Map&a,const Map&b,int t,const Part&p,int code){
 for(int start=0;start<4;start++){int s=start; bool seen[4]{}; while(s!=t&&!seen[s]){seen[s]=true; int act=(code>>p.p[s])&1; s=(act?b:a)[s];} if(s!=t)return false;} return true;
}
bool exists_q1(const Map&a,const Map&b,int t,const Part&p,int* witness=nullptr){ for(int code=0;code<4;code++) if(win_q1(a,b,t,p,code)){if(witness)*witness=code;return true;}return false;}
bool win_q2(const Map&a,const Map&b,int t,const Part&p,int code){
 for(int start=0;start<4;start++){int s=start,m=0; bool seen[8]{}; while(s!=t&&!seen[2*s+m]){seen[2*s+m]=true; int cell=2*m+p.p[s]; int v=(code>>(2*cell))&3; int act=v&1,nm=(v>>1)&1; s=(act?b:a)[s];m=nm;} if(s!=t)return false;} return true;
}
bool exists_q2(const Map&a,const Map&b,int t,const Part&p,int* witness=nullptr){ for(int code=0;code<256;code++) if(win_q2(a,b,t,p,code)){if(witness)*witness=code;return true;}return false;}
std::string partstr(const std::array<int,4>&p){std::string s="[";for(int i=0;i<4;i++){if(i)s+=",";s+=char('0'+p[i]);}return s+"]";}
int main(){auto P=parts2(); if(P.size()!=7)return 2;
 uint64_t systems=0,cases=0,q1wins=0,q2wins=0,rescues=0,systems_rescue=0,rescue31=0,rescue22=0;
 std::map<int,uint64_t> rescue_count_dist; bool have=false; int wt=0,wb0=0,wb1=0,wcode=0;Part wp{};Map wa{},wb{};
 for(int t=0;t<4;t++){std::vector<int> bs;for(int x=0;x<256;x++)if(mt(x)[t]==t)bs.push_back(x);for(int b0:bs)for(int b1:bs){systems++;auto a=mt(b0),b=mt(b1);int rc=0;for(const auto&p:P){cases++;bool q1=exists_q1(a,b,t,p);if(q1){q1wins++;q2wins++;continue;}int code=-1;bool q2=exists_q2(a,b,t,p,&code);if(q2){q2wins++;rescues++;rc++;if(p.profile==31)rescue31++;else rescue22++;auto key=std::make_tuple(t,b0,b1,p.p);if(!have || key<std::make_tuple(wt,wb0,wb1,wp.p)){have=true;wt=t;wb0=b0;wb1=b1;wp=p;wcode=code;wa=a;wb=b;}}}rescue_count_dist[rc]++;if(rc)systems_rescue++;}}
 std::cout<<"{\"status\":\"PASS_BOUNDED\",\"systems\":"<<systems<<",\"two_class_partitions\":7,\"sensor_cases\":"<<cases<<",\"memoryless_winning_sensor_cases\":"<<q1wins<<",\"two_state_memory_winning_sensor_cases\":"<<q2wins<<",\"memory_rescued_sensor_cases\":"<<rescues<<",\"systems_with_memory_rescue\":"<<systems_rescue<<",\"rescues_by_profile\":{\"3+1\":"<<rescue31<<",\"2+2\":"<<rescue22<<"},\"rescue_count_distribution\":{";
 bool first=true;for(auto [k,v]:rescue_count_dist){if(!first)std::cout<<',';first=false;std::cout<<'\"'<<k<<"\":"<<v;}std::cout<<"},\"witness\":{";
 std::cout<<"\"target\":"<<wt<<",\"map0_code\":"<<wb0<<",\"map1_code\":"<<wb1<<",\"map0\":["<<wa[0]<<','<<wa[1]<<','<<wa[2]<<','<<wa[3]<<"],\"map1\":["<<wb[0]<<','<<wb[1]<<','<<wb[2]<<','<<wb[3]<<"],\"partition\":"<<partstr(wp.p)<<",\"profile\":\""<<(wp.profile==31?"3+1":"2+2")<<"\",\"controller_code\":"<<wcode<<",\"controller_cells\":[";
 for(int cell=0;cell<4;cell++){if(cell)std::cout<<',';int v=(wcode>>(2*cell))&3;std::cout<<"{\"memory\":"<<(cell/2)<<",\"observation\":"<<(cell%2)<<",\"action\":"<<(v&1)<<",\"next_memory\":"<<((v>>1)&1)<<"}";}std::cout<<"]}}\n";
}
