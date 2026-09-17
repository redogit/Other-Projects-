#include "gyro/solver.hpp"
#include <cassert>
#include <iostream>

int main(){
    {
        gyro::BitGraph g(6); // C6; alpha=3
        for(std::size_t i=0;i<6;++i) g.add_edge(i,(i+1)%6);
        gyro::Solver s(g);
        auto r=s.find_one(3);
        assert(r.exists && r.witness.size()==3 && s.verify(r.witness,3,3));
        assert(!s.find_one(4).exists);
    }
    {
        gyro::BitGraph g(5); // empty graph, many 3-sets; should find four
        gyro::Solver s(g);
        auto rs=s.find_up_to_four(3,3);
        assert(rs.size()==4);
        for(auto& r:rs) assert(s.verify(r,3,3));
    }
    {
        gyro::BitGraph g(4); // K4; alpha=1
        for(std::size_t i=0;i<4;++i) for(std::size_t j=i+1;j<4;++j) g.add_edge(i,j);
        gyro::Solver s(g);
        assert(s.find_one(1).exists);
        assert(!s.find_one(2).exists);
    }

    {
        // 20-vertex cubic calibration core: alpha=8.
        gyro::BitGraph g(20);
        const std::size_t edges[][2] = {
            {0,9},{0,10},{0,19},{1,5},{1,17},{1,19},{2,5},{2,7},{2,8},
            {3,4},{3,6},{3,8},{4,11},{4,15},{5,12},{6,7},{6,18},{7,14},
            {8,9},{9,16},{10,13},{10,16},{11,18},{11,19},{12,13},{12,14},
            {13,18},{14,15},{15,17},{16,17}
        };
        for(const auto& e:edges) g.add_edge(e[0],e[1]);
        gyro::Solver s(g);
        auto r=s.find_one(8);
        assert(r.exists && s.verify(r.witness,8,8));
        assert(!s.find_one(9).exists);
    }

    std::cout<<"all tests passed\n";
}
