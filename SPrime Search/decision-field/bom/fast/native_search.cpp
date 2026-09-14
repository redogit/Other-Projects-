#include <algorithm>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <vector>
using U=uint64_t;
struct Solver{
  int n; U required; std::vector<U> provide, require; std::vector<int> order; std::vector<U> suffix;
  int best; U bestmask; uint64_t expansions=0;
  Solver(int n_,U r,std::vector<U> p,std::vector<U> q):n(n_),required(r),provide(std::move(p)),require(std::move(q)),best(n_+1),bestmask(0){
    order.resize(n); std::iota(order.begin(),order.end(),0);
    std::stable_sort(order.begin(),order.end(),[&](int a,int b){
      auto ga=__builtin_popcountll(provide[a]&required), gb=__builtin_popcountll(provide[b]&required);
      if(ga!=gb) return ga>gb; return a<b;
    });
    suffix.assign(n+1,0); for(int j=n-1;j>=0;--j) suffix[j]=suffix[j+1]|provide[order[j]];
  }
  void rec(int j,U selected,U provided,U needed,int count){
    ++expansions;
    if((needed & ~provided)==0){ if(count<best || (count==best && selected<bestmask)){best=count;bestmask=selected;} return; }
    if(j==n || count>=best) return;
    U missing=needed & ~provided; if(missing & ~(provided|suffix[j])) return;
    int s=order[j]; U bit=U(1)<<s;
    rec(j+1,selected|bit,provided|provide[s],needed|require[s],count+1);
    rec(j+1,selected,provided,needed,count);
  }
};
int main(){
  int n; U required; if(!(std::cin>>n>>required)) return 2;
  if(n<1 || n>64) return 3;
  std::vector<U> p(n),q(n); for(int i=0;i<n;++i) if(!(std::cin>>p[i]>>q[i])) return 4;
  Solver s(n,required,p,q); s.rec(0,0,0,required,0);
  if(s.best==n+1) std::cout<<"{\"count\":-1,\"mask\":0,\"expansions\":"<<s.expansions<<"}\n";
  else std::cout<<"{\"count\":"<<s.best<<",\"mask\":"<<s.bestmask<<",\"expansions\":"<<s.expansions<<"}\n";
}
