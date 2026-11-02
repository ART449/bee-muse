package com.iartlabs.beemuse;

import android.app.*;
import android.app.role.RoleManager;
import android.content.*;
import android.content.pm.*;
import android.os.*;
import android.provider.Settings;
import android.speech.RecognizerIntent;
import android.widget.*;
import java.util.*;

/** Local user entry point; intent extras never execute device actions. */
public class DeviceActivity extends Activity {
  private LinearLayout body;
  private EditText command;
  private TextView status;
  private String expected="";
  private android.content.SharedPreferences preferences;
  @Override public void onCreate(Bundle saved){
    super.onCreate(saved);preferences=getSharedPreferences("device",0);
    BeeAccessibilityService service=BeeAccessibilityService.active;expected=service==null?"":service.target();
    ScrollView scroll=new ScrollView(this);body=new LinearLayout(this);body.setOrientation(1);body.setPadding(24,24,24,32);scroll.addView(body);setContentView(scroll);
    label("Bee-Muse · Asistente del teléfono");
    label("Da una orden concreta. Los gestos actúan en la aplicación anterior. Puedes revocar cada acceso en Ajustes de Android.");
    button("Habilitar control de pantalla",()->{new AlertDialog.Builder(this).setMessage("Permite leer elementos visibles y realizar gestos por tus órdenes. Bee-Muse no opera en pantallas de contraseñas ni aprueba permisos. Activa Bee-Muse en la siguiente pantalla si quieres este control.").setPositiveButton("Abrir ajustes",(d,w)->startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))).setNegativeButton("Cancelar",null).show();});
    button("Elegir Bee-Muse como asistente",()->{if(checkSelfPermission(android.Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{android.Manifest.permission.RECORD_AUDIO},23);return;}if(Build.VERSION.SDK_INT>=29){RoleManager roles=getSystemService(RoleManager.class);if(roles.isRoleAvailable(RoleManager.ROLE_ASSISTANT)){startActivityForResult(roles.createRequestRoleIntent(RoleManager.ROLE_ASSISTANT),22);return;}}startActivity(new Intent(Settings.ACTION_VOICE_INPUT_SETTINGS));});
    button("Autorizar acceso a notificaciones",()->startActivity(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)));
    button("Elegir aplicaciones para avisos hablados",this::chooseApps);
    toggle("Anunciar notificaciones · voz del teléfono","announce");
    toggle("Incluir remitente si la notificación lo identifica","sender");
    toggle("Avisar cuando Android muestre una solicitud de permiso","permissions");
    command=new EditText(this);command.setHint("abre WhatsApp · baja · pulsa Buscar");body.addView(command);
    button("Ejecutar la orden escrita",()->execute(command.getText().toString()));
    button("Dictar y ejecutar una orden",()->{
      BeeAccessibilityService current=BeeAccessibilityService.active;if(current!=null&&!current.target().isEmpty())expected=current.target();
      Intent intent=new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE,"es-MX");intent.putExtra(RecognizerIntent.EXTRA_PROMPT,"Orden para Bee-Muse: abrir, pulsar, desplazar, volver o inicio");
      try{startActivityForResult(intent,20);}catch(ActivityNotFoundException e){status.setText("No hay reconocimiento de voz disponible. Puedes escribir la orden.");}
    });
    button("Abrir navegador Bee-Muse",()->startActivity(new Intent(this,BrowserActivity.class)));
    button("Ver últimas acciones",()->new AlertDialog.Builder(this).setTitle("Registro local de acciones").setMessage(ActionJournal.latest(this)).setPositiveButton("Cerrar",null).show());
    status=label("Voz del teléfono. El acceso como asistente no activa escucha continua.");
  }
  private TextView label(String text){TextView v=new TextView(this);v.setText(text);v.setTextSize(17);v.setPadding(0,12,0,12);body.addView(v);return v;}
  private void button(String text,Runnable run){Button b=new Button(this);b.setText(text);b.setOnClickListener(v->run.run());body.addView(b);}
  private void toggle(String title,String key){Switch t=new Switch(this);t.setText(title);t.setChecked(preferences.getBoolean(key,false));t.setOnCheckedChangeListener((v,on)->preferences.edit().putBoolean(key,on).apply());body.addView(t);}
  private List<ResolveInfo> apps(){Intent query=new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER);List<ResolveInfo> rows=getPackageManager().queryIntentActivities(query,0);rows.sort(Comparator.comparing(r->r.loadLabel(getPackageManager()).toString(),String.CASE_INSENSITIVE_ORDER));return rows;}
  private void chooseApps(){
    List<ResolveInfo> rows=apps();List<String> packages=new ArrayList<>(),labels=new ArrayList<>();for(ResolveInfo r:rows){String p=r.activityInfo.packageName;if(!packages.contains(p)){packages.add(p);labels.add(r.loadLabel(getPackageManager()).toString());}}
    Set<String> chosen=new HashSet<>(preferences.getStringSet("apps",Collections.emptySet()));boolean[] checked=new boolean[packages.size()];for(int i=0;i<checked.length;i++)checked[i]=chosen.contains(packages.get(i));
    new AlertDialog.Builder(this).setTitle("Avisos sólo de estas aplicaciones").setMultiChoiceItems(labels.toArray(new String[0]),checked,(d,i,on)->{if(on)chosen.add(packages.get(i));else chosen.remove(packages.get(i));}).setPositiveButton("Guardar",(d,w)->preferences.edit().putStringSet("apps",chosen).apply()).setNegativeButton("Cancelar",null).show();
  }
  private void execute(String text){
    try{
      DeviceActions action=DeviceActions.parse(text);
      if(action.type.equals("open")){
        List<ResolveInfo> matches=new ArrayList<>();for(ResolveInfo app:apps())if(DeviceActions.normalize(app.loadLabel(getPackageManager()).toString()).equals(action.argument))matches.add(app);
        if(matches.size()!=1)throw new IllegalArgumentException("No hay una aplicación única con ese nombre. Usa el nombre exacto del lanzador.");
        ResolveInfo r=matches.get(0);Intent open=new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER).setComponent(new ComponentName(r.activityInfo.packageName,r.activityInfo.name)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(open);ActionJournal.record(this,"open","Android aceptó abrir la aplicación; comprueba su pantalla.");status.setText("Se solicitó abrir la aplicación.");return;
      }
      if(action.type.equals("unlock")){getSystemService(KeyguardManager.class).requestDismissKeyguard(this,new KeyguardManager.KeyguardDismissCallback(){@Override public void onDismissSucceeded(){status.setText("Android confirmó el desbloqueo.");ActionJournal.record(DeviceActivity.this,"unlock","Android confirmó el desbloqueo.");}@Override public void onDismissCancelled(){status.setText("Desbloqueo cancelado.");}@Override public void onDismissError(){status.setText("Android no pudo iniciar el desbloqueo desde esta pantalla.");}});return;}
      BeeAccessibilityService service=BeeAccessibilityService.active;if(service==null)throw new IllegalArgumentException("Activa primero el control de Bee-Muse en Accesibilidad.");
      if(expected.isEmpty())throw new IllegalArgumentException("Abre primero la aplicación que quieras controlar y convoca Bee-Muse como asistente.");
      String target=expected;moveTaskToBack(true);finish();
      new Handler(Looper.getMainLooper()).postDelayed(()->{if(BeeAccessibilityService.active!=service){Toast.makeText(getApplicationContext(),"El acceso de pantalla se desactivó.",Toast.LENGTH_LONG).show();return;}service.execute(action,target,result->Toast.makeText(getApplicationContext(),result,Toast.LENGTH_LONG).show());},650);
    }catch(Exception e){status.setText(e.getMessage()==null?"No se pudo ejecutar la orden.":e.getMessage());}
  }
  @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request==20&&result==RESULT_OK&&data!=null){ArrayList<String> words=data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);if(words!=null&&!words.isEmpty()){command.setText(words.get(0));execute(words.get(0));}}}
}
