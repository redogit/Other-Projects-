#include "rmal/rmal.h"

#include <inttypes.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct UrlFixture {
    const char *name;
    const char *input;
    const char *raw;
    const char *scheme;
    const char *authority;
    const char *path;
    const char *canonical;
    const char *kind;
    const char *page_id;
    bool network_required;
    const char *pending_href;
    const char *residual_kind;
    const char *residual_detail;
    const char *consequence;
} UrlFixture;

typedef struct UrlHost {
    const UrlFixture *current;
    size_t results;
} UrlHost;

static const UrlFixture FIXTURES[] = {
    {"local_absolute","rmapl://local/page2","rmapl://local/page2","rmapl","local","/page2","rmapl://local/page2","local","page2",false,"page2","local-navigation-pending","url-resolved-local","local-url-resolved"},
    {"local_relative","page2","page2","rmapl","local","/page2","rmapl://local/page2","local","page2",false,"page2","local-navigation-pending","url-resolved-local","local-url-resolved"},
    {"https_path","https://example.com/docs","https://example.com/docs","https","example.com","/docs","https://example.com/docs","network","",true,"https://example.com/docs","network-transport-pending","url-resolved-network-unavailable","network-url-resolved"},
    {"http_root","http://example.com","http://example.com","http","example.com","/","http://example.com/","network","",true,"http://example.com","network-transport-pending","url-resolved-network-unavailable","network-url-resolved"},
    {"invalid_query","https://example.com/a?b","","","","","","",false,"https://example.com/a?b","url-invalid","unsupported-or-malformed-url","url-invalid"},
    {"invalid_empty_local","rmapl://local/","","","","","","",false,"rmapl://local/","url-invalid","unsupported-or-malformed-url","url-invalid"},
    {"invalid_empty","","","","","","","","",false,"","url-invalid","unsupported-or-malformed-url","url-invalid"}
};
static const size_t FIXTURE_COUNT=sizeof(FIXTURES)/sizeof(FIXTURES[0]);

static RmalStatus ok_status(void){RmalStatus s={0};s.ok=true;return s;}
static RmalStatus err(const char *m){RmalStatus s={0};snprintf(s.message,sizeof(s.message),"%s",m);return s;}
static char *dup_text(const char *t){size_t n=strlen(t)+1U;char *p=(char*)malloc(n);if(p)memcpy(p,t,n);return p;}

static int string_eq(const RmalValue *v,const char *e){
    return v&&v->kind==RMAL_VALUE_STRING&&v->as.string&&strcmp(v->as.string,e)==0;
}

static RmalStatus select_fixture(void *ctx,const RmalValue *a,size_t n,RmalValue *r){
    UrlHost *h=(UrlHost*)ctx;
    if(!h||n!=1U||a[0].kind!=RMAL_VALUE_STRING||!a[0].as.string)return err("BrowserUrlSelect requires one string");
    h->current=NULL;
    for(size_t i=0;i<FIXTURE_COUNT;++i)if(strcmp(a[0].as.string,FIXTURES[i].name)==0){h->current=&FIXTURES[i];break;}
    if(!h->current)return err("unknown URL fixture");
    size_t z=strlen(h->current->name)+sizeof(":ACK");char *ack=(char*)malloc(z);
    if(!ack)return err("URL select allocation failed");
    snprintf(ack,z,"%s:ACK",h->current->name);r->kind=RMAL_VALUE_STRING;r->as.string=ack;return ok_status();
}

static RmalStatus raw_value(void *ctx,const RmalValue *a,size_t n,RmalValue *r){
    (void)a;UrlHost *h=(UrlHost*)ctx;if(!h||!h->current||n!=0U)return err("BrowserUrlRaw requires selected fixture");
    r->kind=RMAL_VALUE_STRING;r->as.string=dup_text(h->current->input);return r->as.string?ok_status():err("URL raw allocation failed");
}

static RmalStatus length_value(void *ctx,const RmalValue *a,size_t n,RmalValue *r){
    (void)a;UrlHost *h=(UrlHost*)ctx;if(!h||!h->current||n!=0U)return err("BrowserUrlLength requires selected fixture");
    r->kind=RMAL_VALUE_INT;r->as.integer=(int64_t)strlen(h->current->input);return ok_status();
}

static RmalStatus byte_value(void *ctx,const RmalValue *a,size_t n,RmalValue *r){
    UrlHost *h=(UrlHost*)ctx;if(!h||!h->current||n!=1U||a[0].kind!=RMAL_VALUE_INT||a[0].as.integer<0)return err("BrowserUrlByte requires nonnegative index");
    size_t i=(size_t)a[0].as.integer;size_t len=strlen(h->current->input);if(i>=len)return err("BrowserUrlByte index outside input");
    r->kind=RMAL_VALUE_INT;r->as.integer=(unsigned char)h->current->input[i];return ok_status();
}

static RmalStatus char_value(void *ctx,const RmalValue *a,size_t n,RmalValue *r){
    UrlHost *h=(UrlHost*)ctx;if(!h||!h->current||n!=1U||a[0].kind!=RMAL_VALUE_INT||a[0].as.integer<0)return err("BrowserUrlChar requires nonnegative index");
    size_t i=(size_t)a[0].as.integer;size_t len=strlen(h->current->input);if(i>=len)return err("BrowserUrlChar index outside input");
    unsigned char c=(unsigned char)h->current->input[i];
    char tmp[2]={0,0};if(c>0U&&c<128U)tmp[0]=(char)c;
    r->kind=RMAL_VALUE_STRING;r->as.string=dup_text(tmp);return r->as.string?ok_status():err("URL char allocation failed");
}

