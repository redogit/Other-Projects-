package org.rmaos.mingx;

import android.content.Context;
import org.json.JSONArray;
import org.json.JSONObject;
import org.rmaos.mingx.generated.MiniGXGraph;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class MiniGXCircuit {
    private static final Set<String> RUNTIME_OPS = Set.of(
        "W114_CENTER","FERMAT_FIRE","FIVE_EYES","ALL_WAYS","FRACTAL_BRANCHES","GPU_SPARKS",
        "COGNATE_FILAMENTS","PULSE_OSCILLATOR","FRAME_FEEDBACK","BLOOM_TONEMAP","TRACE_TAP","HOMEWARD","SURVIVOR_SCORE"
    );
    private static final String WAYS="FORWARD,BACKWARD,UP,DOWN,SIDEWAYS,INWARD,OUTWARD,AROUND,THROUGH,REVERSE,BRANCH,HOMEWARD";
    public static final class NodeSpec {
        public final String id,family,op; public final int stage; private final JSONObject params;
        private NodeSpec(JSONObject row) throws Exception {id=row.getString("id");family=row.getString("family");op=row.getString("op");stage=row.getInt("stage");params=row.getJSONObject("params");}
        public String param(String key){if(!params.has(key))throw new IllegalStateException("Missing MiniGX param "+op+"."+key);return params.optString(key,null);}
        public int intParam(String key){return Integer.parseInt(param(key));}
        public float floatParam(String key){return Float.parseFloat(param(key));}
    }
    public final String digest; public final int nodeCount,edgeCount; private final Map<String,List<NodeSpec>> byOp;
    private MiniGXCircuit(String d,int n,int e,Map<String,List<NodeSpec>> ops){digest=d;nodeCount=n;edgeCount=e;byOp=ops;}
    public NodeSpec one(String op){List<NodeSpec> rows=byOp.get(op);if(rows==null||rows.size()!=1)throw new IllegalStateException("Expected exactly one runtime op "+op+", got "+(rows==null?0:rows.size()));return rows.get(0);}
    public String param(String op,String key){return one(op).param(key);} public int intParam(String op,String key){return one(op).intParam(key);} public float floatParam(String op,String key){return one(op).floatParam(key);}
    private static void requireEq(NodeSpec n,String key,String expected){String got=n.param(key);if(!expected.equals(got))throw new IllegalStateException("Unsupported MiniGX value "+n.op+"."+key+"="+got);}
    private static void requireInt(NodeSpec n,String key,int lo,int hi){int v=n.intParam(key);if(v<lo||v>hi)throw new IllegalStateException("MiniGX integer out of range "+n.op+"."+key+"="+v);}
    private static void requireFloat(NodeSpec n,String key,float lo,float hi){float v=n.floatParam(key);if(!Float.isFinite(v)||v<lo||v>hi)throw new IllegalStateException("MiniGX float out of range "+n.op+"."+key+"="+v);}
    private static void requireShaderPath(NodeSpec n,String key){String p=n.param(key);if(!p.startsWith("shaders/")||p.contains("..")||p.contains("\\")||p.startsWith("/"))throw new IllegalStateException("Unsafe MiniGX shader path "+p);}
    private void validateBackendContract(){
        NodeSpec center=one("W114_CENTER");requireEq(center,"degree","114");requireEq(center,"alpha","1,7,78,79,86,91");requireEq(center,"target","x1^6*x2^77*x3^78*x4^85*x5^90");
        NodeSpec fire=one("FERMAT_FIRE");requireInt(fire,"ray_steps",1,64);requireEq(fire,"quality_dynamic","true");requireEq(fire,"palette","ember");requireShaderPath(fire,"vertex_shader");requireShaderPath(fire,"shader");
        NodeSpec eyes=one("FIVE_EYES");requireEq(eyes,"count","5");requireEq(eyes,"simultaneous","true");
        requireEq(one("ALL_WAYS"),"ways",WAYS);
        NodeSpec branches=one("FRACTAL_BRANCHES");requireInt(branches,"depth",1,15);requireInt(branches,"fanout",1,15);if(branches.intParam("depth")*branches.intParam("fanout")>15)throw new IllegalStateException("MiniGX branch budget exceeds shader backend");
        NodeSpec sparks=one("GPU_SPARKS");requireInt(sparks,"count",1,96);requireFloat(sparks,"feedback",0f,1f);
        requireEq(one("COGNATE_FILAMENTS"),"boundary","COGNATE!=IDENTITY");
        NodeSpec signal=one("PULSE_OSCILLATOR");requireFloat(signal,"bpm",1f,400f);requireEq(signal,"audio_optional","true");
        NodeSpec feedback=one("FRAME_FEEDBACK");requireFloat(feedback,"decay",0f,1f);requireFloat(feedback,"mix",0f,1f);
        NodeSpec post=one("BLOOM_TONEMAP");requireFloat(post,"bloom",0f,4f);requireFloat(post,"exposure",.1f,4f);
        NodeSpec trace=one("TRACE_TAP");requireEq(trace,"schema","rmaos/minigx-trace/v1");requireEq(trace,"authority","method-only");
        NodeSpec home=one("HOMEWARD");requireEq(home,"recenter","true");requireEq(home,"preserve_trace","true");
        requireEq(one("SURVIVOR_SCORE"),"game_score_not_evidence","true");
    }
    public static MiniGXCircuit load(Context c){
        try(InputStream in=c.getAssets().open("minigx/five_eyes_fermat_fire.minigx.json")){
            JSONObject r=new JSONObject(new String(in.readAllBytes(),StandardCharsets.UTF_8));
            if(!MiniGXGraph.SCHEMA.equals(r.getString("schema")))throw new IllegalStateException("schema mismatch");
            if(!MiniGXGraph.DIGEST.equals(r.getString("digest")))throw new IllegalStateException("digest mismatch");
            JSONArray nodes=r.getJSONArray("nodes"),edges=r.getJSONArray("edges"),order=r.getJSONArray("execution_order");
            if(nodes.length()!=MiniGXGraph.NODE_COUNT||edges.length()!=MiniGXGraph.EDGE_COUNT)throw new IllegalStateException("cardinality mismatch");
            if(order.length()!=nodes.length())throw new IllegalStateException("execution order cardinality mismatch");
            Map<String,NodeSpec> byId=new HashMap<>();Map<String,List<NodeSpec>> byOp=new HashMap<>();
            for(int i=0;i<nodes.length();i++){NodeSpec n=new NodeSpec(nodes.getJSONObject(i));if(!RUNTIME_OPS.contains(n.op))throw new IllegalStateException("No MiniGX runtime backend for op "+n.op);if(byId.put(n.id,n)!=null)throw new IllegalStateException("duplicate runtime node "+n.id);byOp.computeIfAbsent(n.op,k->new ArrayList<>()).add(n);}
            Set<String> ordered=new HashSet<>();for(int i=0;i<order.length();i++){String id=order.getString(i);if(!byId.containsKey(id)||!ordered.add(id))throw new IllegalStateException("invalid execution order node "+id);}if(ordered.size()!=byId.size())throw new IllegalStateException("execution order incomplete");
            for(int i=0;i<edges.length();i++){JSONObject e=edges.getJSONObject(i);String src=e.getString("src"),dst=e.getString("dst"),rel=e.getString("relation");if(!byId.containsKey(src)||!byId.containsKey(dst))throw new IllegalStateException("runtime edge endpoint missing");if("FEEDBACK_TO".equals(rel)&&!"FEEDBACK".equals(byId.get(src).family))throw new IllegalStateException("runtime feedback source family mismatch");}
            MiniGXCircuit circuit=new MiniGXCircuit(r.getString("digest"),nodes.length(),edges.length(),byOp);for(String op:RUNTIME_OPS)circuit.one(op);circuit.validateBackendContract();return circuit;
        }catch(Exception e){throw new IllegalStateException("MiniGX circuit load failed",e);}
    }
}
