package com.iartlabs.beemuse;

import java.text.Normalizer;
import java.util.regex.*;

/** Explicit local commands. Unrecognized speech never becomes a gesture. */
final class DeviceActions {
  final String type, argument;
  final int[] points;
  private DeviceActions(String type,String argument,int... points){this.type=type;this.argument=argument;this.points=points;}
  static String normalize(String value){return Normalizer.normalize(value,Normalizer.Form.NFD).replaceAll("\\p{M}","").toLowerCase(java.util.Locale.ROOT).trim().replaceAll("\\s+"," ");}
  static DeviceActions parse(String value){
    String s=normalize(value);
    if(s.length()>240)throw new IllegalArgumentException("Orden demasiado larga.");
    if(s.matches("(abre|abrir) .+"))return new DeviceActions("open",s.replaceFirst("^(abre|abrir) (la aplicacion )?",""));
    if(s.matches("(baja|desplaza hacia abajo|desplaza para abajo|desplazate hacia abajo)"))return new DeviceActions("down","");
    if(s.matches("(sube|desplaza hacia arriba|desplaza para arriba|desplazate hacia arriba)"))return new DeviceActions("up","");
    if(s.matches("(atras|volver|regresa)"))return new DeviceActions("back","");
    if(s.matches("(inicio|ir al inicio|pantalla de inicio)"))return new DeviceActions("home","");
    if(s.matches("(desbloquea|desbloqueate|desbloquear)"))return new DeviceActions("unlock","");
    Matcher tap=Pattern.compile("^(pulsa|toca|aprieta|haz clic|manten pulsado) (\\d{1,5})[ ,]+(\\d{1,5})$").matcher(s);
    if(tap.matches())return new DeviceActions(tap.group(1).equals("manten pulsado")?"hold":"tap","",Integer.parseInt(tap.group(2)),Integer.parseInt(tap.group(3)));
    Matcher drag=Pattern.compile("^arrastra (\\d{1,5})[ ,]+(\\d{1,5}) (?:a|hasta) (\\d{1,5})[ ,]+(\\d{1,5})$").matcher(s);
    if(drag.matches())return new DeviceActions("drag","",Integer.parseInt(drag.group(1)),Integer.parseInt(drag.group(2)),Integer.parseInt(drag.group(3)),Integer.parseInt(drag.group(4)));
    Matcher label=Pattern.compile("^(pulsa|toca|haz clic|aprieta)(?: en)? (.+)$").matcher(s);
    if(label.matches())return new DeviceActions("label",label.group(2));
    throw new IllegalArgumentException("Usa: abre una app, baja, sube, atrás, inicio, pulsa un texto, pulsa X Y, mantén pulsado X Y o arrastra X Y a X Y.");
  }
}
