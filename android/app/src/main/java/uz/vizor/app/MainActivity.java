package uz.vizor.app;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final String DEFAULT_URL = "https://vizor-platform.onrender.com";
    private static final String PREF_URL = "vizor_url";
    private WebView web;
    private ProgressBar progress;
    private LinearLayout settings;
    private TextView status;

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        buildUi();
        String url = getPreferences(MODE_PRIVATE).getString(PREF_URL, DEFAULT_URL);
        loadSafeUrl(url);
    }

    private void buildUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xFF0F1724);

        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.HORIZONTAL);
        top.setPadding(dp(12), dp(8), dp(12), dp(8));
        TextView title = new TextView(this);
        title.setText("VIZOR");
        title.setTextColor(0xFF6EA8FF);
        title.setTextSize(22);
        title.setGravity(android.view.Gravity.CENTER_VERTICAL);
        top.addView(title, new LinearLayout.LayoutParams(0, dp(48), 1));

        Button home = new Button(this);
        home.setText("Bosh sahifa");
        top.addView(home);
        Button reload = new Button(this);
        reload.setText("Yangilash");
        top.addView(reload);
        Button settingsButton = new Button(this);
        settingsButton.setText("Server");
        top.addView(settingsButton);
        root.addView(top);

        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(100);
        root.addView(progress, new LinearLayout.LayoutParams(-1, dp(3)));

        settings = new LinearLayout(this);
        settings.setOrientation(LinearLayout.VERTICAL);
        settings.setPadding(dp(14), dp(8), dp(14), dp(8));
        settings.setVisibility(View.GONE);
        TextView label = new TextView(this);
        label.setText("VIZOR server manzili");
        label.setTextColor(0xFFFFFFFF);
        settings.addView(label);
        android.widget.EditText input = new android.widget.EditText(this);
        input.setSingleLine(true);
        input.setTextColor(0xFFFFFFFF);
        input.setHintTextColor(0xFFB0BEC5);
        input.setHint(DEFAULT_URL);
        input.setText(getPreferences(MODE_PRIVATE).getString(PREF_URL, DEFAULT_URL));
        settings.addView(input);
        Button save = new Button(this);
        save.setText("Manzilni saqlash va ulanish");
        settings.addView(save);
        save.setOnClickListener(v -> {
            String value = input.getText().toString().trim();
            if (!isAllowed(value)) {
                Toast.makeText(this, "Faqat vizor-platform.onrender.com HTTPS serveriga ulanish mumkin.", Toast.LENGTH_LONG).show();
                return;
            }
            getPreferences(MODE_PRIVATE).edit().putString(PREF_URL, value).apply();
            settings.setVisibility(View.GONE);
            web.loadUrl(value);
        });
        root.addView(settings);

        status = new TextView(this);
        status.setTextColor(0xFFFFD180);
        status.setPadding(dp(12), dp(4), dp(12), dp(4));
        status.setVisibility(View.GONE);
        root.addView(status);

        web = new WebView(this);
        web.setBackgroundColor(0xFFFFFFFF);
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);
        web.getSettings().setAllowContentAccess(false);
        web.getSettings().setMixedContentMode(android.webkit.WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        web.getSettings().setSafeBrowsingEnabled(true);
        web.setWebChromeClient(new WebChromeClient() {
            @Override public void onProgressChanged(WebView view, int p) {
                progress.setProgress(p);
                progress.setVisibility(p >= 100 ? View.GONE : View.VISIBLE);
            }
        });
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                Uri u = req.getUrl();
                if (isInternal(u)) return false;
                openExternal(u);
                return true;
            }
            @Override public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
                status.setVisibility(View.GONE);
                progress.setVisibility(View.VISIBLE);
            }
            @Override public void onPageFinished(WebView view, String url) {
                progress.setVisibility(View.GONE);
            }
            @Override public void onReceivedError(WebView view, WebResourceRequest req, android.webkit.WebResourceError err) {
                if (req.isForMainFrame()) {
                    status.setText("Internet yoki serverga ulanishda muammo. "Yangilash" tugmasini bosing.");
                    status.setVisibility(View.VISIBLE);
                }
            }
        });
        root.addView(web, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(root);

        home.setOnClickListener(v -> web.loadUrl(DEFAULT_URL));
        reload.setOnClickListener(v -> web.reload());
        settingsButton.setOnClickListener(v -> settings.setVisibility(settings.getVisibility() == View.VISIBLE ? View.GONE : View.VISIBLE));
    }

    private boolean isAllowed(String raw) {
        try {
            Uri u = Uri.parse(raw);
            return "https".equalsIgnoreCase(u.getScheme()) && "vizor-platform.onrender.com".equalsIgnoreCase(u.getHost());
        } catch (Exception e) { return false; }
    }
    private boolean isInternal(Uri u) {
        return "https".equalsIgnoreCase(u.getScheme()) && "vizor-platform.onrender.com".equalsIgnoreCase(u.getHost());
    }
    private void loadSafeUrl(String raw) {
        if (isAllowed(raw)) web.loadUrl(raw);
        else web.loadUrl(DEFAULT_URL);
    }
    private void openExternal(Uri uri) {
        if (uri == null || !"https".equalsIgnoreCase(uri.getScheme())) return;
        try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); }
        catch (Exception e) { Toast.makeText(this, "Havola ochilmadi", Toast.LENGTH_SHORT).show(); }
    }
    private int dp(int v) { return (int)(v * getResources().getDisplayMetrics().density + 0.5f); }

    @Override public void onBackPressed() {
        if (settings.getVisibility() == View.VISIBLE) settings.setVisibility(View.GONE);
        else if (web != null && web.canGoBack()) web.goBack();
        else super.onBackPressed();
    }
}