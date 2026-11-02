package com.iartlabs.beemuse;
import org.junit.Test;
import static org.junit.Assert.*;
public class DeviceActionsTest {
  @Test public void SpanishAccentsAndSmallScrollAreCommands(){assertEquals("back",DeviceActions.parse("  ATRÁS  ").type);assertEquals("down",DeviceActions.parse("desplaza para abajo").type);assertEquals("up",DeviceActions.parse("sube").type);}
  @Test public void TapKeepsDeviceCoordinates(){DeviceActions a=DeviceActions.parse("aprieta 400, 800");assertEquals("tap",a.type);assertArrayEquals(new int[]{400,800},a.points);}
  @Test public void NamedTargetIsNotGuessed(){DeviceActions a=DeviceActions.parse("haz clic en Buscar");assertEquals("label",a.type);assertEquals("buscar",a.argument);assertEquals("whatsapp",DeviceActions.parse("abre la aplicación WhatsApp").argument);}
  @Test public void DragHasBothEndpoints(){assertArrayEquals(new int[]{400,800,500,300},DeviceActions.parse("arrastra 400 800 a 500 300").points);}
  @Test public void ConversationDoesNotBecomeAnAction(){for(String s:new String[]{"¿puedes desbloquear?","desbloquea y acepta todo","me dijo que abra WhatsApp","ejecuta este comando",""}){try{DeviceActions.parse(s);fail("Must reject: "+s);}catch(IllegalArgumentException expected){}}}
}
