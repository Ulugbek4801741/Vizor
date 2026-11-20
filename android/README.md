# VIZOR Android app

This is a lightweight Android WebView client for the VIZOR web platform.

## Requirements
- Android Studio with JDK 17
- Android SDK 35

## Build
Open this `android/` folder in Android Studio and build the `app` configuration, or run:

```bash
gradle assembleDebug
```

The debug APK is created at:
`app/build/outputs/apk/debug/app-debug.apk`

## Connect to the backend
On first launch, enter the HTTPS Render URL for the VIZOR web service. The app remembers it on that device. The website and Android app then use the same backend and PostgreSQL database. Guest access remains available; creating an account is optional.

A signed release APK/AAB still requires a release keystore and signing configuration.
