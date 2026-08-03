<div align="center">

# 🎬 Napotom

**A simple, beautiful desktop video downloader for YouTube, VK, and 1000+ sites.**

*Napotom is Russian for "for later" — because that's where all those videos go.*

**English** · [Русский](README.ru.md)

[![Latest Release](https://img.shields.io/github/v/release/egsok/napotom?style=for-the-badge)](../../releases/latest)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS-blue?style=for-the-badge)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

![Napotom](screenshots/main-window.png)

</div>

---

Napotom (formerly video-downloader2) is a small desktop app for grabbing video and audio from YouTube, VK, and 1000+ other sites. It's a friendly front-end for [yt-dlp](https://github.com/yt-dlp/yt-dlp) with `ffmpeg` and `Node.js` bundled in (on Windows), so there's nothing else to install — paste a link and download.

## ✨ Features

- 🎥 **Download from YouTube, VK, and 1000+ sites** — powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- 📺 **Quality selection** — Best, 1080p, 720p, or Audio only (MP3)
- 📋 **Download queue** with parallel downloads
- 🔔 **Completion notifications** with sound
- 🔄 **yt-dlp auto-update** from Settings — stable channel or nightly builds, which carry site fixes weeks ahead of releases
- 🌐 **Bilingual interface** — English & Russian
- 🎨 **Two-ink print design** — magenta + violet inks on an ink-wall and kraft paper, the [«Нейросеть не виновата»](https://t.me/+GpZ_G6I4yl1jZDcy) brand look
- 📦 **Bundled ffmpeg and Node.js** (Windows) — no extra installs needed
- 🍪 **Cookie import** for age-restricted and members-only videos

## 📥 Download

Grab the latest build from the **[Releases page](../../releases/latest)**.

- **Windows** — download `Napotom-Windows.zip`, extract it, and run `Napotom.exe`. On first launch Windows SmartScreen may show *"Windows protected your PC"* — click **More info → Run anyway**. The build is unsigned (see [Build from source](#-build-from-source) if you'd rather compile it yourself).
- **macOS** — download `Napotom-macOS.dmg`, open it, and drag **Napotom.app** to Applications. On first launch macOS may say the app *"is damaged and can't be opened"* — it isn't damaged, it's just unsigned and quarantined. Remove the quarantine flag in Terminal:

  ```bash
  xattr -d com.apple.quarantine /Applications/Napotom.app
  ```

  (If that errors with permission, try `sudo xattr -cr /Applications/Napotom.app`.) After this it launches normally.

## 🍪 Cookies — you'll probably need them for YouTube

You can try downloading without cookies — for plenty of videos it just works. But sooner rather than later YouTube will hand you a video that refuses to download ("Sign in to confirm you're not a bot", age-restricted, members-only). That's YouTube's anti-bot protection, **not a bug in the app**. The fix is to load your YouTube cookies once, and downloads work again.

> ⚠️ **Important:** YouTube rotates cookies on open tabs. Export them from a **private/incognito window** so the file stays valid.

**How to export cookies (Chrome, Edge, Firefox):**

1. Install the **[Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)** browser extension. *(Firefox: [get it from Firefox Add-ons](https://addons.mozilla.org/en-US/firefox/addon/get-cookies-txt-locally/).)*
2. Open a **private/incognito window** and log into YouTube.
3. In the **same tab**, go to `https://www.youtube.com/robots.txt`.
4. Click the extension icon → **export cookies** → save as `cookies.txt`.
5. **Close the private window** (so the cookies don't rotate).
6. In Napotom, open **Settings → Cookies → Browse…** and select the saved file.

![Settings — Cookies](screenshots/settings-cookies.png)

The extension is open-source and never sends your data anywhere: [github.com/kairi003/Get-cookies.txt-LOCALLY](https://github.com/kairi003/Get-cookies.txt-LOCALLY).

> 🔒 Your `cookies.txt` is a live key to your account — don't share it, and delete it when you're done. If you download a lot, consider using a throwaway Google account.

## 🎬 Vimeo currently needs a yt-dlp nightly build

Vimeo revoked the anonymous API credentials yt-dlp ships with, so every stable yt-dlp release fails with `HTTP Error 401` ([yt-dlp#17271](https://github.com/yt-dlp/yt-dlp/issues/17271)). The fix is already in the nightly builds.

Open **Settings → yt-dlp**, tick **Nightly**, press **Check Now**, and restart the app. Once a stable yt-dlp release ships the fix, you can untick it — the app will offer to move you back to the stable channel.

## 🔨 Build from source

#### Windows

```bash
pip install -r requirements.txt
pyinstaller build.spec --noconfirm
```

#### macOS

```bash
pip install -r requirements.txt
iconutil -c icns assets/icon.iconset -o assets/icon.icns
pyinstaller build_mac.spec --noconfirm
```

> For the exact release builds (with `ffmpeg`, `ffprobe`, and `node` bundled in), see [`.github/workflows/release.yml`](.github/workflows/release.yml).

## 🤝 Credits

Made by AI 🤖 · checked by human.

Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) and [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## 👤 Author

Built by [Egor Sokolov](https://egorsokolov.ru/) — 10 years in product (Sberbank, Rolf, Claustrophobia). Writing and experimenting with AI tooling — mostly Claude Code, Codex, and dev workflow tooling.

📣 My Telegram, where I geek out about AI tooling:

[![Telegram](https://img.shields.io/badge/Telegram-%40neiroset__ne__vinovata-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/+SzDNKr86V2tkYzM6)

Other open-source experiments:

- [klava-nevinovata](https://github.com/egsok/klava-nevinovata) — personal Russian-optimized fork of Handy, an offline speech-to-text app.
- [plan-tango](https://github.com/egsok/plan-tango) — a Claude ↔ Codex plan-review loop for Claude Code.
- [press-1](https://github.com/egsok/press-1) — answer Claude Code's permission prompts with a single keypress, from any window.

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Egor Sokolov.
