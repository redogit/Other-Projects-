package org.rmaos.mingx;
import android.content.Context;import org.json.*;import org.rmaos.mingx.generated.MiniGXGraph;import java.io.InputStream;import java.nio.charset.StandardCharsets;
public final class MiniGXCircuit {
 public final String digest;public final int nodeCount,edgeCount;
 private MiniGXCircuit(String d,int n,int e){digest=d;nodeCount=n;edgeCount=e;}
 public static MiniGXCircuit load(Context c){try(InputStream in=c.getAssets().open("minigx/five_eyes_fermat_fire.minigx.json")){JSONObject r=new JSONObject(new String(in.readAllBytes(),StandardCharsets.UTF_8));if(!MiniGXGraph.SCHEMA.equals(r.getString("schema")))throw new IllegalStateException("schema mismatch");if(!MiniGXGraph.DIGEST.equals(r.getString("digest")))throw new IllegalStateException("digest mismatch");JSONArray n=r.getJSONArray("nodes"),e=r.getJSONArray("edges");if(n.length()!=MiniGXGraph.NODE_COUNT||e.length()!=MiniGXGraph.EDGE_COUNT)throw new IllegalStateException("cardinality mismatch");return new MiniGXCircuit(r.getString("digest"),n.length(),e.length());}catch(Exception e){throw new IllegalStateException("MiniGX circuit load failed",e);}}
}
