package com.iartlabs.beemuse;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.provider.DocumentsContract;
import android.speech.RecognizerIntent;
import android.speech.tts.TextToSpeech;
import android.view.View;
import android.webkit.WebView;
import android.widget.*;
import org.json.*;
import javax.net.ssl.HttpsURLConnection;
import java.io.*;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
  private LinearLayout layout, results;
  private EditText host, code, message, extension;
  private TextView status, chat;
  private WebView companion;
  private CheckBox speak;
  private TextToSpeech tts;
  private String origin="", cookie="";
  private final JSONArray history=new JSONArray();
  private final java.util.concurrent.ExecutorService worker=Executors.newSingleThreadExecutor();
  private boolean busy=false;
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    ScrollView scroll=new ScrollView(this);layout=new LinearLayout(this);layout.setOrientation(1);layout.setPadding(24,32,24,32);layout.setBackgroundColor(Color.rgb(18,16,25));scroll.addView(layout);setContentView(scroll);
    text("Bee-Muse · IArtLabs",26);text("Muse + tus herramientas. Archivos del teléfono y conversación.",15);
    companion=new WebView(this);companion.setBackgroundColor(Color.TRANSPARENT);companion.getSettings().setJavaScriptEnabled(false);layout.addView(companion,new LinearLayout.LayoutParams(-1,160));animate("waving");
    host=input("Servidor HTTPS de Bee-Muse",false);host.setText(getPreferences(0).getString("host",""));code=input("Código de emparejamiento",true);button("Conectar mi dispositivo",v->pair());
    status=text("Elige archivos locales o conecta tu servidor para conversar con Muse.",14);
    button("Elegir carpeta del teléfono",v->{Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);startActivityForResult(i,10);});
    extension=input("Filtrar extensión: html, png, pdf… (vacío: todos)",false);
    results=new LinearLayout(this);results.setOrientation(1);layout.addView(results);
    chat=text("",16);message=input("Habla con Muse o pide una tarea",false);message.setSingleLine(false);message.setMinLines(3);
    button("Enviar a Muse",v->send());button("Dictar · reconocimiento del teléfono",v->{Intent i=new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);i.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);i.putExtra(RecognizerIntent.EXTRA_LANGUAGE,"es-MX");try{startActivityForResult(i,11);}catch(Exception e){status.setText("Este teléfono no tiene reconocimiento de voz disponible.");}});
    speak=new CheckBox(this);speak.setText("Leer respuestas · voz del teléfono");speak.setTextColor(Color.WHITE);layout.addView(speak);button("Detener voz",v->{if(tts!=null)tts.stop();});
    tts=new TextToSpeech(this,result->{if(result==TextToSpeech.SUCCESS)tts.setLanguage(new Locale("es","MX"));});
  }
  private TextView text(String value,int size){TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(Color.WHITE);t.setPadding(0,12,0,12);layout.addView(t);return t;}
  private EditText input(String hint,boolean secret){EditText t=new EditText(this);t.setHint(hint);t.setHintTextColor(Color.LTGRAY);t.setTextColor(Color.WHITE);if(secret)t.setInputType(129);layout.addView(t);return t;}
  private void button(String label,View.OnClickListener action){Button b=new Button(this);b.setText(label);b.setOnClickListener(action);layout.addView(b);}
  private void animate(String state){companion.loadDataWithBaseURL("file:///android_asset/","<html><body style='margin:0;background:transparent;text-align:right'><img alt='CyberBee y OctoHype' height='150' src='companion/"+state+".gif'></body></html>","text/html","UTF-8",null);}
  private JSONObject request(String path,JSONObject body,boolean pairing)throws Exception{
    HttpsURLConnection conn=(HttpsURLConnection)new URL(origin+path).openConnection();conn.setConnectTimeout(15000);conn.setReadTimeout(270000);conn.setInstanceFollowRedirects(false);if(!pairing)conn.setRequestProperty("Cookie",cookie);
    if(body!=null){conn.setRequestMethod("POST");conn.setDoOutput(true);conn.setRequestProperty("Content-Type","application/json");try(OutputStream out=conn.getOutputStream()){out.write(body.toString().getBytes(StandardCharsets.UTF_8));}}
    int response=conn.getResponseCode();InputStream stream=response<400?conn.getInputStream():conn.getErrorStream();ByteArrayOutputStream data=new ByteArrayOutputStream();byte[] buffer=new byte[8192];int count;try{while(stream!=null&&(count=stream.read(buffer))!=-1){if(data.size()+count>4000000)throw new IOException("Respuesta demasiado grande");data.write(buffer,0,count);}}finally{if(stream!=null)stream.close();}
    JSONObject result=new JSONObject(data.toString("UTF-8"));if(response>=400)throw new IOException(result.optString("error","El servidor no completó la solicitud."));
    if(pairing){String header=conn.getHeaderField("Set-Cookie");if(header==null||!header.startsWith("bee_remote="))throw new IOException("El servidor no confirmó el emparejamiento.");cookie=header.split(";",2)[0];}conn.disconnect();return result;
  }
  private void pair(){if(busy)return;try{Uri uri=Uri.parse(host.getText().toString().trim());if(!"https".equals(uri.getScheme())||uri.getHost()==null||uri.getUserInfo()!=null||uri.getQuery()!=null||uri.getFragment()!=null||!(uri.getPath()==null||uri.getPath().isEmpty()||uri.getPath().equals("/")))throw new Exception();origin=uri.buildUpon().path("").build().toString();}catch(Exception e){status.setText("Escribe la dirección HTTPS del servidor, sin claves en la URL.");return;}String pairingCode=code.getText().toString().trim();busy=true;animate("waiting");worker.execute(()->{try{request("/pair",new JSONObject().put("code",pairingCode),true);runOnUiThread(()->{code.setText("");getPreferences(0).edit().putString("host",origin).apply();status.setText("Dispositivo conectado. La sesión se conserva sólo mientras la aplicación está abierta.");animate("jumping");});}catch(Exception e){error(e);}finally{busy=false;}});}
  private void send(){if(busy)return;if(cookie.isEmpty()){status.setText("Conecta tu servidor de Muse primero.");return;}String prompt=message.getText().toString().trim();if(prompt.isEmpty())return;busy=true;message.setText("");chat.append("\nTú: "+prompt+"\n");animate("running");worker.execute(()->{try{JSONObject started=request("/api/muse/start",new JSONObject().put("message",prompt).put("history",history),false);String id=started.getString("id");JSONObject job;do{Thread.sleep(1200);job=request("/api/muse/job?id="+id,null,false);}while(job.getString("state").equals("running"));if(!job.getString("state").equals("completed"))throw new IOException(job.optString("error"));String answer=job.getJSONObject("result").getString("message");history.put(new JSONObject().put("role","user").put("content",prompt));history.put(new JSONObject().put("role","assistant").put("content",answer.substring(0,Math.min(8000,answer.length()))));while(history.length()>8)history.remove(0);runOnUiThread(()->{chat.append("\nMuse: "+answer+"\n");animate("jumping");if(speak.isChecked()&&tts!=null)tts.speak(answer,TextToSpeech.QUEUE_FLUSH,null,"muse");});}catch(Exception e){error(e);}finally{busy=false;}});}
  private void error(Exception e){runOnUiThread(()->{status.setText(e.getMessage()==null?"No se pudo completar la operación.":e.getMessage());animate("failed");});}
  @Override protected void onActivityResult(int req,int result,Intent data){super.onActivityResult(req,result,data);if(result!=RESULT_OK||data==null)return;if(req==11){ArrayList<String> words=data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);if(words!=null&&!words.isEmpty())message.setText(words.get(0));return;}if(req==10){Uri tree=data.getData();getContentResolver().takePersistableUriPermission(tree,Intent.FLAG_GRANT_READ_URI_PERMISSION);results.removeAllViews();String suffix=extension.getText().toString().trim().toLowerCase(Locale.ROOT).replaceFirst("^\\.","");animate("running");worker.execute(()->{try{int[] budget={0};list(tree,DocumentsContract.getTreeDocumentId(tree),suffix,budget);runOnUiThread(()->{status.setText(budget[0]+" entradas revisadas. Sólo la carpeta elegida; hasta 5000 entradas por recorrido.");animate("review");});}catch(Exception e){error(e);}});}}
  private void list(Uri tree,String parent,String suffix,int[] budget)throws Exception{if(budget[0]>=5000)return;Uri children=DocumentsContract.buildChildDocumentsUriUsingTree(tree,parent);try(Cursor rows=getContentResolver().query(children,new String[]{DocumentsContract.Document.COLUMN_DOCUMENT_ID,DocumentsContract.Document.COLUMN_DISPLAY_NAME,DocumentsContract.Document.COLUMN_MIME_TYPE},null,null,null)){if(rows==null)return;while(rows.moveToNext()&&budget[0]<5000){budget[0]++;String id=rows.getString(0),name=rows.getString(1),mime=rows.getString(2);if(DocumentsContract.Document.MIME_TYPE_DIR.equals(mime)){list(tree,id,suffix,budget);continue;}if(!suffix.isEmpty()&&!name.toLowerCase(Locale.ROOT).endsWith("."+suffix))continue;Uri file=DocumentsContract.buildDocumentUriUsingTree(tree,id);runOnUiThread(()->{Button b=new Button(this);b.setText(name);b.setOnClickListener(v->{Intent open=new Intent(Intent.ACTION_VIEW);open.setDataAndType(file,mime);open.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);try{startActivity(open);}catch(Exception e){status.setText("No hay una aplicación para abrir este tipo de archivo.");}});results.addView(b);});}}}
  @Override protected void onDestroy(){worker.shutdownNow();if(tts!=null){tts.stop();tts.shutdown();}companion.destroy();super.onDestroy();}
}
