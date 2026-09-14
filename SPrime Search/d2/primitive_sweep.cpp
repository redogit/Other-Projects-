#include <array>
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <set>
#include <vector>
using U=uint8_t;
U apply(int op,U a,U b){U r=0;for(int i=0;i<8;i++){int av=(a>>i)&1,bv=(b>>i)&1;r|=((op>>(2*av+bv))&1)<<i;}return r;}
int main(int argc,char**argv){if(argc!=2)return 2; std::ofstream out(argv[1]);out<<"primitive\treachable_through_5\tcomplete\n";
  const int NAND=7; for(int p=0;p<16;p++){
    std::set<std::vector<U>> states; states.insert({170,204,240}); std::array<int,256> min;min.fill(-1);min[170]=min[204]=min[240]=0;
    for(int d=1;d<=5;d++){std::set<std::vector<U>> next;
      for(auto const&s:states){int n=s.size();for(int oi=0;oi<2;oi++){int op=oi?p:NAND;for(int a=0;a<n;a++)for(int b=0;b<n;b++){U v=apply(op,s[a],s[b]);if(std::find(s.begin(),s.end(),v)!=s.end())continue;auto ns=s;ns.push_back(v);std::sort(ns.begin(),ns.end());next.insert(ns);if(min[v]<0)min[v]=d;}}}states.swap(next);}int c=0;for(int v:min)if(v>=0)c++;out<<p<<"\t"<<c<<"\t"<<(c==256?1:0)<<"\n";}
}
