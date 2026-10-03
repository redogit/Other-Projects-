#include "rmal/rmal.h"
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct Page { const char *id; const char *source; } Page;
typedef struct NavFixture {
    const char *name; const char *target; const Page *pages; size_t page_count;
    const char *current_url; bool found; const char *source;
    bool append_history, promote_pending, clear_navigation, clear_render;
    const char *residual_kind,*residual_detail,*consequence;
} NavFixture;
typedef struct Host { const NavFixture *current; size_t results; } Host;

static const Page PAGES[]={{"page1","<h1>ONE</h1>"},{"page2","<h1>TWO</h1>"},{"page3","<h1>THREE</h1>"}};
static const NavFixture FIXTURES[]={
 {.name="navigate_first",.target="page1",.pages=PAGES,.page_count=3,.current_url="rmapl://local/current",.found=true,.source="<h1>ONE</h1>",.append_history=true,.promote_pending=true,.clear_navigation=true,.clear_render=true,.residual_kind="html-tokenization-pending",.residual_detail="local-navigation",.consequence="local-navigation"},
 {.name="navigate_third",.target="page3",.pages=PAGES,.page_count=3,.current_url="rmapl://local/current",.found=true,.source="<h1>THREE</h1>",.append_history=true,.promote_pending=true,.clear_navigation=true,.clear_render=true,.residual_kind="html-tokenization-pending",.residual_detail="local-navigation",.consequence="local-navigation"},
 {.name="missing",.target="missing",.pages=PAGES,.page_count=3,.current_url="rmapl://local/current",.found=false,.source="",.append_history=false,.promote_pending=false,.clear_navigation=false,.clear_render=false,.residual_kind="navigation-target-missing",.residual_detail="local-page-not-found",.consequence="navigation-target-missing"}
};
static const size_t FIXTURE_COUNT=sizeof(FIXTURES)/sizeof(FIXTURES[0]);

static RmalStatus ok(void){RmalStatus s={0};s.ok=true;return s;}
static RmalStatus bad(const char*m){RmalStatus s={0};snprintf(s.message,sizeof(s.message),"%s",m);return s;}
static char*dup_text(const char*t){size_t n=strlen(t)+1U;char*p=(char*)malloc(n);if(p)memcpy(p,t,n);return p;}
static int seq(const RmalValue*v,const char*e){return v&&v->kind==RMAL_VALUE_STRING&&v->as.string&&strcmp(v->as.string,e)==0;}
static RmalStatus select_f(void*ctx,const RmalValue*a,size_t n,RmalValue*r){Host*h=(Host*)ctx;if(!h||n!=1U||a[0].kind!=RMAL_VALUE_STRING||!a[0].as.string)return bad("select requires name");h->current=NULL;for(size_t i=0;i<FIXTURE_COUNT;++i)if(strcmp(a[0].as.string,FIXTURES[i].name)==0){h->current=&FIXTURES[i];break;}if(!h->current)return bad("unknown nav fixture");size_t z=strlen(h->current->name)+sizeof(":ACK");char*ack=(char*)malloc(z);if(!ack)return bad("select alloc");snprintf(ack,z,"%s:ACK",h->current->name);r->kind=RMAL_VALUE_STRING;r->as.string=ack;return ok();}
static RmalStatus str0(void*ctx,const RmalValue*a,size_t n,RmalValue*r,int which){(void)a;Host*h=(Host*)ctx;if(!h||!h->current||n!=0U)return bad("nav string requires fixture");const char*t=which==0?h->current->target:h->current->current_url;r->kind=RMAL_VALUE_STRING;r->as.string=dup_text(t);return r->as.string?ok():bad("nav string alloc");}
static RmalStatus target_f(void*c,const RmalValue*a,size_t n,RmalValue*r){return str0(c,a,n,r,0);}
static RmalStatus current_f(void*c,const RmalValue*a,size_t n,RmalValue*r){return str0(c,a,n,r,1);}
static RmalStatus count_f(void*ctx,const RmalValue*a,size_t n,RmalValue*r){(void)a;Host*h=(Host*)ctx;if(!h||!h->current||n!=0U)return bad("page count requires fixture");r->kind=RMAL_VALUE_INT;r->as.integer=(int64_t)h->current->page_count;return ok();}
static const Page*page_at(Host*h,const RmalValue*a,size_t n){if(!h||!h->current||n!=1U||a[0].kind!=RMAL_VALUE_INT||a[0].as.integer<0||(uint64_t)a[0].as.integer>=(uint64_t)h->current->page_count)return NULL;return &h->current->pages[(size_t)a[0].as.integer];}
static RmalStatus page_text(void*ctx,const RmalValue*a,size_t n,RmalValue*r,int which){Host*h=(Host*)ctx;const Page*p=page_at(h,a,n);if(!p)return bad("page index invalid");r->kind=RMAL_VALUE_STRING;r->as.string=dup_text(which==0?p->id:p->source);return r->as.string?ok():bad("page text alloc");}
static RmalStatus id_f(void*c,const RmalValue*a,size_t n,RmalValue*r){return page_text(c,a,n,r,0);}
static RmalStatus source_f(void*c,const RmalValue*a,size_t n,RmalValue*r){return page_text(c,a,n,r,1);}
static RmalStatus result_f(void*ctx,const RmalValue*a,size_t n,RmalValue*r){Host*h=(Host*)ctx;if(!h||!h->current||n!=11U||a[0].kind!=RMAL_VALUE_BOOL||a[4].kind!=RMAL_VALUE_BOOL||a[5].kind!=RMAL_VALUE_BOOL||a[6].kind!=RMAL_VALUE_BOOL||a[7].kind!=RMAL_VALUE_BOOL)return bad("nav result contract");const NavFixture*e=h->current;if(a[0].as.boolean!=e->found||!seq(&a[1],e->target)||!seq(&a[2],e->source)||!seq(&a[3],e->current_url)||a[4].as.boolean!=e->append_history||a[5].as.boolean!=e->promote_pending||a[6].as.boolean!=e->clear_navigation||a[7].as.boolean!=e->clear_render||!seq(&a[8],e->residual_kind)||!seq(&a[9],e->residual_detail)||!seq(&a[10],e->consequence))return bad("RMAL nav result differs");
 printf("RMAL_LOCAL_NAV fixture=%s found=%s target=%s source_hex=",e->name,a[0].as.boolean?"true":"false",a[1].as.string);for(const unsigned char*p=(const unsigned char*)a[2].as.string;*p;++p)printf("%02x",(unsigned)*p);printf(" current=%s history=%s promote=%s clear_nav=%s clear_render=%s residual=%s detail=%s consequence=%s\n",a[3].as.string,a[4].as.boolean?"true":"false",a[5].as.boolean?"true":"false",a[6].as.boolean?"true":"false",a[7].as.boolean?"true":"false",a[8].as.string,a[9].as.string,a[10].as.string);
 size_t z=strlen(e->consequence)+sizeof(":ACK");char*ack=(char*)malloc(z);if(!ack)return bad("result alloc");snprintf(ack,z,"%s:ACK",e->consequence);r->kind=RMAL_VALUE_STRING;r->as.string=ack;h->results+=1U;return ok();}
