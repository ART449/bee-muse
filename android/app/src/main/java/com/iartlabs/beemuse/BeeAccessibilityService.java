package com.iartlabs.beemuse;

import android.accessibilityservice.*;
import android.app.KeyguardManager;
import android.graphics.*;
import android.os.*;
import android.view.WindowManager;
import android.view.accessibility.*;
import java.util.*;
import java.util.function.Consumer;

public class BeeAccessibilityService extends AccessibilityService {
  static BeeAccessibilityService active;
  private String previousPackage="";
  private boolean busy;
  @Override protected void onServiceConnected(){active=this;}
  @Override public void onAccessibilityEvent(AccessibilityEvent event){
    if(event.getEventType()==AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED && event.getPackageName()!=null){String p=event.getPackageName().toString();if(p.contains("permissioncontroller"))BeeNotificationService.permissionNotice();if(!p.equals(getPackageName())&&!p.startsWith("com.google.android.googlequicksearchbox"))previousPackage=p;}
  }
  @Override public void onInterrupt(){busy=false;}
  @Override public void onDestroy(){if(active==this)active=null;super.onDestroy();}
  String target(){return previousPackage;}
  private void reply(DeviceActions action,String result,Consumer<String> callback){busy=false;ActionJournal.record(this,action.type,result);callback.accept(result);}
  private boolean sensitive(AccessibilityNodeInfo root){
    ArrayDeque<AccessibilityNodeInfo> nodes=new ArrayDeque<>();nodes.add(root);int budget=2000;
    while(!nodes.isEmpty()&&budget-->0){AccessibilityNodeInfo n=nodes.removeFirst();if(n.isPassword())return true;for(int i=0;i<n.getChildCount();i++){AccessibilityNodeInfo child=n.getChild(i);if(child!=null)nodes.addLast(child);}}
    return !nodes.isEmpty();
  }
  private boolean protectedPackage(String p){return p.equals("com.android.settings")||p.equals("com.android.systemui")||p.contains("permissioncontroller")||p.contains("packageinstaller");}
  void execute(DeviceActions action,String expected,Consumer<String> callback){
    if(busy){callback.accept("Otra acción sigue en curso.");return;}
    busy=true;
    KeyguardManager lock=getSystemService(KeyguardManager.class);
    AccessibilityNodeInfo root=getRootInActiveWindow();String actual=root==null||root.getPackageName()==null?"":root.getPackageName().toString();
    if(lock.isDeviceLocked()||actual.isEmpty()||actual.equals(getPackageName())||!actual.equals(expected)||protectedPackage(actual)||sensitive(root)){
      reply(action,"No se ejecutó: cambió la aplicación, el teléfono está bloqueado o la pantalla requiere interacción directa.",callback);return;
    }
    if(action.type.equals("back")||action.type.equals("home")){boolean accepted=performGlobalAction(action.type.equals("back")?GLOBAL_ACTION_BACK:GLOBAL_ACTION_HOME);reply(action,accepted?"Android aceptó la navegación; comprueba la pantalla.":"Android rechazó la navegación.",callback);return;}
    Rect bounds=new Rect();root.getBoundsInScreen(bounds);
    if(action.type.equals("label")){
      List<AccessibilityNodeInfo> matches=root.findAccessibilityNodeInfosByText(action.argument),exact=new ArrayList<>();
      for(AccessibilityNodeInfo n:matches){String t=n.getText()==null?"":DeviceActions.normalize(n.getText().toString()),d=n.getContentDescription()==null?"":DeviceActions.normalize(n.getContentDescription().toString());if((t.equals(action.argument)||d.equals(action.argument))&&n.isVisibleToUser()&&n.isEnabled())exact.add(n);}
      if(exact.size()!=1){reply(action,"No se ejecutó: el texto no identifica un único elemento visible.",callback);return;}
      exact.get(0).getBoundsInScreen(bounds);
    }
    android.util.DisplayMetrics dm=new android.util.DisplayMetrics();getSystemService(WindowManager.class).getDefaultDisplay().getRealMetrics(dm);
    float x=bounds.exactCenterX(),y=bounds.exactCenterY(),endX=x,endY=y;long duration=90;
    if(action.type.equals("tap")||action.type.equals("hold")||action.type.equals("drag")){x=action.points[0];y=action.points[1];endX=x;endY=y;if(action.type.equals("hold"))duration=900;if(action.type.equals("drag")){endX=action.points[2];endY=action.points[3];duration=700;}}
    if(action.type.equals("down")||action.type.equals("up")){float delta=Math.min(dm.heightPixels*.20f,bounds.height()*.25f);y=bounds.exactCenterY()+(action.type.equals("down")?delta/2:-delta/2);endY=y+(action.type.equals("down")?-delta:delta);duration=350;}
    if(x<0||y<0||endX<0||endY<0||x>=dm.widthPixels||endX>=dm.widthPixels||y>=dm.heightPixels||endY>=dm.heightPixels){reply(action,"Coordenadas fuera de la pantalla del teléfono.",callback);return;}
    Path path=new Path();path.moveTo(x,y);if(x!=endX||y!=endY)path.lineTo(endX,endY);
    GestureDescription gesture=new GestureDescription.Builder().addStroke(new GestureDescription.StrokeDescription(path,0,duration)).build();
    boolean sent=dispatchGesture(gesture,new GestureResultCallback(){
      @Override public void onCompleted(GestureDescription g){reply(action,"Android completó el gesto; comprueba el resultado en la aplicación.",callback);}
      @Override public void onCancelled(GestureDescription g){reply(action,"Android canceló el gesto.",callback);}
    },new Handler(Looper.getMainLooper()));
    if(!sent)reply(action,"Android no aceptó el gesto.",callback);
  }
}
