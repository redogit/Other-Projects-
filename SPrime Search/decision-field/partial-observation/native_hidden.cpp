#include <array>
#include <cstdint>
#include <iostream>
using namespace std;
struct Sys{array<array<int,8>,4> t;array<int,8> obs;};
Sys make(){Sys s{};for(int m=0;m<2;m++)for(int p=0;p<4;p++){int w=4*m+p;s.obs[w]=p;s.t[0][w]=4*m+((p==0)?(m?2:1):p);s.t[1][w]=4*m+((p==1||p==2)?0:p);s.t[2][w]=4*m+((p==0)?(m?1:3):p);s.t[3][w]=4*m+((p==0)?(m?3:1):p);}return s;}
void decode(uint64_t code,int q,int action[3][4],int upd[3][4]){uint64_t base=4*q;for(int m=0;m<q;m++)for(int o=0;o<4;o++){int d=code%base;code/=base;action[m][o]=d%4;upd[m][o]=d/4;}}
bool wins(const Sys&s,int q,uint64_t code){int action[3][4]{},upd[3][4]{};decode(code,q,action,upd);for(int start:{0,4}){int w=start,m=0;bool seen[24]{};bool hit=false;for(int step=0;step<24;step++){if((w%4)==3){hit=true;break;}int key=8*m+w;if(seen[key])break;seen[key]=true;int o=s.obs[w];int a=action[m][o];int nm=upd[m][o];w=s.t[a][w];m=nm;}if(!hit)return false;}return true;}
int main(){auto s=make();uint64_t counts[3]{},totals[3]{},first[3]{};for(int q=1;q<=2;q++){uint64_t base=4*q,total=1;for(int i=0;i<4*q;i++)total*=base;totals[q]=total;for(uint64_t code=0;code<total;code++)if(wins(s,q,code)){if(!counts[q])first[q]=code;counts[q]++;}}
 int action[3][4]{},upd[3][4]{};decode(first[2],2,action,upd);
 cout<<"{\n  \"q1_total\":"<<totals[1]<<",\n  \"q1_winning\":"<<counts[1]<<",\n  \"q2_total\":"<<totals[2]<<",\n  \"q2_winning\":"<<counts[2]<<",\n  \"first_q2_code\":"<<first[2]<<",\n  \"first_q2_actions\":[[";
 for(int o=0;o<4;o++){if(o)cout<<",";cout<<action[0][o];}cout<<"],[";for(int o=0;o<4;o++){if(o)cout<<",";cout<<action[1][o];}cout<<"]],\n  \"first_q2_updates\":[[";for(int o=0;o<4;o++){if(o)cout<<",";cout<<upd[0][o];}cout<<"],[";for(int o=0;o<4;o++){if(o)cout<<",";cout<<upd[1][o];}cout<<"]]\n}\n";}
