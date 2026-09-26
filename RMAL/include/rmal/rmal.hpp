#pragma once
#include <cstdint>
#include <map>
#include <string>
#include <variant>
#include <vector>

namespace rmal {

enum class TokenKind { End, Identifier, Number, String, LParen, RParen, LBrace, RBrace,
  Comma, Semicolon, Assign, Plus, Minus, Star, Slash, Percent, Bang, EqualEqual, BangEqual,
  Less, LessEqual, Greater, GreaterEqual, AndAnd, OrOr };

struct Token { TokenKind kind; std::string lexeme; int line; int column; };
using Value = std::variant<std::monostate, std::int64_t, bool, std::string>;
std::string to_string(const Value&);
bool truthy(const Value&);

struct Expr {
  enum class Kind { Literal, Variable, Unary, Binary, Call } kind;
  Value literal{}; std::string text; std::vector<Expr> args;
};

struct Stmt {
  enum class Kind { Const, Let, Print, Assert, ExprStmt, Block, If, While, Return, Function, Directive } kind;
  std::string name; Expr expr{}; std::vector<Stmt> body; std::vector<Stmt> else_body;
  std::vector<std::string> params; std::string directive_payload;
};

struct Program { std::string module="main"; std::vector<Stmt> statements; };

class Lexer {
public:
  explicit Lexer(std::string source);
  std::vector<Token> scan();
private:
  std::string src_; std::size_t i_=0; int line_=1,col_=1; std::vector<Token> out_;
  char peek(std::size_t n=0) const; char advance(); bool match(char);
  void token(TokenKind,std::string,int,int);
};

class Parser {
public:
  explicit Parser(std::vector<Token>);
  Program parse();
private:
  std::vector<Token> t_; std::size_t i_=0; Program p_;
  const Token& peek(std::size_t n=0) const; bool at_end() const; bool accept(TokenKind);
  const Token& expect(TokenKind,const char*);
  Stmt statement(); std::vector<Stmt> block(); Expr expression(int minPrec=0); Expr prefix();
  int precedence(TokenKind) const;
};

enum class Op : std::uint8_t { PushConst, Load, Store, Add, Sub, Mul, Div, Mod, Neg, Not,
  Eq, Ne, Lt, Le, Gt, Ge, And, Or, Print, Assert, Pop, Jump, JumpIfFalse, Call, Ret, Halt, Directive };

struct Instruction { Op op; std::int64_t a=0; std::int64_t b=0; };
struct Function { std::string name; std::vector<std::string> params; std::vector<Instruction> code; };
struct Bytecode {
  std::string module;
  std::vector<Value> constants;
  std::vector<std::string> names;
  std::vector<Function> functions;
  std::vector<Instruction> main;
};

class Compiler {
public:
  Bytecode compile(const Program&);
private:
  Bytecode bc_; std::map<std::string,std::size_t> names_;
  std::size_t constant(Value); std::size_t name(const std::string&);
  void emit_expr(const Expr&,std::vector<Instruction>&);
  void emit_stmt(const Stmt&,std::vector<Instruction>&);
  void patch(std::vector<Instruction>&,std::size_t,std::size_t);
};

struct TraceEvent { std::size_t pc; std::string op; std::string detail; };
class VM {
public:
  Value run(const Bytecode&,bool trace=false);
  const std::vector<TraceEvent>& trace() const { return trace_; }
private:
  std::vector<TraceEvent> trace_;
  std::map<std::string,Value> globals_;
  Value exec(const Bytecode&,const std::vector<Instruction>&,const std::vector<Value>& args={},
             const Function* fn=nullptr,bool tracing=false);
};

Program parse_source(const std::string&);
Bytecode compile_source(const std::string&);
std::string disassemble(const Bytecode&);
std::string audit(const Program&,const Bytecode&);
bool selfcheck(std::string* report=nullptr);

} // namespace rmal
