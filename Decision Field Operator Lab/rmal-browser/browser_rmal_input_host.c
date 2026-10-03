#include "rmal/rmal.h"

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct Hit {
    int64_t x, y, width, height;
    const char *href;
} Hit;

typedef struct InputFixture {
    const char *name;
    const char *kind;
    int64_t px, py;
    const char *key;
    const Hit *hits;
    size_t hit_count;
    const char *initial_pending;
    const char *initial_last;
    int64_t initial_focus;
    const char *initial_focused;
    const char *expected_pending;
    const char *expected_last;
    int64_t expected_focus;
    const char *expected_focused;
    bool residual_present;
    const char *residual_kind;
    const char *residual_detail;
    const char *consequence;
} InputFixture;

typedef struct InputHost {
    const InputFixture *current;
    size_t results;
} InputHost;

static const Hit HITS_TWO[] = {
    {4,4,24,7,"page2"},
    {40,4,30,7,"https://example.com"}
};

static const InputFixture FIXTURES[] = {
    {.name="pointer_second",.kind="pointer",.px=45,.py=5,.key="",.hits=HITS_TWO,.hit_count=2,
     .initial_pending="KEEP",.initial_last="OLD",.initial_focus=1,.initial_focused="OLD_FOCUS",
     .expected_pending="https://example.com",.expected_last="https://example.com",.expected_focus=1,.expected_focused="OLD_FOCUS",
     .residual_present=true,.residual_kind="url-resolution-pending",.residual_detail="pointer-hit",.consequence="pointer-hit"},
    {.name="pointer_miss",.kind="pointer",.px=100,.py=50,.key="",.hits=HITS_TWO,.hit_count=2,
     .initial_pending="KEEP",.initial_last="OLD",.initial_focus=1,.initial_focused="OLD_FOCUS",
     .expected_pending="KEEP",.expected_last="",.expected_focus=1,.expected_focused="OLD_FOCUS",
     .residual_present=true,.residual_kind="pointer-no-target",.residual_detail="no-hit",.consequence="pointer-no-target"},
    {.name="tab_first",.kind="keyboard",.px=0,.py=0,.key="TAB",.hits=HITS_TWO,.hit_count=2,
     .initial_pending="KEEP",.initial_last="OLD",.initial_focus=-1,.initial_focused="OLD_FOCUS",
     .expected_pending="KEEP",.expected_last="page2",.expected_focus=0,.expected_focused="page2",
     .residual_present=false,.residual_kind="",.residual_detail="",.consequence="keyboard-focus"},
    {.name="tab_wrap",.kind="keyboard",.px=0,.py=0,.key="TAB",.hits=HITS_TWO,.hit_count=2,
     .initial_pending="KEEP",.initial_last="OLD",.initial_focus=1,.initial_focused="https://example.com",
     .expected_pending="KEEP",.expected_last="page2",.expected_focus=0,.expected_focused="page2",
     .residual_present=false,.residual_kind="",.residual_detail="",.consequence="keyboard-focus"},
    {.name="tab_no_hits",.kind="keyboard",.px=0,.py=0,.key="TAB",.hits=NULL,.hit_count=0,
     .initial_pending="KEEP",.initial_last="OLD",.initial_focus=-1,.initial_focused="OLD_FOCUS",
     .expected_pending="KEEP",.expected_last="OLD",.expected_focus=-1,.expected_focused="OLD_FOCUS",
     .residual_present=true,.residual_kind="keyboard-no-target",.residual_detail="no-focused-link",.consequence="keyboard-no-target"},
    {.name="enter_valid",.kind="keyboard",.px=0,.py=0,.key="ENTER",.hits=HITS_TWO,.hit_count=2,
     .initial_pending="KEEP",.initial_last="OLD",.initial_focus=1,.initial_focused="https://example.com",
     .expected_pending="https://example.com",.expected_last="https://example.com",.expected_focus=-1,.expected_focused="",
     .residual_present=true,.residual_kind="url-resolution-pending",.residual_detail="keyboard-enter",.consequence="keyboard-enter"},
    {.name="enter_invalid",.kind="keyboard",.px=0,.py=0,.key="ENTER",.hits=HITS_TWO,.hit_count=2,
     .initial_pending="KEEP",.initial_last="OLD",.initial_focus=-1,.initial_focused="OLD_FOCUS",
     .expected_pending="KEEP",.expected_last="OLD",.expected_focus=-1,.expected_focused="OLD_FOCUS",
     .residual_present=true,.residual_kind="keyboard-no-target",.residual_detail="no-focused-link",.consequence="keyboard-no-target"},
    {.name="unsupported",.kind="keyboard",.px=0,.py=0,.key="ESC",.hits=HITS_TWO,.hit_count=2,
     .initial_pending="KEEP",.initial_last="OLD",.initial_focus=0,.initial_focused="page2",
     .expected_pending="KEEP",.expected_last="OLD",.expected_focus=0,.expected_focused="page2",
     .residual_present=true,.residual_kind="keyboard-unsupported",.residual_detail="unsupported-key",.consequence="keyboard-unsupported"}
};
static const size_t FIXTURE_COUNT=sizeof(FIXTURES)/sizeof(FIXTURES[0]);

