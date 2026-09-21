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
            MiniGXCircuit circuit=new MiniGXCircuit(r.getString("digest"),nodes.length(),edges.length(),byOp);for(String op:RUNTIME_OPS)circuit.one(op);
            if(circuit.intParam("FIVE_EYES","count")!=5)throw new IllegalStateException("Five Eyes count must be 5");
            if(circuit.param("ALL_WAYS","ways").split(",").length!=12)throw new IllegalStateException("ALL_WAYS must contain 12 directions");
            return circuit;
        }catch(Exception e){throw new IllegalStateException("MiniGX circuit load failed",e);}
    }
}
