package org.rmaos.mingx;
import org.rmaos.mingx.generated.MiniGXGraph;import java.nio.charset.StandardCharsets;import java.security.MessageDigest;import java.util.Locale;
public final class MiniGXGameState {
 private static final String[] WAYS={"FORWARD","BACKWARD","UP","DOWN","SIDEWAYS","INWARD","OUTWARD","AROUND","THROUGH","REVERSE","BRANCH","HOMEWARD"};
 private int serial=0,wayMask,hits,combo=1,ash,ember,survivor;private String objectId,status,lastWay="AROUND";private float integrity;private boolean bbf;private long score;
 public MiniGXGameState(){spawn();}
 private static String shortHash(String s){try{byte[]d=MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8));StringBuilder b=new StringBuilder();for(int i=0;i<4;i++)b.append(String.format(Locale.US,"%02x",d[i]));return b.toString();}catch(Exception e){return"00000000";}}
 private void spawn(){serial++;objectId="CYC:MGX:"+shortHash(MiniGXGraph.DIGEST+":"+serial);int seed=(int)Long.parseLong(shortHash(objectId),16);integrity=.72f+((seed&255)/255f)*.25f;wayMask=0;hits=0;bbf=false;status="GENERATED";}
 private static int bit(int w){return 1<<Math.floorMod(w,WAYS.length);} private static int bits(int x){return Integer.bitCount(x);}
 public synchronized void pulse(int way){if(status.equals("ASH")||status.equals("SURVIVOR"))spawn();int w=Math.floorMod(way,WAYS.length);lastWay=WAYS[w];wayMask|=bit(w);hits++;float repeated=Math.max(0,hits-bits(wayMask));integrity-=.035f+.015f*repeated+.012f*((serial*31+w*17)%7);long pts=Math.max(1,Math.round(25f*(1f+bits(wayMask)*.22f)));score+=pts*combo;if(integrity<=0){status="ASH";ash++;combo=1;return;}if(bits(wayMask)>=3&&status.equals("GENERATED")){status="EMBER";ember++;score+=150;combo=Math.min(9,combo+1);}if(bits(wayMask)>=6&&bbf&&integrity>.28f&&!status.equals("SURVIVOR")){status="SURVIVOR";survivor++;score+=1000L*combo;combo=Math.min(12,combo+2);}}
 public synchronized void reverse(){lastWay="REVERSE";wayMask|=bit(9);bbf=true;score+=80;} public synchronized void homeward(){lastWay="HOMEWARD";wayMask|=bit(11);}
 public synchronized String objectId(){return objectId;}public synchronized String status(){return status;}public synchronized String lastWay(){return lastWay;}public synchronized float integrity(){return Math.max(0,integrity);}public synchronized long score(){return score;}public synchronized int combo(){return combo;}public synchronized int ash(){return ash;}public synchronized int ember(){return ember;}public synchronized int survivor(){return survivor;}public synchronized int uniqueWays(){return bits(wayMask);}
}