static RmalStatus ok(void){RmalStatus s={0};s.ok=true;return s;}
static RmalStatus bad(const char *m){RmalStatus s={0};snprintf(s.message,sizeof(s.message),"%s",m);return s;}
static char *dup_text(const char *t){size_t n=strlen(t)+1U;char *p=(char*)malloc(n);if(p)memcpy(p,t,n);return p;}
static int str_eq(const RmalValue *v,const char *e){return v&&v->kind==RMAL_VALUE_STRING&&v->as.string&&strcmp(v->as.string,e)==0;}

static RmalStatus select_fixture(void *ctx,const RmalValue *a,size_t n,RmalValue *r){
    InputHost *h=(InputHost*)ctx;if(!h||n!=1U||a[0].kind!=RMAL_VALUE_STRING||!a[0].as.string)return bad("BrowserInputSelect requires one string");
    h->current=NULL;for(size_t i=0;i<FIXTURE_COUNT;++i)if(strcmp(a[0].as.string,FIXTURES[i].name)==0){h->current=&FIXTURES[i];break;}
    if(!h->current)return bad("unknown input fixture");size_t z=strlen(h->current->name)+sizeof(":ACK");char *ack=(char*)malloc(z);if(!ack)return bad("select allocation");
    snprintf(ack,z,"%s:ACK",h->current->name);r->kind=RMAL_VALUE_STRING;r->as.string=ack;return ok();
}
static RmalStatus int0(void *ctx,const RmalValue *a,size_t n,RmalValue *r,int which){
    (void)a;InputHost*h=(InputHost*)ctx;if(!h||!h->current||n!=0U)return bad("input scalar requires fixture");
    r->kind=RMAL_VALUE_INT;
    if(which==0)r->as.integer=h->current->px;else if(which==1)r->as.integer=h->current->py;else r->as.integer=h->current->initial_focus;
    return ok();
}
static RmalStatus px_fn(void*c,const RmalValue*a,size_t n,RmalValue*r){return int0(c,a,n,r,0);}
static RmalStatus py_fn(void*c,const RmalValue*a,size_t n,RmalValue*r){return int0(c,a,n,r,1);}
static RmalStatus focus_fn(void*c,const RmalValue*a,size_t n,RmalValue*r){return int0(c,a,n,r,2);}
static RmalStatus text0(void *ctx,const RmalValue *a,size_t n,RmalValue *r,int which){
    (void)a;InputHost*h=(InputHost*)ctx;if(!h||!h->current||n!=0U)return bad("input text requires fixture");
    const char*t=which==0?h->current->key:which==1?h->current->initial_pending:which==2?h->current->initial_last:h->current->initial_focused;
    r->kind=RMAL_VALUE_STRING;r->as.string=dup_text(t);return r->as.string?ok():bad("text allocation");
}
static RmalStatus key_fn(void*c,const RmalValue*a,size_t n,RmalValue*r){return text0(c,a,n,r,0);}
static RmalStatus pending_fn(void*c,const RmalValue*a,size_t n,RmalValue*r){return text0(c,a,n,r,1);}
static RmalStatus last_fn(void*c,const RmalValue*a,size_t n,RmalValue*r){return text0(c,a,n,r,2);}
static RmalStatus focused_fn(void*c,const RmalValue*a,size_t n,RmalValue*r){return text0(c,a,n,r,3);}
static RmalStatus hit_count_fn(void *ctx,const RmalValue*a,size_t n,RmalValue*r){(void)a;InputHost*h=(InputHost*)ctx;if(!h||!h->current||n!=0U)return bad("hit count requires fixture");r->kind=RMAL_VALUE_INT;r->as.integer=(int64_t)h->current->hit_count;return ok();}
static const Hit *get_hit(InputHost*h,const RmalValue*a,size_t n){if(!h||!h->current||n!=1U||a[0].kind!=RMAL_VALUE_INT||a[0].as.integer<0||(uint64_t)a[0].as.integer>=(uint64_t)h->current->hit_count)return NULL;return &h->current->hits[(size_t)a[0].as.integer];}
static RmalStatus hit_int(void*ctx,const RmalValue*a,size_t n,RmalValue*r,int which){InputHost*h=(InputHost*)ctx;const Hit*hit=get_hit(h,a,n);if(!hit)return bad("hit index invalid");r->kind=RMAL_VALUE_INT;r->as.integer=which==0?hit->x:which==1?hit->y:which==2?hit->width:hit->height;return ok();}
static RmalStatus hx(void*c,const RmalValue*a,size_t n,RmalValue*r){return hit_int(c,a,n,r,0);}
static RmalStatus hy(void*c,const RmalValue*a,size_t n,RmalValue*r){return hit_int(c,a,n,r,1);}
static RmalStatus hw(void*c,const RmalValue*a,size_t n,RmalValue*r){return hit_int(c,a,n,r,2);}
static RmalStatus hh(void*c,const RmalValue*a,size_t n,RmalValue*r){return hit_int(c,a,n,r,3);}
static RmalStatus href_fn(void*ctx,const RmalValue*a,size_t n,RmalValue*r){InputHost*h=(InputHost*)ctx;const Hit*hit=get_hit(h,a,n);if(!hit)return bad("href index invalid");r->kind=RMAL_VALUE_STRING;r->as.string=dup_text(hit->href);return r->as.string?ok():bad("href allocation");}

