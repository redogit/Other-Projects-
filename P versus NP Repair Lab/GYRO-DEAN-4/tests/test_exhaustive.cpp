#include "gyro/solver.hpp"
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <vector>

static std::vector<std::pair<std::size_t,std::size_t>> edge_list(std::size_t n){
    std::vector<std::pair<std::size_t,std::size_t>> e;
    for(std::size_t i=0;i<n;++i) for(std::size_t j=i+1;j<n;++j) e.emplace_back(i,j);
    return e;
}

static std::size_t brute_count_q(const gyro::BitGraph& g,std::size_t q){
    const std::size_t n=g.size();
    std::size_t count=0;
    const std::uint64_t lim=1ULL<<n;
    for(std::uint64_t mask=0;mask<lim;++mask){
        if(std::popcount(mask)!=static_cast<int>(q)) continue;
        std::vector<std::size_t> v;
        for(std::size_t i=0;i<n;++i) if((mask>>i)&1ULL) v.push_back(i);
        if(g.is_independent(v)){
            ++count;
            if(count>=4) return 4;
        }
    }
    return count;
}

int main(){
    std::size_t cases=0;
    for(std::size_t n=1;n<=5;++n){
        auto edges=edge_list(n);
        const std::uint64_t graph_count=1ULL<<edges.size();
        for(std::uint64_t gm=0;gm<graph_count;++gm){
            gyro::BitGraph g(n);
            for(std::size_t e=0;e<edges.size();++e)
                if((gm>>e)&1ULL) g.add_edge(edges[e].first,edges[e].second);
            gyro::Solver s(g);
            for(std::size_t q=1;q<=n;++q){
                const auto want=brute_count_q(g,q);
                const auto one=s.find_one(q);
                assert(one.exists==(want>0));
                if(one.exists) assert(s.verify(one.witness,q,q));
                const auto four=s.find_up_to_four(q,q);
                assert(four.size()==want);
                for(const auto& w:four) assert(s.verify(w,q,q));
                for(std::size_t i=0;i<four.size();++i){
                    auto a=four[i]; std::sort(a.begin(),a.end());
                    for(std::size_t j=i+1;j<four.size();++j){
                        auto b=four[j]; std::sort(b.begin(),b.end());
                        assert(a!=b);
                    }
                }
                ++cases;
            }
        }
    }
    std::cout << "exhaustive labeled graphs n<=5: " << cases << " graph/target cases passed\n";
}