static RmalStatus url_result(void *ctx,const RmalValue *a,size_t n,RmalValue *r){
    UrlHost *h=(UrlHost*)ctx;
    if(!h||!h->current||n!=12U||a[7].kind!=RMAL_VALUE_BOOL)return err("BrowserUrlResult contract violated");
    const UrlFixture *e=h->current;
    if(!string_eq(&a[0],e->raw)||!string_eq(&a[1],e->scheme)||!string_eq(&a[2],e->authority)||
       !string_eq(&a[3],e->path)||!string_eq(&a[4],e->canonical)||!string_eq(&a[5],e->kind)||
       !string_eq(&a[6],e->page_id)||a[7].as.boolean!=e->network_required||
       !string_eq(&a[8],e->pending_href)||!string_eq(&a[9],e->residual_kind)||
       !string_eq(&a[10],e->residual_detail)||!string_eq(&a[11],e->consequence))
        return err("RMAL URL result differs from fixture contract");

    printf("RMAL_URL fixture=%s raw_hex=",e->name);
    for(const unsigned char *p=(const unsigned char*)a[0].as.string;*p;++p)printf("%02x",(unsigned int)*p);
    printf(" scheme=%s authority=%s path=%s canonical=%s kind=%s page=%s network=%s pending_hex=",
           a[1].as.string,a[2].as.string,a[3].as.string,a[4].as.string,a[5].as.string,a[6].as.string,
           a[7].as.boolean?"true":"false");
    for(const unsigned char *p=(const unsigned char*)a[8].as.string;*p;++p)printf("%02x",(unsigned int)*p);
    printf(" residual=%s detail=%s consequence=%s\n",a[9].as.string,a[10].as.string,a[11].as.string);

    size_t z=strlen(e->consequence)+sizeof(":ACK");char *ack=(char*)malloc(z);
    if(!ack)return err("URL result allocation failed");
    snprintf(ack,z,"%s:ACK",e->consequence);r->kind=RMAL_VALUE_STRING;r->as.string=ack;h->results+=1U;return ok_status();
}

static FILE *open_read(const char *p){
#if defined(_WIN32)
    FILE *f=NULL;if(fopen_s(&f,p,"rb")!=0)return NULL;return f;
#else
    return fopen(p,"rb");
#endif
}
static char *read_file(const char *p){FILE *f=open_read(p);if(!f)return NULL;if(fseek(f,0,SEEK_END)!=0){fclose(f);return NULL;}long e=ftell(f);if(e<0){fclose(f);return NULL;}rewind(f);size_t n=(size_t)e;char *b=(char*)malloc(n+1U);if(!b){fclose(f);return NULL;}size_t g=fread(b,1U,n,f);fclose(f);if(g!=n){free(b);return NULL;}b[n]='\0';return b;}
static int print_status(const char *stage,const RmalStatus *s){fprintf(stderr,"%s failed at %d:%d: %s\n",stage,s?s->line:0,s?s->column:0,s?s->message:"unknown");return 1;}

int main(int argc,char **argv){
    if(argc!=2){fprintf(stderr,"usage: browser_rmal_url_host <browser_url_resolve.rmal>\n");return 64;}
    char *src=read_file(argv[1]);if(!src)return 65;RmalStatus st={0};RmalProgram *p=rmal_parse_source(src,argv[1],&st);free(src);if(!p)return print_status("parse",&st);
    RmalBytecode *bc=rmal_compile(p,&st);if(!bc){rmal_program_free(p);return print_status("compile",&st);}RmalVm *vm=rmal_vm_create();if(!vm){rmal_bytecode_free(bc);rmal_program_free(p);return 66;}
    UrlHost host={0};
    struct B{const char *name;size_t arity;RmalNativeFunction fn;} b[]={
        {"BrowserUrlSelect",1U,select_fixture},{"BrowserUrlRaw",0U,raw_value},{"BrowserUrlLength",0U,length_value},
        {"BrowserUrlByte",1U,byte_value},{"BrowserUrlChar",1U,char_value},{"BrowserUrlResult",12U,url_result}
    };
    for(size_t i=0;i<sizeof(b)/sizeof(b[0]);++i){st=rmal_vm_bind_native(vm,b[i].name,b[i].arity,b[i].fn,&host);if(!st.ok){rmal_vm_free(vm);rmal_bytecode_free(bc);rmal_program_free(p);return print_status("bind",&st);}}
    RmalValue result={0};st=rmal_vm_run(vm,bc,true,&result);rmal_value_free(&result);int rc=0;
    if(!st.ok)rc=print_status("run",&st);else if(host.results!=FIXTURE_COUNT){fprintf(stderr,"URL results incomplete: %zu/%zu\n",host.results,FIXTURE_COUNT);rc=67;}
    else printf("RMAL_URL_RECEIPT fixtures=%zu policy_in_rmal=true python_runtime_used=false\n",host.results);
    rmal_vm_free(vm);rmal_bytecode_free(bc);rmal_program_free(p);return rc;
}