static RmalStatus result_fn(void *ctx,const RmalValue*a,size_t n,RmalValue*r){
    InputHost*h=(InputHost*)ctx;if(!h||!h->current||n!=8U||a[2].kind!=RMAL_VALUE_INT||a[4].kind!=RMAL_VALUE_BOOL)return bad("BrowserInputResult contract violated");
    const InputFixture*e=h->current;
    if(!str_eq(&a[0],e->expected_pending)||!str_eq(&a[1],e->expected_last)||a[2].as.integer!=e->expected_focus||
       !str_eq(&a[3],e->expected_focused)||a[4].as.boolean!=e->residual_present||
       !str_eq(&a[5],e->residual_kind)||!str_eq(&a[6],e->residual_detail)||!str_eq(&a[7],e->consequence))
        return bad("RMAL input decision differs from fixture");
    printf("RMAL_INPUT fixture=%s pending_hex=",e->name);for(const unsigned char*p=(const unsigned char*)a[0].as.string;*p;++p)printf("%02x",(unsigned int)*p);
    printf(" last_hex=");for(const unsigned char*p=(const unsigned char*)a[1].as.string;*p;++p)printf("%02x",(unsigned int)*p);
    printf(" focus=%lld focused_hex=",(long long)a[2].as.integer);for(const unsigned char*p=(const unsigned char*)a[3].as.string;*p;++p)printf("%02x",(unsigned int)*p);
    printf(" has_residual=%s residual=%s detail=%s consequence=%s\n",a[4].as.boolean?"true":"false",a[5].as.string[0]?a[5].as.string:"none",a[6].as.string[0]?a[6].as.string:"none",a[7].as.string);
    size_t z=strlen(e->consequence)+sizeof(":ACK");char*ack=(char*)malloc(z);if(!ack)return bad("result allocation");snprintf(ack,z,"%s:ACK",e->consequence);r->kind=RMAL_VALUE_STRING;r->as.string=ack;h->results+=1U;return ok();
}
static FILE*open_read(const char*p){
#if defined(_WIN32)
 FILE*f=NULL;if(fopen_s(&f,p,"rb")!=0)return NULL;return f;
#else
 return fopen(p,"rb");
#endif
}
static char*read_file(const char*p){FILE*f=open_read(p);if(!f)return NULL;if(fseek(f,0,SEEK_END)!=0){fclose(f);return NULL;}long e=ftell(f);if(e<0){fclose(f);return NULL;}rewind(f);size_t n=(size_t)e;char*b=(char*)malloc(n+1U);if(!b){fclose(f);return NULL;}size_t g=fread(b,1U,n,f);fclose(f);if(g!=n){free(b);return NULL;}b[n]='\0';return b;}
static int status(const char*stage,const RmalStatus*s){fprintf(stderr,"%s failed at %d:%d: %s\n",stage,s?s->line:0,s?s->column:0,s?s->message:"unknown");return 1;}
int main(int argc,char**argv){if(argc!=2)return 64;char*src=read_file(argv[1]);if(!src)return 65;RmalStatus st={0};RmalProgram*p=rmal_parse_source(src,argv[1],&st);free(src);if(!p)return status("parse",&st);RmalBytecode*bc=rmal_compile(p,&st);if(!bc){rmal_program_free(p);return status("compile",&st);}RmalVm*vm=rmal_vm_create();if(!vm)return 66;InputHost h={0};
 struct B{const char*n;size_t a;RmalNativeFunction f;}b[]={{"BrowserInputSelect",1,select_fixture},{"BrowserPointerX",0,px_fn},{"BrowserPointerY",0,py_fn},{"BrowserKey",0,key_fn},{"BrowserHitCount",0,hit_count_fn},{"BrowserHitX",1,hx},{"BrowserHitY",1,hy},{"BrowserHitWidth",1,hw},{"BrowserHitHeight",1,hh},{"BrowserHitHref",1,href_fn},{"BrowserInitialPendingHref",0,pending_fn},{"BrowserInitialLastHit",0,last_fn},{"BrowserInitialFocusIndex",0,focus_fn},{"BrowserInitialFocusedHref",0,focused_fn},{"BrowserInputResult",8,result_fn}};
 for(size_t i=0;i<sizeof(b)/sizeof(b[0]);++i){st=rmal_vm_bind_native(vm,b[i].n,b[i].a,b[i].f,&h);if(!st.ok){rmal_vm_free(vm);rmal_bytecode_free(bc);rmal_program_free(p);return status("bind",&st);}}
 RmalValue rv={0};st=rmal_vm_run(vm,bc,true,&rv);rmal_value_free(&rv);int rc=0;if(!st.ok)rc=status("run",&st);else if(h.results!=FIXTURE_COUNT){fprintf(stderr,"input results incomplete\n");rc=67;}else printf("RMAL_INPUT_RECEIPT fixtures=%zu policy_in_rmal=true python_runtime_used=false\n",h.results);rmal_vm_free(vm);rmal_bytecode_free(bc);rmal_program_free(p);return rc;}
