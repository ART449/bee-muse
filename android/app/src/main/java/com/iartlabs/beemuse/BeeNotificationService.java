package com.iartlabs.beemuse;

import android.app.*;
import android.content.*;
import android.os.Build;
import android.service.notification.*;
import android.speech.tts.TextToSpeech;
import java.util.*;

/** No notification text is sent to Muse, a server, or the action executor. */
public class BeeNotificationService extends NotificationListenerService {
  private static BeeNotificationService active;
  private TextToSpeech tts;
  private boolean ready;
  private long lastPermission;
  private final Map<String,Long> recent=new HashMap<>();
  @Override public void onCreate(){super.onCreate();active=this;tts=new TextToSpeech(this,s->{ready=s==TextToSpeech.SUCCESS;if(ready)tts.setLanguage(new Locale("es","MX"));});}
  static void permissionNotice(){BeeNotificationService s=active;if(s==null||!s.ready||System.currentTimeMillis()-s.lastPermission<10000||!s.getSharedPreferences("device",0).getBoolean("permissions",false))return;s.lastPermission=System.currentTimeMillis();s.tts.speak("Android solicita un permiso. Revisa la pantalla para decidir.",TextToSpeech.QUEUE_ADD,null,"permission");}
  @Override public void onNotificationPosted(StatusBarNotification event){
    SharedPreferences prefs=getSharedPreferences("device",0);Notification n=event.getNotification();
    if(!ready||!prefs.getBoolean("announce",false)||!prefs.getStringSet("apps",Collections.emptySet()).contains(event.getPackageName())||(n.flags&(Notification.FLAG_ONGOING_EVENT|Notification.FLAG_GROUP_SUMMARY))!=0)return;
    if(getSystemService(KeyguardManager.class).isDeviceLocked())return;
    long now=System.currentTimeMillis();String key=event.getPackageName();if(now-recent.getOrDefault(key,0L)<4000)return;if(recent.size()>100)recent.clear();recent.put(key,now);
    String app="una aplicación";try{app=getPackageManager().getApplicationLabel(getPackageManager().getApplicationInfo(key,0)).toString();}catch(Exception ignored){}
    String spoken="Tienes una notificación de "+clean(app)+".";
    if(prefs.getBoolean("sender",false)&&Build.VERSION.SDK_INT>=28){try{Notification.Style restored=Notification.Builder.recoverBuilder(this,n).getStyle();if(restored instanceof Notification.MessagingStyle){Notification.MessagingStyle style=(Notification.MessagingStyle)restored;if(!style.getMessages().isEmpty()){Person sender=style.getMessages().get(style.getMessages().size()-1).getSenderPerson();if(sender!=null&&sender.getName()!=null)spoken="Llegó un mensaje de "+clean(sender.getName().toString())+" en "+clean(app)+".";}}}catch(RuntimeException ignored){/* Some apps provide incomplete notification metadata; announce only their name. */}}
    tts.speak(spoken,TextToSpeech.QUEUE_ADD,null,"notification");
  }
  private static String clean(String value){String s=value.replaceAll("[\\p{Cntrl}]"," ").trim();return s.substring(0,Math.min(60,s.length()));}
  @Override public void onDestroy(){if(active==this)active=null;if(tts!=null){tts.stop();tts.shutdown();}super.onDestroy();}
}
