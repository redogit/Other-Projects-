#include "rmal/rmal.hpp"
#include <algorithm>
#include <cctype>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>

namespace rmal {

std::string to_string(const Value& v){
  if(std::holds_alternative<std::monostate>(v)) return "nil";
  if(auto p=std::get_if<std::int64_t>(&v)) return std::to_string(*p);
  if(auto p=std::get_if<bool>(&v)) return *p?"true":"false";
  return std::get<std::string>(v);
}
bool truthy(const Value& v){
  if(auto p=std::get_if<bool>(&v)) return *p;
  if(auto p=std::get_if<std::int64_t>(&v)) return *p!=0;
  if(auto p=std::get_if<std::string>(&v)) return !p->empty();
  return false;
}

Lexer::Lexer(std::string s):src_(std::move(s)){}
char Lexer::peek(std::size_t n) const { return i_+n<src_.size()?src_[i_+n]:'\0'; }
char Lexer::advance(){
  char c=peek(); if(c=='\0') return c; ++i_;
  if(c=='\n'){ ++line_; col_=1; } else ++col_;
  return c;
}
bool Lexer::match(char c){ if(peek()!=c) return false; advance(); return true; }
void Lexer::token(TokenKind k,std::string s,int l,int c){ out_.push_back({k,std::move(s),l,c}); }

std::vector<Token> Lexer::scan(){
  while(peek()){
    int l=line_,c=col_; char ch=advance();
    if(std::isspace((unsigned char)ch)) continue;
    if(ch=='#'){ while(peek()&&peek()!='\n') advance(); continue; }
    if(ch=='/'&&peek()=='/'){ while(peek()&&peek()!='\n') advance(); continue; }
    if(std::isalpha((unsigned char)ch)||ch=='_'){
      std::string s(1,ch);
      while(std::isalnum((unsigned char)peek())||peek()=='_'||peek()=='.') s+=advance();
      token(TokenKind::Identifier,s,l,c); continue;
    }
    if(std::isdigit((unsigned char)ch)){
      std::string s(1,ch);
      while(std::isdigit((unsigned char)peek())) s+=advance();
      token(TokenKind::Number,s,l,c); continue;
    }
    if(ch=='"'){
      std::string s;
      while(peek()&&peek()!='"'){
        char q=advance();
        if(q=='\\'){
          char e=advance();
          s += e=='n'?'\n':e=='t'?'\t':e;
        } else s+=q;
      }
      if(!match('"')) throw std::runtime_error("unterminated string at line "+std::to_string(l));
      token(TokenKind::String,s,l,c); continue;
    }
    switch(ch){
      case '(': token(TokenKind::LParen,"(",l,c); break;
      case ')': token(TokenKind::RParen,")",l,c); break;
      case '{': token(TokenKind::LBrace,"{",l,c); break;
      case '}': token(TokenKind::RBrace,"}",l,c); break;
      case ',': token(TokenKind::Comma,",",l,c); break;
      case ';': token(TokenKind::Semicolon,";",l,c); break;
      case '+': token(TokenKind::Plus,"+",l,c); break;
      case '-': token(TokenKind::Minus,"-",l,c); break;
      case '*': token(TokenKind::Star,"*",l,c); break;
      case '/': token(TokenKind::Slash,"/",l,c); break;
      case '%': token(TokenKind::Percent,"%",l,c); break;
      case '=': { bool eq=match('='); token(eq?TokenKind::EqualEqual:TokenKind::Assign,eq?"==":"=",l,c); break; }
      case '!': if(match('=')) token(TokenKind::BangEqual,"!=",l,c); else token(TokenKind::Bang,"!",l,c); break;
      case '<': if(match('=')) token(TokenKind::LessEqual,"<=",l,c); else token(TokenKind::Less,"<",l,c); break;
      case '>': if(match('=')) token(TokenKind::GreaterEqual,">=",l,c); else token(TokenKind::Greater,">",l,c); break;
      case '&': if(match('&')) token(TokenKind::AndAnd,"&&",l,c); else throw std::runtime_error("expected &&"); break;
      case '|': if(match('|')) token(TokenKind::OrOr,"||",l,c); else throw std::runtime_error("expected ||"); break;
      default: throw std::runtime_error(std::string("unexpected character: ")+ch);
    }
  }
  out_.push_back({TokenKind::End,"",line_,col_});
  return out_;
}

Parser::Parser(std::vector<Token> t):t_(std::move(t)){}
const Token& Parser::peek(std::size_t n) const { return t_[std::min(i_+n,t_.size()-1)]; }
bool Parser::at_end() const { return peek().kind==TokenKind::End; }
bool Parser::accept(TokenKind k){ if(peek().kind!=k) return false; ++i_; return true; }
const Token& Parser::expect(TokenKind k,const char* w){
  if(peek().kind!=k) throw std::runtime_error("expected "+std::string(w)+" at line "+std::to_string(peek().line));
  return t_[i_++];
}
static bool kw(const Token& t,const char* s){ return t.kind==TokenKind::Identifier&&t.lexeme==s; }

Program Parser::parse(){
  while(!at_end()) p_.statements.push_back(statement());
  return p_;
}

std::vector<Stmt> Parser::block(){
  expect(TokenKind::LBrace,"{");
  std::vector<Stmt> b;
  while(!accept(TokenKind::RBrace)){
    if(at_end()) throw std::runtime_error("unterminated block");
    b.push_back(statement());
  }
  return b;
}

Stmt Parser::statement(){
  if(kw(peek(),"MODULE")){
    ++i_; p_.module=expect(TokenKind::Identifier,"module name").lexeme; accept(TokenKind::Semicolon);
    Stmt s; s.kind=Stmt::Kind::Directive; s.name="MODULE"; s.directive_payload=p_.module; return s;
  }
  if(kw(peek(),"const")||kw(peek(),"CONST")){
    ++i_; auto n=expect(TokenKind::Identifier,"name").lexeme; expect(TokenKind::Assign,"=");
    auto e=expression(); accept(TokenKind::Semicolon); Stmt s; s.kind=Stmt::Kind::Const; s.name=n; s.expr=e; return s;
  }
  if(kw(peek(),"let")){
    ++i_; auto n=expect(TokenKind::Identifier,"name").lexeme; expect(TokenKind::Assign,"=");
    auto e=expression(); accept(TokenKind::Semicolon); Stmt s; s.kind=Stmt::Kind::Let; s.name=n; s.expr=e; return s;
  }
  if(kw(peek(),"print")){ ++i_; auto e=expression(); accept(TokenKind::Semicolon); Stmt s; s.kind=Stmt::Kind::Print; s.expr=e; return s; }
  if(kw(peek(),"assert")){ ++i_; auto e=expression(); accept(TokenKind::Semicolon); Stmt s; s.kind=Stmt::Kind::Assert; s.expr=e; return s; }
  if(kw(peek(),"return")){ ++i_; auto e=expression(); accept(TokenKind::Semicolon); Stmt s; s.kind=Stmt::Kind::Return; s.expr=e; return s; }
  if(kw(peek(),"if")){
    ++i_; auto e=expression(); auto b=block(); std::vector<Stmt> eb;
    if(kw(peek(),"else")){ ++i_; eb=block(); }
    Stmt s; s.kind=Stmt::Kind::If; s.expr=e; s.body=b; s.else_body=eb; return s;
  }
  if(kw(peek(),"while")){
    ++i_; auto e=expression(); auto b=block();
    Stmt s; s.kind=Stmt::Kind::While; s.expr=e; s.body=b; return s;
  }
  if(kw(peek(),"fn")){
    ++i_; auto n=expect(TokenKind::Identifier,"function name").lexeme; expect(TokenKind::LParen,"(");
    std::vector<std::string> ps;
    if(!accept(TokenKind::RParen)){
      do { ps.push_back(expect(TokenKind::Identifier,"parameter").lexeme); } while(accept(TokenKind::Comma));
      expect(TokenKind::RParen,")");
    }
    auto b=block();
    Stmt s; s.kind=Stmt::Kind::Function; s.name=n; s.params=ps; s.body=b; return s;
  }

  static const char* directives[]={
    "EXPORT","CONTEXT","RELATION","PRESERVE","ALLOW","DENY","CLAIM","EVIDENCE",
    "COUNTERPROBE","VERIFY","CONTINUE","OBLIGATION","INVARIANT","REMAINDER","SURFACE","TRACE"
  };
  if(peek().kind==TokenKind::Identifier){
    for(auto d:directives) if(peek().lexeme==d){
      const int line=peek().line;
      auto name=peek().lexeme; ++i_;
      std::ostringstream ss;
      while(!at_end() && peek().kind!=TokenKind::Semicolon && peek().line==line){
        ss<<peek().lexeme;
        if(peek(1).line==line && peek(1).kind!=TokenKind::Semicolon) ss<<' ';
        ++i_;
      }
      accept(TokenKind::Semicolon);
      Stmt s; s.kind=Stmt::Kind::Directive; s.name=name; s.directive_payload=ss.str(); return s;
    }
  }

  auto e=expression(); accept(TokenKind::Semicolon);
  Stmt s; s.kind=Stmt::Kind::ExprStmt; s.expr=e; return s;
}

int Parser::precedence(TokenKind k) const {
  switch(k){
    case TokenKind::OrOr:return 1;
    case TokenKind::AndAnd:return 2;
    case TokenKind::EqualEqual:case TokenKind::BangEqual:return 3;
    case TokenKind::Less:case TokenKind::LessEqual:case TokenKind::Greater:case TokenKind::GreaterEqual:return 4;
    case TokenKind::Plus:case TokenKind::Minus:return 5;
    case TokenKind::Star:case TokenKind::Slash:case TokenKind::Percent:return 6;
    default:return -1;
  }
}

Expr Parser::prefix(){
  if(accept(TokenKind::Minus)){ Expr e; e.kind=Expr::Kind::Unary; e.text="-"; e.args.push_back(prefix()); return e; }
  if(accept(TokenKind::Bang)){ Expr e; e.kind=Expr::Kind::Unary; e.text="!"; e.args.push_back(prefix()); return e; }
  if(accept(TokenKind::LParen)){ auto e=expression(); expect(TokenKind::RParen,")"); return e; }
  if(peek().kind==TokenKind::Number){ auto t=t_[i_++]; Expr e; e.kind=Expr::Kind::Literal; e.literal=(std::int64_t)std::stoll(t.lexeme); return e; }
  if(peek().kind==TokenKind::String){ auto t=t_[i_++]; Expr e; e.kind=Expr::Kind::Literal; e.literal=t.lexeme; return e; }
  if(kw(peek(),"true")||kw(peek(),"false")){ bool v=kw(peek(),"true"); ++i_; Expr e; e.kind=Expr::Kind::Literal; e.literal=v; return e; }

  auto id=expect(TokenKind::Identifier,"expression").lexeme;
  if(accept(TokenKind::LParen)){
    Expr e; e.kind=Expr::Kind::Call; e.text=id;
    if(!accept(TokenKind::RParen)){
      do { e.args.push_back(expression()); } while(accept(TokenKind::Comma));
      expect(TokenKind::RParen,")");
    }
    return e;
  }
  Expr e; e.kind=Expr::Kind::Variable; e.text=id; return e;
}

Expr Parser::expression(int min){
  int baseLine=peek().line;
  auto lhs=prefix();
  while(true){
    if(peek().line>baseLine) break;
    int p=precedence(peek().kind);
    if(p<min) break;
    auto op=peek().lexeme; ++i_;
    auto rhs=expression(p+1);
    Expr e; e.kind=Expr::Kind::Binary; e.text=op; e.args={lhs,rhs};
    lhs=std::move(e);
  }
  return lhs;
}

std::size_t Compiler::constant(Value v){ bc_.constants.push_back(std::move(v)); return bc_.constants.size()-1; }
std::size_t Compiler::name(const std::string& n){
  auto it=names_.find(n); if(it!=names_.end()) return it->second;
  auto x=bc_.names.size(); bc_.names.push_back(n); names_[n]=x; return x;
}

void Compiler::emit_expr(const Expr& e,std::vector<Instruction>& o){
  if(e.kind==Expr::Kind::Literal){ o.push_back({Op::PushConst,(std::int64_t)constant(e.literal)}); return; }
  if(e.kind==Expr::Kind::Variable){ o.push_back({Op::Load,(std::int64_t)name(e.text)}); return; }
  if(e.kind==Expr::Kind::Unary){
    emit_expr(e.args[0],o); o.push_back({e.text=="-"?Op::Neg:Op::Not}); return;
  }
  if(e.kind==Expr::Kind::Call){
    for(auto& a:e.args) emit_expr(a,o);
    o.push_back({Op::Call,(std::int64_t)name(e.text),(std::int64_t)e.args.size()}); return;
  }
  emit_expr(e.args[0],o); emit_expr(e.args[1],o);
  static const std::map<std::string,Op> ops={
    {"+",Op::Add},{"-",Op::Sub},{"*",Op::Mul},{"/",Op::Div},{"%",Op::Mod},
    {"==",Op::Eq},{"!=",Op::Ne},{"<",Op::Lt},{"<=",Op::Le},{">",Op::Gt},{">=",Op::Ge},
    {"&&",Op::And},{"||",Op::Or}
  };
  o.push_back({ops.at(e.text)});
}

void Compiler::patch(std::vector<Instruction>& o,std::size_t at,std::size_t to){ o[at].a=(std::int64_t)to; }

void Compiler::emit_stmt(const Stmt& s,std::vector<Instruction>& o){
  switch(s.kind){
    case Stmt::Kind::Const:
    case Stmt::Kind::Let:
      emit_expr(s.expr,o); o.push_back({Op::Store,(std::int64_t)name(s.name)}); break;
    case Stmt::Kind::Print:
      emit_expr(s.expr,o); o.push_back({Op::Print}); break;
    case Stmt::Kind::Assert:
      emit_expr(s.expr,o); o.push_back({Op::Assert}); break;
    case Stmt::Kind::ExprStmt:
      emit_expr(s.expr,o); o.push_back({Op::Pop}); break;
    case Stmt::Kind::Return:
      emit_expr(s.expr,o); o.push_back({Op::Ret}); break;
    case Stmt::Kind::Directive:
      o.push_back({Op::Directive,(std::int64_t)constant(s.name+" "+s.directive_payload)}); break;
    case Stmt::Kind::If: {
      emit_expr(s.expr,o);
      auto jf=o.size(); o.push_back({Op::JumpIfFalse});
      for(auto& x:s.body) emit_stmt(x,o);
      auto j=o.size(); o.push_back({Op::Jump});
      patch(o,jf,o.size());
      for(auto& x:s.else_body) emit_stmt(x,o);
      patch(o,j,o.size());
      break;
    }
    case Stmt::Kind::While: {
      auto start=o.size(); emit_expr(s.expr,o);
      auto jf=o.size(); o.push_back({Op::JumpIfFalse});
      for(auto& x:s.body) emit_stmt(x,o);
      o.push_back({Op::Jump,(std::int64_t)start});
      patch(o,jf,o.size());
      break;
    }
    case Stmt::Kind::Function: break;
    case Stmt::Kind::Block: for(auto& x:s.body) emit_stmt(x,o); break;
  }
}

Bytecode Compiler::compile(const Program& p){
  bc_={}; names_.clear(); bc_.module=p.module;
  for(auto& s:p.statements) if(s.kind==Stmt::Kind::Function){
    Function f; f.name=s.name; f.params=s.params;
    for(auto& x:s.body) emit_stmt(x,f.code);
    f.code.push_back({Op::PushConst,(std::int64_t)constant({})});
    f.code.push_back({Op::Ret});
    bc_.functions.push_back(std::move(f));
  }
  for(auto& s:p.statements) if(s.kind!=Stmt::Kind::Function) emit_stmt(s,bc_.main);
  bc_.main.push_back({Op::Halt});
  return bc_;
}

static std::int64_t asint(const Value& v){
  if(auto p=std::get_if<std::int64_t>(&v)) return *p;
  throw std::runtime_error("expected integer");
}

Value VM::exec(const Bytecode& bc,const std::vector<Instruction>& code,const std::vector<Value>& args,const Function* fn,bool tracing){
  std::vector<Value> st;
  std::map<std::string,Value> locals;
  if(fn) for(std::size_t k=0;k<fn->params.size();++k) locals[fn->params[k]]=args[k];
  auto pop=[&](){
    if(st.empty()) throw std::runtime_error("stack underflow");
    auto v=st.back(); st.pop_back(); return v;
  };

  for(std::size_t pc=0;pc<code.size();++pc){
    auto in=code[pc];
    if(tracing) trace_.push_back({pc,std::to_string((int)in.op),""});
    switch(in.op){
      case Op::PushConst: st.push_back(bc.constants.at(in.a)); break;
      case Op::Load: {
        auto n=bc.names.at(in.a);
        if(locals.count(n)) st.push_back(locals[n]);
        else if(globals_.count(n)) st.push_back(globals_[n]);
        else throw std::runtime_error("undefined name: "+n);
        break;
      }
      case Op::Store: { auto n=bc.names.at(in.a); globals_[n]=pop(); break; }
      case Op::Add: {
        auto b=pop(),a=pop();
        if(std::holds_alternative<std::string>(a)||std::holds_alternative<std::string>(b)) st.push_back(to_string(a)+to_string(b));
        else st.push_back(asint(a)+asint(b));
        break;
      }
      case Op::Sub: { auto b=asint(pop()),a=asint(pop()); st.push_back(a-b); break; }
      case Op::Mul: { auto b=asint(pop()),a=asint(pop()); st.push_back(a*b); break; }
      case Op::Div: { auto b=asint(pop()),a=asint(pop()); if(!b) throw std::runtime_error("division by zero"); st.push_back(a/b); break; }
      case Op::Mod: { auto b=asint(pop()),a=asint(pop()); if(!b) throw std::runtime_error("modulo by zero"); st.push_back(a%b); break; }
      case Op::Neg: st.push_back(-asint(pop())); break;
      case Op::Not: st.push_back(!truthy(pop())); break;
      case Op::Eq: { auto b=pop(),a=pop(); st.push_back(to_string(a)==to_string(b)); break; }
      case Op::Ne: { auto b=pop(),a=pop(); st.push_back(to_string(a)!=to_string(b)); break; }
      case Op::Lt: { auto b=asint(pop()),a=asint(pop()); st.push_back(a<b); break; }
      case Op::Le: { auto b=asint(pop()),a=asint(pop()); st.push_back(a<=b); break; }
      case Op::Gt: { auto b=asint(pop()),a=asint(pop()); st.push_back(a>b); break; }
      case Op::Ge: { auto b=asint(pop()),a=asint(pop()); st.push_back(a>=b); break; }
      case Op::And: { auto b=truthy(pop()),a=truthy(pop()); st.push_back(a&&b); break; }
      case Op::Or: { auto b=truthy(pop()),a=truthy(pop()); st.push_back(a||b); break; }
      case Op::Print: std::cout<<to_string(pop())<<'\n'; break;
      case Op::Assert: if(!truthy(pop())) throw std::runtime_error("assertion failed"); break;
      case Op::Pop: pop(); break;
      case Op::Jump: pc=(std::size_t)in.a-1; break;
      case Op::JumpIfFalse: if(!truthy(pop())) pc=(std::size_t)in.a-1; break;
      case Op::Call: {
        std::vector<Value> a((std::size_t)in.b);
        for(std::size_t k=a.size();k-->0;) a[k]=pop();
        auto n=bc.names.at(in.a);
        auto it=std::find_if(bc.functions.begin(),bc.functions.end(),[&](auto& f){ return f.name==n; });
        if(it==bc.functions.end()) throw std::runtime_error("undefined function: "+n);
        st.push_back(exec(bc,it->code,a,&*it,tracing));
        break;
      }
      case Op::Ret: return st.empty()?Value{}:pop();
      case Op::Directive: break;
      case Op::Halt: return st.empty()?Value{}:st.back();
    }
  }
  return {};
}

Value VM::run(const Bytecode& bc,bool trace){
  trace_.clear(); globals_.clear();
  return exec(bc,bc.main,{},nullptr,trace);
}

Program parse_source(const std::string& s){ return Parser(Lexer(s).scan()).parse(); }
Bytecode compile_source(const std::string& s){ return Compiler().compile(parse_source(s)); }

static const char* opname(Op o){
  static const char* n[]={
    "PUSH","LOAD","STORE","ADD","SUB","MUL","DIV","MOD","NEG","NOT","EQ","NE","LT","LE",
    "GT","GE","AND","OR","PRINT","ASSERT","POP","JUMP","JFALSE","CALL","RET","HALT","DIRECTIVE"
  };
  return n[(int)o];
}

std::string disassemble(const Bytecode& bc){
  std::ostringstream s;
  s<<"RMALBC1 module="<<bc.module<<"\n";
  for(std::size_t i=0;i<bc.main.size();++i)
    s<<i<<"\t"<<opname(bc.main[i].op)<<"\t"<<bc.main[i].a<<"\t"<<bc.main[i].b<<"\n";
  for(auto& f:bc.functions){
    s<<"fn "<<f.name<<"\n";
    for(std::size_t i=0;i<f.code.size();++i)
      s<<"  "<<i<<"\t"<<opname(f.code[i].op)<<"\t"<<f.code[i].a<<"\t"<<f.code[i].b<<"\n";
  }
  return s.str();
}

std::string audit(const Program& p,const Bytecode& bc){
  std::ostringstream s;
  s<<"AUDIT PASS\n";
  s<<"module="<<p.module<<"\n";
  s<<"statements="<<p.statements.size()<<"\n";
  s<<"bytecode="<<bc.main.size()<<"\n";
  s<<"functions="<<bc.functions.size()<<"\n";
  s<<"AUDIT_PASS != SEMANTIC_TRUTH\n";
  return s.str();
}

bool selfcheck(std::string* report){
  try {
    std::string src=R"(MODULE selfcheck;
const two = 2;
fn fact(n) { if n <= 1 { return 1; } else { return n * fact(n - 1); } }
assert fact(5) == 120;
assert two + 3 * 4 == 14;
CONTEXT SelfCheck authority=LOCAL evidence_transfer=DENY
VERIFY "parser compiler vm";
CONTINUE;
)";
    auto p=parse_source(src);
    auto b=Compiler().compile(p);
    VM vm; vm.run(b,true);
    if(report) *report=audit(p,b)+"trace="+std::to_string(vm.trace().size())+"\n";
    return true;
  } catch(const std::exception& e){
    if(report) *report=e.what();
    return false;
  }
}

} // namespace rmal
