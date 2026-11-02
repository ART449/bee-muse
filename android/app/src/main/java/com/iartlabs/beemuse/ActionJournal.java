package com.iartlabs.beemuse;

import android.content.Context;
import org.json.*;
import java.util.UUID;

final class ActionJournal {
  private static final String SESSION=UUID.randomUUID().toString();
  static synchronized void record(Context context,String action,String result){
    android.content.SharedPreferences p=context.getSharedPreferences("device-actions",0);
    try{
      JSONArray old=new JSONArray(p.getString("receipts","[]")), rows=new JSONArray();
      String node=p.getString("node",null);if(node==null){node=UUID.randomUUID().toString();p.edit().putString("node",node).apply();}
      rows.put(new JSONObject().put("event_id",UUID.randomUUID().toString()).put("session_id",SESSION).put("node_id",node).put("time",System.currentTimeMillis()).put("action",action).put("result",result));
      for(int i=0;i<Math.min(49,old.length());i++)rows.put(old.get(i));
      p.edit().putString("receipts",rows.toString()).apply();
    }catch(JSONException ignored){android.util.Log.w("BeeMuse","Could not save action receipt");}
  }
  static String latest(Context c){try{JSONArray rows=new JSONArray(c.getSharedPreferences("device-actions",0).getString("receipts","[]"));StringBuilder out=new StringBuilder();for(int i=0;i<Math.min(10,rows.length());i++){JSONObject r=rows.getJSONObject(i);out.append(r.getString("action")).append(": ").append(r.getString("result")).append('\n');}return out.length()==0?"Todavía no hay acciones registradas.":out.toString();}catch(JSONException e){return "No se pudo leer el registro.";}}
}
