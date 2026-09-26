#include "rmal/rmal.hpp"
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>

static std::string readall(const std::string& p){
  std::ifstream f(p);
  if(!f) throw std::runtime_error("cannot open "+p);
  std::ostringstream s; s<<f.rdbuf(); return s.str();
}

int main(int argc,char** argv){
  try {
    if(argc<2){
      std::cerr<<"rmalc <check|compile|run|audit|trace|selfcheck> [file]\n";
      return 2;
    }
    std::string cmd=argv[1];
    if(cmd=="selfcheck"){
      std::string report;
      bool ok=rmal::selfcheck(&report);
      std::cout<<report;
      return ok?0:1;
    }
    if(argc<3) throw std::runtime_error("source file required");
    auto src=readall(argv[2]);
    auto p=rmal::parse_source(src);
    auto bc=rmal::Compiler().compile(p);
    if(cmd=="check"){
      std::cout<<"CHECK PASS module="<<p.module<<" statements="<<p.statements.size()<<"\n";
      return 0;
    }
    if(cmd=="compile"){ std::cout<<rmal::disassemble(bc); return 0; }
    if(cmd=="audit"){ std::cout<<rmal::audit(p,bc); return 0; }
    if(cmd=="run"||cmd=="trace"){
      rmal::VM vm; vm.run(bc,cmd=="trace");
      if(cmd=="trace")
        for(auto& e:vm.trace()) std::cout<<"TRACE pc="<<e.pc<<" op="<<e.op<<"\n";
      return 0;
    }
    throw std::runtime_error("unknown command: "+cmd);
  } catch(const std::exception& e){
    std::cerr<<"RMALC ERROR: "<<e.what()<<"\n";
    return 1;
  }
}
