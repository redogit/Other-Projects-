#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
using namespace std;

static array<int,4> tup(int b){ return {b&3,(b>>2)&3,(b>>4)&3,(b>>6)&3}; }
static int pack(const array<int,4>& a){ return a[0] | (a[1]<<2) | (a[2]<<4) | (a[3]<<6); }
static int comp(int after,int before){ auto a=tup(after),b=tup(before); return pack({a[b[0]],a[b[1]],a[b[2]],a[b[3]]}); }

static int fixed_safety(int a,int b,int safe,bool ctrl){
    auto A=tup(a),B=tup(b); int cur=safe;
    while(true){ int nxt=0;
        for(int s=0;s<4;s++) if(cur&(1<<s)){
            bool x=cur&(1<<A[s]), y=cur&(1<<B[s]);
            if(ctrl ? (x||y) : (x&&y)) nxt|=1<<s;
        }
        if(nxt==cur) return cur; cur=nxt;
    }
}
static int brute_safety(int a,int b,int safe,bool ctrl){
    auto A=tup(a),B=tup(b); int best=0;
    for(int sub=0;sub<16;sub++){
        if(sub & ~safe) continue; bool ok=true;
        for(int s=0;s<4 && ok;s++) if(sub&(1<<s)){
            bool x=sub&(1<<A[s]), y=sub&(1<<B[s]);
            ok = ctrl ? (x||y) : (x&&y);
        }
        if(ok) best|=sub;
    }
    return best;
}
static int fixed_reach(int a,int b,int target,bool ctrl){
    auto A=tup(a),B=tup(b); int cur=target;
    while(true){ int nxt=cur;
        for(int s=0;s<4;s++) if(!(cur&(1<<s))){
            bool x=cur&(1<<A[s]), y=cur&(1<<B[s]);
            if(ctrl ? (x||y) : (x&&y)) nxt|=1<<s;
        }
        if(nxt==cur) return cur; cur=nxt;
    }
}
static int bounded_reach(int a,int b,int target,bool ctrl){
    auto A=tup(a),B=tup(b); int cur=target;
    for(int step=0;step<4;step++){
        int nxt=cur;
        for(int s=0;s<4;s++) if(!(cur&(1<<s))){
            bool x=cur&(1<<A[s]), y=cur&(1<<B[s]);
            if(ctrl ? (x||y) : (x&&y)) nxt|=1<<s;
        }
        cur=nxt;
    }
    return cur;
}
int main(){
    static uint8_t C[256][256];
    uint64_t pairs=0, triples=0, game_cases=0;
    for(int a=0;a<256;a++) for(int b=0;b<256;b++){ C[a][b]=comp(a,b); pairs++; }
    const int I=0xe4;
    for(int x=0;x<256;x++) if(C[I][x]!=x || C[x][I]!=x) throw runtime_error("identity");
    for(int a=0;a<256;a++) for(int b=0;b<256;b++) for(int c=0;c<256;c++){
        if(C[C[a][b]][c] != C[a][C[b][c]]) throw runtime_error("assoc"); triples++;
    }
    for(int a=0;a<256;a++) for(int b=0;b<256;b++) for(int mask=0;mask<16;mask++){
        for(bool ctrl: {false,true}){
            if(fixed_safety(a,b,mask,ctrl)!=brute_safety(a,b,mask,ctrl)) throw runtime_error("safety");
            if(fixed_reach(a,b,mask,ctrl)!=bounded_reach(a,b,mask,ctrl)) throw runtime_error("reach");
        }
        game_cases++;
    }
    cout << "{\"status\":\"PASS\",\"composition_pairs\":"<<pairs
         <<",\"associativity_triples\":"<<triples
         <<",\"ordered_map_pair_mask_game_cases\":"<<game_cases<<"}\n";
}