static FILE*open_read(const char*p){
#if defined(_WIN32)
 FILE*f=NULL;if(fopen_s(&f,p,"rb")!=0)return NULL;return f;
#else
 return fopen(p,"rb");
#endif
}
static char*read_file(const char*p){FILE*f=open_read(p);if(!f)return NULL;if(fseek(f,0,SEEK_END)!=0){fclose(f);return NULL;}long e=ftell(f);if(e<0){fclose(f);return NULL;}rewind(f);size_t n=(size_t)e;char*b=(char*)malloc(n+1U);if(!b){fclose(f);return NULL;}size_t g=fread(b,1U,n,f);fclose(f);if(g!=n){free(b);return NULL;}b[n]='\0';return b;}
static int st(const char*x,const RmalStatus*s){fprintf(stderr,"%s failed at %d:%d: %s\n",x,s?s->line:0,s?s->column:0,s?s->message:"unknown");return 1;}
int main(int argc,char**argv){if(argc!=2)return 64;char*src=read_file(argv[1]);if(!src)return 65;RmalStatus s={0};RmalProgram*p=rmal_parse_source(src,argv[1],&s);free(src);if(!p)return st("parse",&s);RmalBytecode*bc=rmal_compile(p,&s);if(!bc){rmal_program_free(p);return st("compile",&s);}RmalVm*vm=rmal_vm_create();if(!vm)return 66;Host h={0};struct B{const char*n;size_t a;RmalNativeFunction f;}b[]={{"BrowserLocalNavSelect",1,select_f},{"BrowserNavTarget",0,target_f},{"BrowserPageCount",0,count_f},{"BrowserPageId",1,id_f},{"BrowserPageSource",1,source_f},{"BrowserCurrentUrlCanonical",0,current_f},{"BrowserLocalNavResult",11,result_f}};for(size_t i=0;i<sizeof(b)/sizeof(b[0]);++i){s=rmal_vm_bind_native(vm,b[i].n,b[i].a,b[i].f,&h);if(!s.ok){rmal_vm_free(vm);rmal_bytecode_free(bc);rmal_program_free(p);return st("bind",&s);}}RmalValue rv={0};s=rmal_vm_run(vm,bc,true,&rv);rmal_value_free(&rv);int rc=0;if(!s.ok)rc=st("run",&s);else if(h.results!=FIXTURE_COUNT){fprintf(stderr,"nav results incomplete\n");rc=67;}else printf("RMAL_LOCAL_NAV_RECEIPT fixtures=%zu policy_in_rmal=true python_runtime_used=false\n",h.results);rmal_vm_free(vm);rmal_bytecode_free(bc);rmal_program_free(p);return rc;}
