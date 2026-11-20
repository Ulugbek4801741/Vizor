package uz.vizor.app;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final String PREFS = "vizor_settings";
    private static final String URL_KEY = "server_url";
    private WebView webView;
    private EditText urlInput;
    private LinearLayout setupPanel;
    private ProgressBar progress;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        showApp();
        String saved = getPreferences(MODE_PRIVATE).getString(URL_KEY, "https://vizor-platform.onrender.com");
        if (!saved.isEmpty()) openServer(saved);
    }

    private void showApp() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF121824);

        TextView brand = new TextView(this);
        brand.setText("VIZOR");
        brand.setTextSize(25);
        brand.setTextColor(0xFF4D8DFF);
        brand.setPadding(20, 18, 20, 10);
        root.addView(brand);

        setupPanel = new LinearLayout(this);
        setupPanel.setPadding(20, 12, 20, 12);
        setupPanel.setOrientation(LinearLayout.VERTICAL);
        TextView hint = new TextView(this);
        hint.setText("VIZOR server manzilini kiriting. Server ishga tushgach, Render bergan HTTPS manzilini shu yerga yozing.");
        hint.setTextColor(0xFFFFFFFF);
        setupPanel.addView(hint);

        urlInput = new EditText(this);
        urlInput.setSingleLine(true);
        urlInput.setHint("https://sizning-vizor-server.onrender.com");
        urlInput.setTextColor(0xFFFFFFFF);
        urlInput.setHintTextColor(0xFF9AABC3);
        setupPanel.addView(urlInput);

        Button connect = new Button(this);
        connect.setText("VIZOR serveriga ulanish");
        setupPanel.addView(connect);
        connect.setOnClickListener(v -> {
            String url = urlInput.getText().toString().trim();
            if (!url.startsWith("https://")) {
                Toast.makeText(this, "Xavfsizlik uchun HTTPS manzil kiriting.", Toast.LENGTH_LONG).show();
                return;
            }
            getPreferences(MODE_PRIVATE).edit().putString(URL_KEY, url).apply();
            openServer(url);
        });
        root.addView(setupPanel);

        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(100);
        root.addView(progress);

        webView = new WebView(this);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.getSettings().setDomStorageEnabled(true);
        webView.getSettings().setAllowFileAccess(false);
        webView.getSettings().setAllowContentAccess(false);
        webView.getSettings().setMixedContentMode(android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        webView.setWebChromeClient(new WebChromeClient() {
            @Override public void onProgressChanged(WebView view, int newProgress) {
                progress.setProgress(newProgress);
                progress.setVisibility(newProgress >= 100 ? View.GONE : View.VISIBLE);
            }
        });
        webView.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if ("https".equals(uri.getScheme())) return false;
                startActivity(new Intent(Intent.ACTION_VIEW, uri));
                return true;
            }
            @Override public void onPageStarted(WebView view, String url, Bitmap favicon) {
                progress.setVisibility(View.VISIBLE);
            }
        });
        root.addView(webView, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(root);
    }

    private void openServer(String rawUrl) {
        String url = rawUrl.trim();
        if (!url.startsWith("https://")) return;
        setupPanel.setVisibility(View.GONE);
        webView.setVisibility(View.VISIBLE);
        webView.loadUrl(url);
    }

    @Override public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }
}
