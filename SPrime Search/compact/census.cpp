// Exhaust all D1 programs up to six NAND gates. No generated native code runs.
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>

using Counts = std::array<std::array<std::uint64_t,256>,7>;
static Counts counts{};
static std::array<std::string,256> witnesses{};
static std::array<unsigned,9> regs{{240,204,170,0,0,0,0,0,0}};
static std::string code = "D1";
static int cap = 6;

static void visit(int depth) {
    if (depth >= cap || depth >= 6) return;
    const int n = 3+depth;
    for (int a=0; a<n; ++a) {
        for (int b=0; b<n; ++b) {
            unsigned f = 255U ^ (regs[a] & regs[b]);
            ++counts[depth+1][f];
            regs[n] = f;
            code.push_back(static_cast<char>(32+8*a+b));
            if (witnesses[f].empty() || code.size() < witnesses[f].size())
                witnesses[f] = code;
            if (depth+1 < cap) visit(depth+1);
            code.pop_back();
        }
    }
}

static std::string hex(const std::string &s) {
    constexpr char digits[]="0123456789abcdef";
    std::string out;
    for (unsigned char c:s) {out+=digits[c>>4];out+=digits[c&15];}
    return out;
}

int main(int argc, char **argv) {
    try {
        if (argc>2) throw std::invalid_argument("usage: census [1..6]");
        if (argc==2) {
            std::string arg(argv[1]);
            if (arg.size()!=1 || arg[0]<'1' || arg[0]>'6')
                throw std::invalid_argument("gate bound must be 1..6");
            cap=arg[0]-'0';
        }
        for (int i=0;i<3;++i) {
            counts[0][regs[i]]=1;
            witnesses[regs[i]]=std::string("D1")+"xyz"[i];
        }
        visit(0);
        std::uint64_t expected=1;
        for (int k=0;k<=cap;++k) {
            if (k) expected*=static_cast<std::uint64_t>((k+2)*(k+2));
            std::uint64_t sum=0;for (auto x:counts[k])sum+=x;
            if (sum!=(k ? expected:3)) throw std::runtime_error("count oracle mismatch");
        }
        std::cout << "{\"format\":\"D1\",\"max_gates\":" << cap << ",\"counts_by_gates\":[";
        for (int k=0;k<=cap;++k) {
            if(k) std::cout << ',';
            std::cout << '[';
            for (int f=0;f<256;++f) {if(f)std::cout << ',';std::cout << counts[k][f];}
            std::cout << ']';
        }
        std::cout << "],\"shortest_hex_by_behavior\":[";
        for (int f=0;f<256;++f) {
            if(f) std::cout << ',';
            if (witnesses[f].empty()) std::cout << "null";
            else std::cout << '"' << hex(witnesses[f]) << '"';
        }
        std::cout << "]}\n";
        return 0;
    } catch (const std::exception &e) {std::cerr << e.what() << '\n'; return 2;}
}
