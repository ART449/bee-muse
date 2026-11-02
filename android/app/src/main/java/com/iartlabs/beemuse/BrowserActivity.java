package com.iartlabs.beemuse;
import android.app.Activity;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.*;
import android.widget.*;

/** Web content has no bridge to files, terminal, device commands or identity tokens. */
public class BrowserActivity extends Activity {
  private WebView web;
  private EditText address;
  private TextView status;
  private boolean safe(String value){try{Uri uri=Uri.parse(value);return value.length()<8192&&"https".equals(uri.getScheme())&&uri.getHost()!=null&&uri.getUserInfo()==null;}catch(Exception e){return false;}}
  @Override public void onCreate(Bundle state){super.onCreate(state);LinearLayout root=new LinearLayout(this);root.setOrientation(1);setContentView(root);address=new EditText(this);address.setSingleLine(true);address.setHint("Dirección HTTPS");root.addView(address);LinearLayout bar=new LinearLayout(this);root.addView(bar);Button go=new Button(this);go.setText("Ir");bar.addView(go);go.setOnClickListener(v->{String value=address.getText().toString().trim();if(!value.contains("://"))value="https://"+value;if(safe(value))web.loadUrl(value);else status.setText("Usa una dirección HTTPS sin credenciales.");});Button back=new Button(this);back.setText("Atrás");bar.addView(back);back.setOnClickListener(v->{if(web.canGoBack())web.goBack();});Button next=new Button(this);next.setText("Adelante");bar.addView(next);next.setOnClickListener(v->{if(web.canGoForward())web.goForward();});Button reload=new Button(this);reload.setText("Recargar");bar.addView(reload);reload.setOnClickListener(v->web.reload());status=new TextView(this);status.setText("Navegador Bee-Muse · HTTPS");root.addView(status);
    web=new WebView(this);root.addView(web,new LinearLayout.LayoutParams(-1,0,1));WebSettings settings=web.getSettings();settings.setJavaScriptEnabled(true);settings.setDomStorageEnabled(true);settings.setAllowFileAccess(false);settings.setAllowContentAccess(false);settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);settings.setJavaScriptCanOpenWindowsAutomatically(false);WebView.setWebContentsDebuggingEnabled(false);
    web.setWebViewClient(new WebViewClient(){@Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest request){if(!safe(request.getUrl().toString())){status.setText("Esta dirección no se abre en Bee-Muse.");return true;}return false;}@Override public void onPageFinished(WebView view,String url){address.setText(url);status.setText(view.getTitle());}});
    web.setWebChromeClient(new WebChromeClient(){@Override public void onPermissionRequest(PermissionRequest request){request.deny();}});
    if(state!=null)web.restoreState(state);
  }
  @Override protected void onSaveInstanceState(Bundle state){web.saveState(state);super.onSaveInstanceState(state);}
  @Override protected void onDestroy(){web.stopLoading();web.destroy();super.onDestroy();}
}
