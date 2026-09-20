# FIRE Music Dance — Local Android App

Local Android wrapper for the exact live FIRE + Music + Dance interface.

- No INTERNET permission.
- HTML/CSS/JS are bundled under `app/src/main/assets/`.
- State stays in the WebView's local storage unless the user explicitly exports it.
- Native bridge adds clipboard, JSON save, JSON file picking, share, and haptic pulses.
- `GENERATE != VERIFY != ADMIT` and all existing live-interface claim boundaries remain in the bundled runtime.

## Build

Requires Java 17, Android SDK 35, and Gradle 8.10.2+.

```sh
gradle :app:assembleDebug
```

APK:

```text
app/build/outputs/apk/debug/app-debug.apk
```

## Install locally

Copy the APK to the Android phone and open it to install after allowing installs from that file/browser source.

This is a local research-control interface, not a domain-evidence authority.
