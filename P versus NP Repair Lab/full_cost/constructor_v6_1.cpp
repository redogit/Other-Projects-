// Exact finite NAND DAG / symmetry-selector audit. No external dependencies.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <map>
#include <numeric>
#include <set>
#include <stdexcept>
#include <string>
#include <sys/resource.h>
#include <tuple>
#include <unordered_set>
#include <vector>
using namespace std;
using Clock=chrono::steady_clock;
double elapsed(Clock::time_point a){return chrono::duration<double,milli>(Clock::now()-a).count();}
using Counts=map<string,uint64_t>;
struct State{array<uint16_t,6> a{};uint8_t n=0;bool operator==(State const&o)const{return n==o.n&&a==o.a;}};
struct Hash{size_t operator()(State const&s)const noexcept{size_t h=s.n;for(int i=0;i<s.n;++i)h=h*1000003^s.a[i];return h;}};
struct Context{int n,g,p;uint16_t mask;vector<uint16_t> vars;Context(int nv,int gates):n(nv),g(gates),p(1<<nv),mask(uint16_t((1u<<p)-1)){for(int j=0;j<n;++j){uint16_t v=0;for(int x=0;x<p;++x)if(x>>j&1)v|=uint16_t(1u<<x);vars.push_back(v);}}};
struct ClassResult{vector<uint16_t> funcs;vector<uint64_t> states;Counts counts;};
ClassResult build_class(Context const&c){
 ClassResult r;vector<State> cur(1);set<uint16_t> funcs(c.vars.begin(),c.vars.end());r.states.push_back(1);
 for(int d=1;d<=c.g;++d){unordered_set<State,Hash> next;
  for(auto const&s:cur){array<uint16_t,10> sig{};int m=0;for(auto v:c.vars)sig[m++]=v;for(int i=0;i<s.n;++i)sig[m++]=s.a[i];
   for(int i=0;i<m;++i)for(int j=i;j<m;++j){++r.counts["nand_candidate_evaluations"];uint16_t f=uint16_t(~(sig[i]&sig[j]))&c.mask;bool exists=false;for(int k=0;k<m;++k){++r.counts["duplicate_signal_comparisons"];if(sig[k]==f){exists=true;break;}}if(exists){++r.counts["duplicate_signal_candidates_skipped"];continue;}
    funcs.insert(f);State t=s;if(t.n>=t.a.size())throw runtime_error("state capacity exceeded");int pos=t.n++;while(pos>0&&t.a[pos-1]>f){t.a[pos]=t.a[pos-1];--pos;}t.a[pos]=f;++r.counts["state_insert_attempts"];next.insert(t);
   }
  }
  r.states.push_back(next.size());cur.assign(next.begin(),next.end());
 }
 r.funcs.assign(funcs.begin(),funcs.end());return r;
}
// Independent enumerator: syntactic gate sequences, including redundant gates,
// with no semantic-state merging. Every prefix contributes its output functions.
vector<uint16_t> syntactic_class(Context const&c,uint64_t&visits){
 set<uint16_t> found(c.vars.begin(),c.vars.end());vector<uint16_t> signals=c.vars;
 function<void(int)> visit=[&](int d){if(d==c.g)return;int m=signals.size();for(int i=0;i<m;++i)for(int j=i;j<m;++j){++visits;uint16_t f=uint16_t(~(signals[i]&signals[j]))&c.mask;found.insert(f);signals.push_back(f);visit(d+1);signals.pop_back();}};visit(0);return vector<uint16_t>(found.begin(),found.end());
}
struct Perm{array<int,16> map{};};
vector<Perm> permutations(Context const&c){vector<int>a(c.n);iota(a.begin(),a.end(),0);vector<Perm> ps;do{Perm q;for(int x=0;x<c.p;++x){int y=0;for(int j=0;j<c.n;++j)if(x>>j&1)y|=1<<a[j];q.map[x]=y;}ps.push_back(q);}while(next_permutation(a.begin(),a.end()));return ps;}
struct Index{
 int N,W,P;vector<array<vector<uint64_t>,2>> mask;
 Index(vector<uint16_t>const&f,int p):N(f.size()),W((N+63)/64),P(p),mask(p){for(int x=0;x<P;++x)for(int b=0;b<2;++b)mask[x][b].assign(W,0);for(int i=0;i<N;++i)for(int x=0;x<P;++x)mask[x][f[i]>>x&1][i>>6]|=1ull<<(i&63);}
 uint64_t payload_bytes()const{return uint64_t(P)*2*W*sizeof(uint64_t);}
 uint64_t accounted_capacity_bytes()const{uint64_t sum=sizeof(*this)+mask.capacity()*sizeof(mask[0]);for(auto const&a:mask)for(auto const&v:a)sum+=v.capacity()*sizeof(uint64_t);return sum;}
 long count(vector<uint64_t>const&s,int x,int y,int b,Counts&k)const{long result=0;for(int w=0;w<W;++w){uint64_t z=s[w]&mask[x][b][w];++k["score_and_word_ops"];if(y>=0){z&=mask[y][b][w];++k["score_and_word_ops"];}result+=__builtin_popcountll(z);++k["score_popcount_word_calls"];}return result;}
 void apply(vector<uint64_t>&s,int x,int y,int b,Counts&k)const{for(int w=0;w<W;++w){s[w]&=mask[x][b][w];++k["application_and_word_ops"];if(y>=0){s[w]&=mask[y][b][w];++k["application_and_word_ops"];}++k["application_word_stores"];}}
 long pop(vector<uint64_t>const&s,Counts&k)const{long result=0;for(auto z:s){result+=__builtin_popcountll(z);++k["survivor_popcount_word_calls"];}return result;}
};
using Obs=array<int,16>;
vector<int> stabilizer(vector<Perm>const&ps,Obs const&o,int p,int t,Counts&k){vector<int> group;for(int i=0;i<int(ps.size());++i){++k["stabilizer_permutations_examined"];bool ok=true;for(int x=0;x<p;++x){++k["stabilizer_coordinate_checks"];if(o[x]>=0){++k["stabilizer_observation_comparisons"];if(o[ps[i].map[x]]!=o[x]){ok=false;break;}}}if(ok&&t>=0){++k["stabilizer_translation_checks"];ok=ps[i].map[t]==t;}if(ok)group.push_back(i);}return group;}
vector<int> representatives(vector<Perm>const&ps,vector<int>const&group,Obs const&o,int p,int t,Counts&k){array<bool,16> seen{};vector<int> reps;for(int x=0;x<p;++x){++k["orbit_coordinates_examined"];if(t>=0&&x>(x^t))continue;if(seen[x]||o[x]>=0||(t>=0&&o[x^t]>=0))continue;int rep=x;for(int gi:group){++k["orbit_map_applications"];int y=ps[gi].map[x];if(t>=0){++k["orbit_pair_canonicalizations"];y=min(y,y^t);}if(o[y]<0&&(t<0||o[y^t]<0)){seen[y]=true;rep=min(rep,y);}}seen[x]=true;reps.push_back(rep);}sort(reps.begin(),reps.end());k["orbit_representatives"]+=reps.size();return reps;}
struct Step{int x,b;};
struct Route{string name;int t=-1,obs=0;Counts counts;vector<long>path;vector<Step>picks;vector<int>groups,reps;bool eliminated=false;double planning_ms=0,verification_ms=0;uint64_t verification_reads=0;};
Route plan(Index const&idx,vector<Perm>const&ps,int t){auto start=Clock::now();Route r;r.t=t;r.name=t<0?"generic_sym":"paired_t"+to_string(t);Obs o;o.fill(-1);vector<uint64_t>s(idx.W,~0ull);if(idx.N%64)s.back()=(1ull<<(idx.N%64))-1;r.path.push_back(idx.N);
 // Retain v5's while-condition and after-step popcount calls so their cost is visible.
 while(idx.pop(s,r.counts)>0){auto group=stabilizer(ps,o,idx.P,t,r.counts);auto reps=representatives(ps,group,o,idx.P,t,r.counts);if(reps.empty())break;r.groups.push_back(group.size());r.reps.push_back(reps.size());tuple<long,int,int>best={numeric_limits<long>::max(),-1,-1};for(int x:reps)for(int b=0;b<2;++b){++r.counts["candidate_scores"];long score=idx.count(s,x,t<0?-1:x^t,b,r.counts);best=min(best,tuple<long,int,int>{score,x,b});}auto [count,x,b]=best;(void)count;o[x]=b;if(t>=0)o[x^t]=b;idx.apply(s,x,t<0?-1:x^t,b,r.counts);r.obs+=t<0?1:2;r.picks.push_back({x,b});r.path.push_back(idx.pop(s,r.counts));if(!r.path.back())break;}
 r.eliminated=r.path.back()==0;r.planning_ms=elapsed(start);return r;
}
void verify_route(Route&r,vector<uint16_t>const&f,int p){auto start=Clock::now();vector<uint16_t>survivors=f;Obs o;o.fill(-1);if(r.path.empty()||r.path[0]!=long(f.size()))throw runtime_error("initial path mismatch");
 for(size_t step=0;step<r.picks.size();++step){auto chosen=r.picks[step];tuple<long,int,int>best={numeric_limits<long>::max(),-1,-1};
  // Exhaustively score ALL available actions, not orbit representatives or bitsets.
  for(int x=0;x<p;++x){if(o[x]>=0||(r.t>=0&&(x>(x^r.t)||o[x^r.t]>=0)))continue;for(int b=0;b<2;++b){long count=0;for(auto table:survivors){++r.verification_reads;bool ok=(table>>x&1)==b;if(r.t>=0){++r.verification_reads;bool second=((table>>(x^r.t)&1)==b);ok=ok&second;}if(ok)++count;}best=min(best,tuple<long,int,int>{count,x,b});}}
  auto [count,x,b]=best;if(x!=chosen.x||b!=chosen.b)throw runtime_error("full-action scalar greedy choice mismatch");o[x]=b;if(r.t>=0)o[x^r.t]=b;vector<uint16_t>next;for(auto table:survivors){++r.verification_reads;bool ok=(table>>x&1)==b;if(r.t>=0){++r.verification_reads;bool second=((table>>(x^r.t)&1)==b);ok=ok&second;}if(ok)next.push_back(table);}survivors.swap(next);if(long(survivors.size())!=r.path[step+1]||count!=r.path[step+1])throw runtime_error("scalar path mismatch");}
 if(r.eliminated!=survivors.empty()){throw runtime_error("certificate status mismatch");}
 r.verification_ms=elapsed(start);
}
void print_counts(ostream&o,Counts const&v){o<<'{';bool comma=false;for(auto const&[key,value]:v){if(comma)o<<',';comma=true;o<<'"'<<key<<"\":"<<value;}o<<'}';}
template<class T>void print_vector(ostream&o,vector<T>const&v){o<<'[';for(size_t i=0;i<v.size();++i){if(i)o<<',';o<<v[i];}o<<']';}
int main(int argc,char**argv){try{if(argc!=4)throw runtime_error("usage: constructor N GATES OUTPUT.json");int n=stoi(argv[1]),g=stoi(argv[2]);if(n<2||n>4||g<0||g>6)throw runtime_error("bounds: 2<=n<=4, 0<=gates<=6");Context c(n,g);auto total=Clock::now(),start=Clock::now();auto built=build_class(c);double build_ms=elapsed(start);start=Clock::now();Index idx(built.funcs,c.p);double index_ms=elapsed(start);start=Clock::now();auto ps=permutations(c);double permutation_ms=elapsed(start);vector<Route>routes;routes.push_back(plan(idx,ps,-1));for(int w=1;w<=n;++w)routes.push_back(plan(idx,ps,(1<<w)-1));
 start=Clock::now();uint64_t visits=0;bool class_crosscheck=n<=3;if(class_crosscheck&&syntactic_class(c,visits)!=built.funcs)throw runtime_error("syntactic class cross-check failed");double class_verification_ms=elapsed(start);
 start=Clock::now();uint64_t closure_checks=0;for(auto f:built.funcs)for(auto const&p:ps){uint16_t image=0;for(int x=0;x<c.p;++x)if(f>>x&1)image|=uint16_t(1u<<p.map[x]);if(!binary_search(built.funcs.begin(),built.funcs.end(),image))throw runtime_error("permutation closure failed");++closure_checks;}for(int w=1;w<=n;++w){Counts k;Obs o;o.fill(-1);int t=(1<<w)-1;auto group=stabilizer(ps,o,c.p,t,k);auto reps=representatives(ps,group,o,c.p,t,k);if(int(reps.size())!=(w/2+1)*(n-w+1))throw runtime_error("initial pair orbit formula failed");}double symmetry_verification_ms=elapsed(start);for(auto&r:routes)verify_route(r,built.funcs,c.p);
 // Exact n=4,g=6 historical calibration: scores, charged AND words, survivor paths.
 bool calibration=n==4&&g==6;if(calibration){vector<vector<long>> paths={{3310,1371,417,90,1,0},{3310,790,160,45,10,0},{3310,582,32,0},{3310,500,21,0},{3310,548,78,7,0}};vector<int> scores={56,30,30,22,20},ops={2912,3120,3120,2288,2080};for(size_t i=0;i<routes.size();++i)if(routes[i].path!=paths[i]||routes[i].counts["candidate_scores"]!=uint64_t(scores[i])||routes[i].counts["score_and_word_ops"]!=uint64_t(ops[i]))throw runtime_error("v5 calibration failed");}
 ofstream out(argv[3]);if(!out)throw runtime_error("cannot write result");out.precision(12);out<<"{\"n\":"<<n<<",\"gate_budget\":"<<g<<",\"class_size\":"<<built.funcs.size()<<",\"truth_tables\":";print_vector(out,built.funcs);out<<",\"states_by_distinct_gate_signals\":";print_vector(out,built.states);out<<",\"construction_counts\":";print_counts(out,built.counts);out<<",\"index\":{\"words_per_survivor_mask\":"<<idx.W<<",\"mask_payload_bytes\":"<<idx.payload_bytes()<<",\"accounted_capacity_bytes\":"<<idx.accounted_capacity_bytes()<<",\"allocator_metadata_excluded\":true},\"permutations\":"<<ps.size()<<",\"timing_ms\":{\"build_class\":"<<build_ms<<",\"build_index\":"<<index_ms<<",\"build_permutations\":"<<permutation_ms<<",\"independent_class_verification\":"<<class_verification_ms<<",\"symmetry_verification\":"<<symmetry_verification_ms<<"},\"verification\":{\"syntactic_class_crosscheck\":"<<(class_crosscheck?"true":"false")<<",\"syntactic_gate_candidates\":"<<visits<<",\"permutation_closure_checks\":"<<closure_checks<<",\"all_actions_scalar_score_and_path_check\":true,\"initial_pair_orbit_formula\":true,\"historical_v5_calibration\":"<<(calibration?"true":"false")<<"},\"routes\":[";
 for(size_t i=0;i<routes.size();++i){if(i)out<<',';auto const&r=routes[i];out<<"{\"name\":\""<<r.name<<"\",\"translation\":"<<r.t<<",\"observations\":"<<r.obs<<",\"eliminated_class\":"<<(r.eliminated?"true":"false")<<",\"path\":";print_vector(out,r.path);out<<",\"picks\":[";for(size_t j=0;j<r.picks.size();++j){if(j)out<<',';out<<'['<<r.picks[j].x<<','<<r.picks[j].b<<']';}out<<"],\"stabilizer_sizes\":";print_vector(out,r.groups);out<<",\"representative_counts\":";print_vector(out,r.reps);out<<",\"counts\":";print_counts(out,r.counts);out<<",\"planning_ms\":"<<r.planning_ms<<",\"scalar_verification_ms\":"<<r.verification_ms<<",\"scalar_verification_bit_reads\":"<<r.verification_reads<<'}';}
 struct rusage ru{};getrusage(RUSAGE_SELF,&ru);out<<"],\"peak_rss_kib\":"<<ru.ru_maxrss<<",\"total_before_serialization_end_ms\":"<<elapsed(total)<<"}\n";out.close();if(!out)throw runtime_error("result write failed");cout<<"n="<<n<<" gates="<<g<<" class="<<built.funcs.size()<<" checks=pass\n";return 0;
 }catch(exception const&e){cerr<<e.what()<<'\n';return 1;}}
