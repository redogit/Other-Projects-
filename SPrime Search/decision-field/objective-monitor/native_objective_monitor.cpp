#include <array>
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <queue>
#include <tuple>

using Map = std::array<int,4>;

static Map decode(int code) {
    Map out{};
    for (int i=0;i<4;i++) out[i]=(code>>(2*i))&3;
    return out;
}

struct CaseResult { int collisions=0; int min_radius=-1; int physical=-1; std::array<int,8> parent{}; std::array<int,8> parent_action{}; std::array<int,8> dist{}; };

static CaseResult initial_case(const Map& a, const Map& b, int initial) {
    std::array<int,8> dist; dist.fill(-1);
    std::array<int,8> parent; parent.fill(-1);
    std::array<int,8> parent_action; parent_action.fill(-1);
    auto index=[](int state,int seen){return state*2+seen;};
    const int start=index(initial, initial==1);
    std::queue<int> q; q.push(start); dist[start]=0;
    while(!q.empty()) {
        int cur=q.front(); q.pop();
        int state=cur/2, seen=cur%2;
        for(int ai=0;ai<2;ai++) {
            const Map& action= ai==0 ? a : b;
            int nxt=action[state], nseen=seen || nxt==1, ni=index(nxt,nseen);
            if(dist[ni]<0) { dist[ni]=dist[cur]+1; parent[ni]=cur; parent_action[ni]=ai; q.push(ni); }
        }
    }
    CaseResult out; out.parent=parent; out.parent_action=parent_action; out.dist=dist;
    for(int s=0;s<4;s++) {
        int d0=dist[index(s,0)], d1=dist[index(s,1)];
        if(d0>=0 && d1>=0) {
            out.collisions++;
            int radius=std::max(d0,d1);
            if(out.min_radius<0 || std::tie(radius,s)<std::tie(out.min_radius,out.physical)) { out.min_radius=radius; out.physical=s; }
        }
    }
    return out;
}

static void emit_word(const CaseResult& r, int target) {
    std::array<int,8> rev{}; int n=0, cur=target;
    while(r.parent[cur]>=0) { rev[n++]=r.parent_action[cur]; cur=r.parent[cur]; }
    std::cout << '[';
    for(int i=n-1;i>=0;i--) { if(i!=n-1) std::cout << ','; std::cout << rev[i]; }
    std::cout << ']';
}

int main() {
    long long systems_with=0, initial_with=0, collision_states=0;
    std::array<long long,5> by_collision_count{};
    std::array<long long,8> radius_dist{};
    bool have_witness=false; int w_l=0,w_r=0,w_i=0,w_p=0,w_rad=99; CaseResult w_case; Map w_a{},w_b{};
    for(int lc=0;lc<256;lc++) {
        Map a=decode(lc);
        for(int rc=0;rc<256;rc++) {
            Map b=decode(rc); bool system=false;
            for(int init=0;init<4;init++) {
                CaseResult r=initial_case(a,b,init);
                by_collision_count[r.collisions]++;
                if(!r.collisions) continue;
                system=true; initial_with++; collision_states+=r.collisions; radius_dist[r.min_radius]++;
                auto key=std::make_tuple(r.min_radius,lc,rc,init,r.physical);
                auto old=std::make_tuple(w_rad,w_l,w_r,w_i,w_p);
                if(!have_witness || key<old) { have_witness=true; w_rad=r.min_radius;w_l=lc;w_r=rc;w_i=init;w_p=r.physical;w_case=r;w_a=a;w_b=b; }
            }
            if(system) systems_with++;
        }
    }
    std::cout << "{\"status\":\"PASS_BOUNDED\",\"state_count\":4,\"action_count\":2,\"ordered_action_map_pairs\":65536,\"initial_state_cases\":262144,\"tracked_state\":1";
    std::cout << ",\"systems_with_monitor_collision\":"<<systems_with;
    std::cout << ",\"initial_cases_with_monitor_collision\":"<<initial_with;
    std::cout << ",\"collision_physical_states\":"<<collision_states;
    std::cout << ",\"minimum_certificate_radius_distribution\":{";
    bool first=true; for(int i=0;i<(int)radius_dist.size();i++) if(radius_dist[i]) { if(!first) std::cout<<','; first=false; std::cout<<'\"'<<i<<"\":"<<radius_dist[i]; }
    std::cout << "},\"initial_cases_by_colliding_state_count\":{";
    first=true; for(int i=0;i<5;i++) { if(!first) std::cout<<','; first=false; std::cout<<'\"'<<i<<"\":"<<by_collision_count[i]; }
    std::cout << "},\"maximum_minimum_certificate_radius\":";
    int maxrad=-1; for(int i=0;i<(int)radius_dist.size();i++) if(radius_dist[i]) maxrad=i; std::cout<<maxrad;
    std::cout << ",\"witness\":{\"left_code\":"<<w_l<<",\"right_code\":"<<w_r<<",\"left_map\":["<<w_a[0]<<','<<w_a[1]<<','<<w_a[2]<<','<<w_a[3]<<"],\"right_map\":["<<w_b[0]<<','<<w_b[1]<<','<<w_b[2]<<','<<w_b[3]<<"],\"initial_state\":"<<w_i<<",\"physical_state\":"<<w_p<<",\"radius\":"<<w_rad<<",\"word_without_visit\":";
    emit_word(w_case,w_p*2+0); std::cout << ",\"word_with_visit\":"; emit_word(w_case,w_p*2+1); std::cout << "}}\n";
    return 0;
}
