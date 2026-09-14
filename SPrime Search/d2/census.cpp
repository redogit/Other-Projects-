#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
using u64=uint64_t;
static std::array<std::array<u64,256>,6> counts{};
static std::array<int,256> shortest;
static std::array<std::string,256> witness;
static uint8_t regs_[16];
static uint8_t inst_[16];

__attribute__((noinline)) void dfs_exact(int d,int k){
  if(k<1 || k>5 || d<0 || d>k || d>5){std::abort();}
  if(d==k){
    uint8_t f=regs_[2+d]; counts[k][f]++;
    if(shortest[f]<0){shortest[f]=k; witness[f]=std::string(reinterpret_cast<char*>(inst_), k);} return;
  }
  int n=3+d;
  for(int op=0;op<2;op++) for(int a=0;a<8;a++){ if(a>=n) break; for(int b=0;b<8;b++){ if(b>=n) break;
    regs_[n]=op==0?uint8_t(255^(regs_[a]&regs_[b])):uint8_t(regs_[a]^regs_[b]);
    inst_[d]=uint8_t((op<<6)|(a<<3)|b); dfs_exact(d+1,k);
  }}
}
int main(int argc,char**argv){
  if(argc!=2){std::fprintf(stderr,"usage: census OUT.tsv\n"); return 2;}
  shortest.fill(-1); regs_[0]=240; regs_[1]=204; regs_[2]=170;
  shortest[240]=shortest[204]=shortest[170]=0;
  for(int k=1;k<=5;k++){dfs_exact(0,k); u64 total=0;int beh=0;for(auto c:counts[k]){total+=c;if(c)beh++;}
    std::fprintf(stderr,"k=%d total=%llu behavior=%d\n",k,(unsigned long long)total,beh);}
  std::ofstream out(argv[1]); out<<"table\tshortest_gates\twitness_payload_hex";for(int k=1;k<=5;k++)out<<"\tcount_k"<<k;out<<"\n";
  for(int f=0;f<256;f++){out<<f<<"\t"<<shortest[f]<<"\t";for(unsigned char c:witness[f]){char b[3];std::sprintf(b,"%02x",c);out<<b;}for(int k=1;k<=5;k++)out<<"\t"<<counts[k][f];out<<"\n";}
}
