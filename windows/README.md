# VIZOR Windows app

This desktop shell opens the live VIZOR platform in a secure Electron window.

## Build locally
1. Install Node.js 20 or newer.
2. Open PowerShell in this folder.
3. Run:
   ```powershell
   npm install
   npm run build:win
   ```
4. Installer will be in `dist/`.

The Windows installer is built automatically by GitHub Actions when Windows app files change. Download the `vizor-windows-installer` artifact from the workflow run.

Site URL: https://vizor-platform.onrender.com
