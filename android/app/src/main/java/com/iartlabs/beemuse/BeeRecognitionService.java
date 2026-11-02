package com.iartlabs.beemuse;

import android.content.*;
import android.content.pm.*;
import android.os.Bundle;
import android.os.RemoteException;
import android.provider.Settings;
import android.speech.*;
import java.util.List;

/** Delegates to the user's installed recognizer, never recursively to itself. */
public class BeeRecognitionService extends RecognitionService {
  private SpeechRecognizer recognizer;
  private interface Delivery {void send() throws RemoteException;}
  private void deliver(Delivery event){try{event.send();}catch(RemoteException e){clear();}}
  private void clear(){if(recognizer!=null){recognizer.destroy();recognizer=null;}}
  @Override protected void onStartListening(Intent intent,Callback callback){
    if(recognizer!=null){deliver(()->callback.error(SpeechRecognizer.ERROR_RECOGNIZER_BUSY));return;}
    List<ResolveInfo> providers=getPackageManager().queryIntentServices(new Intent(RecognitionService.SERVICE_INTERFACE),0);
    ComponentName preferred=ComponentName.unflattenFromString(Settings.Secure.getString(getContentResolver(),"voice_recognition_service")==null?"":Settings.Secure.getString(getContentResolver(),"voice_recognition_service")),selected=null;
    for(ResolveInfo info:providers){ServiceInfo s=info.serviceInfo;if(s==null||s.packageName.equals(getPackageName()))continue;ComponentName c=new ComponentName(s.packageName,s.name);if(c.equals(preferred)){selected=c;break;}if(selected==null&&(s.applicationInfo.flags&ApplicationInfo.FLAG_SYSTEM)!=0)selected=c;}
    if(selected==null){deliver(()->callback.error(SpeechRecognizer.ERROR_CLIENT));return;}
    try{
      recognizer=SpeechRecognizer.createSpeechRecognizer(this,selected);
      recognizer.setRecognitionListener(new RecognitionListener(){
        public void onReadyForSpeech(Bundle b){deliver(()->callback.readyForSpeech(b));}
        public void onBeginningOfSpeech(){deliver(callback::beginningOfSpeech);}
        public void onRmsChanged(float value){deliver(()->callback.rmsChanged(value));}
        public void onBufferReceived(byte[] buffer){deliver(()->callback.bufferReceived(buffer));}
        public void onEndOfSpeech(){deliver(callback::endOfSpeech);}
        public void onError(int error){deliver(()->callback.error(error));clear();}
        public void onResults(Bundle results){deliver(()->callback.results(results));clear();}
        public void onPartialResults(Bundle results){deliver(()->callback.partialResults(results));}
        public void onEvent(int type,Bundle params){}
      });recognizer.startListening(new Intent(intent));
    }catch(Exception e){clear();deliver(()->callback.error(SpeechRecognizer.ERROR_CLIENT));}
  }
  @Override protected void onStopListening(Callback callback){if(recognizer!=null)recognizer.stopListening();}
  @Override protected void onCancel(Callback callback){if(recognizer!=null)recognizer.cancel();clear();}
  @Override public void onDestroy(){clear();super.onDestroy();}
}
