package com.iartlabs.beemuse;
import android.os.Bundle;
import android.service.voice.*;
public class BeeVoiceSessionService extends VoiceInteractionSessionService {
  @Override public VoiceInteractionSession onNewSession(Bundle args){return new BeeVoiceSession(this);}
}
