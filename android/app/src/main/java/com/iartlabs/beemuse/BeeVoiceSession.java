package com.iartlabs.beemuse;
import android.content.*;
import android.service.voice.VoiceInteractionSession;
import android.view.View;
import android.widget.*;
public class BeeVoiceSession extends VoiceInteractionSession {
  public BeeVoiceSession(Context context){super(context);}
  @Override public View onCreateContentView(){LinearLayout view=new LinearLayout(getContext());view.setOrientation(1);view.setPadding(24,24,24,24);boolean locked=getContext().getSystemService(android.app.KeyguardManager.class).isDeviceLocked();TextView title=new TextView(getContext());title.setText(locked?"Bee-Muse · Desbloquea con Android para continuar":"Bee-Muse · ¿Qué quieres hacer?");view.addView(title);Button b=new Button(getContext());b.setText(locked?"Desbloquear con Android":"Dar una orden al teléfono");b.setOnClickListener(v->{startAssistantActivity(new Intent(getContext(),DeviceActivity.class));finish();});view.addView(b);if(!locked){Button chat=new Button(getContext());chat.setText("Conversar con Muse");chat.setOnClickListener(v->{startAssistantActivity(new Intent(getContext(),MainActivity.class));finish();});view.addView(chat);}return view;}
}
