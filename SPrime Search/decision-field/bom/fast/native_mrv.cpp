#include <algorithm>
#include <cstdint>
#include <iostream>
#include <unordered_set>
#include <vector>
using U=uint64_t;
struct Solver{
  int n; U required; std::vector<U> provide, require; int best; U bestmask; uint64_t expansions=0,prunes=0,dead=0; std::unordered_set<U> seen;
  Solver(int n_,U r,std::vector<U> p,std::vector<U> q):n(n_),required(r),provide(std::move(p)),require(std::move(q)),best(n_+1),bestmask(0){}
  static int pc(U x){return __builtin_popcountll(x);} 
  void rec(U selected,U provided,U needed,int count){
    if(seen.find(selected)!=seen.end()) return; seen.insert(selected); ++expansions;
    U missing=needed & ~provided;
    if(!missing){ if(count<best || (count==best && selected<bestmask)){best=count;bestmask=selected;} return; }
    if(count>=best){++prunes; return;}
    std::vector<int> candidates; int maxNew=0;
    for(int i=0;i<n;++i) if(!(selected&(U(1)<<i)) && (provide[i]&missing)){candidates.push_back(i);maxNew=std::max(maxNew,pc(provide[i]&missing));}
    if(candidates.empty()){++dead;return;}
    int lower=(pc(missing)+maxNew-1)/maxNew; if(count+lower>best){++prunes;return;}
    int chosen=-1,bestProviders=n+1; std::vector<int> providers;
    for(int b=0;b<64;++b) if(missing&(U(1)<<b)){
      std::vector<int> ps; for(int i:candidates) if(provide[i]&(U(1)<<b)) ps.push_back(i);
      if(ps.empty()){++dead;return;}
      if((int)ps.size()<bestProviders){bestProviders=ps.size();chosen=b;providers=std::move(ps);} 
    }
    std::sort(providers.begin(),providers.end(),[&](int a,int b){
      int na=pc(provide[a]&missing), nb=pc(provide[b]&missing); if(na!=nb) return na>nb;
      int ra=pc(require[a]), rb=pc(require[b]); if(ra!=rb) return ra<rb; return a<b;
    });
    for(int i:providers) rec(selected|(U(1)<<i),provided|provide[i],needed|require[i],count+1);
  }
};
int main(){int n;U required;if(!(std::cin>>n>>required))return 2;if(n<1||n>64)return 3;std::vector<U> p(n),q(n);for(int i=0;i<n;++i)if(!(std::cin>>p[i]>>q[i]))return 4;Solver s(n,required,p,q);s.rec(0,0,required,0);std::cout<<"{\"count\":"<<(s.best==n+1?-1:s.best)<<",\"mask\":"<<s.bestmask<<",\"expansions\":"<<s.expansions<<",\"prunes\":"<<s.prunes<<",\"dead\":"<<s.dead<<"}\n";}
