# VIZOR Android app build

Android WebView client for VIZOR.

## Build APK
1. Install Android Studio.
2. Open this repository's `android/` folder.
3. Wait for Gradle sync.
4. Build > Build APK(s).
5. APK output: `android/app/build/outputs/apk/debug/app-debug.apk`.

The existing GitHub Actions workflow `.github/workflows/android-apk.yml` builds a debug APK and uploads it as `vizor-android-debug`.

Web service: https://vizor-platform.onrender.com
