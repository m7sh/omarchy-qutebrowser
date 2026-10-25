# 🌐 Omarchy Qutebrowser

> **A keyboard-first Qutebrowser setup for Omarchy Linux: live theme sync, Brave-grade ad blocking, native dark themes, and zero extension glue.**

<p align="center">
  <img src="./preview.png" alt="Omarchy Qutebrowser Preview" width="100%">
</p>

<p align="center">
  <a href="https://github.com/m7sh/omarchy-qutebrowser/releases"><img src="https://img.shields.io/github/v/release/m7sh/omarchy-qutebrowser?style=flat-square&color=8b5cf6" alt="Release"></a>
  <img src="https://img.shields.io/badge/qutebrowser-3.7%2B-8b5cf6?style=flat-square&logo=qutebrowser&logoColor=white" alt="qutebrowser">
  <img src="https://img.shields.io/badge/adblock-Brave%20adblock--rust-ff385c?style=flat-square&logo=brave&logoColor=white" alt="Brave Adblock">
  <img src="https://img.shields.io/badge/Omarchy-Arch%20Linux-38bdf8?style=flat-square&logo=arch-linux&logoColor=white" alt="Omarchy">
  <img src="https://img.shields.io/badge/License-MIT-f59e0b?style=flat-square" alt="MIT License">
</p>

---

## ✨ What you get

- 🛡️ **Brave's actual ad blocker** — the same `adblock-rust` engine and filter catalog Brave ships, including cosmetic element hiding. No uBlock clone, no wrapper extension.
- 🎬 **YouTube without ads** — network blocking plus cosmetic hiding plus an in-stream skip engine that mutes, fast-forwards and seeks past video ads.
- 🌙 **Native dark themes first** — sites receive `prefers-color-scheme` from the active Omarchy theme, so switches, checkboxes and form controls keep their intended styling. A forced-dark fallback is one keypress away.
- 🎨 **Live Omarchy theme sync** — switch themes with `omarchy theme set` and every Qutebrowser colour updates over IPC. Tabs stay open.
- ⚡ **Local terminal startpage** — an instant new-tab dashboard with clock, date, DuckDuckGo search, bookmark tiles and a Vim cheat sheet. No network round-trip.
- ⌨️ **Vim controls** — single-key navigation, link hints, tab history, and one-key `mpv` streaming for videos.
- 📦 **pacman only** — `qutebrowser` and `python-adblock` come from the Arch repos. No `uv` tool environment, no duplicate user-site packages.

**Tested on:** Omarchy / Arch Linux, Qutebrowser 3.7.0, QtWebEngine 6.12.0, `python-adblock` 0.6.0.

---

## 📦 Requirements

| Dependency | Why |
| :--- | :--- |
| **Arch Linux / Omarchy** | The installer uses `pacman`; the theming hook targets Omarchy |
| **qutebrowser ≥ 3.7** | Adblock backend, dark-mode runtime switching, QtWebEngine integration |
| **python-adblock ≥ 0.6** | Brave's `adblock-rust` engine (qutebrowser's network blocker) |
| **QtWebEngine ≥ 6.7** | Required for toggling dark mode without restarting |
| **mpv** *(optional)* | Only for the <kbd>M</kbd> / <kbd>,</kbd><kbd>m</kbd> video-streaming bindings |

---

## 🚀 Install

One line:

```bash
git clone https://github.com/m7sh/omarchy-qutebrowser.git /tmp/omarchy-qutebrowser && /tmp/omarchy-qutebrowser/install.sh && rm -rf /tmp/omarchy-qutebrowser
```

Or clone and run it yourself:

```bash
git clone https://github.com/m7sh/omarchy-qutebrowser.git
cd omarchy-qutebrowser
./install.sh
```

### What the installer does

1. Installs `qutebrowser` and `python-adblock` from the Arch repos with `pacman`.
2. Backs up an existing `~/.config/qutebrowser/config.py`, then deploys `config.py`, `brave_adblock.py`, `brave_cosmetics.py` and `brave-lists.txt`.
3. Pre-builds the 27-list Brave adblock cache (≈ 14 MB) so blocking works on the very first launch.
4. Installs the Omarchy theme template and startpage template.
5. Installs the `theme-set.d` hook that regenerates colours and reloads Qutebrowser on theme changes.
6. Generates the palette for your current theme immediately.
7. Registers the desktop launcher entry and icon.

Existing configs are never silently replaced: the old `config.py` is copied to `config.py.bak.<timestamp>`.

---

## 🛡️ Brave-grade ad blocking

Qutebrowser's native blocker already uses **Brave's `adblock-rust` engine** through the `adblock` Python package. This project plugs Brave's real filter catalog into it and restores the piece qutebrowser leaves out: **cosmetic filtering**.

| Layer | What it adds |
| :--- | :--- |
| **Brave Default** | uBlock Origin filters (+ yearly lists), EasyList, URLhaus, Brave Specific / Social / SugarCoat |
| **Brave Privacy** | EasyPrivacy + uBO Privacy |
| **Brave First Party** | `brave-firstparty.txt` + regional first-party rules |
| **Cookie Notices** | Fanboy Cookie + uBO Cookie + Brave cookie rules |
| **Hosts layer** | StevenBlack hosts as a second net for trackers missing from ABP lists |
| **Cosmetic layer** | `brave_cosmetics.py` asks the same engine for `hide_selectors`, `style_selectors` and generic `.class`/`#id` rules, then injects them as a `<style>` element |

The catalog in [`brave-lists.txt`](./brave-lists.txt) mirrors the default-enabled entries of Brave's [`list_catalog.json`](https://github.com/brave/adblock-resources/blob/master/filter_lists/list_catalog.json).

### Verified in practice

A fresh-profile run against ten ad-heavy sites (above-the-fold screenshots) recorded **256 blocked requests** and **no visible ad creatives**:

| Site | Blocked | Cosmetic rules | Visible ads |
| :--- | ---: | ---: | :--- |
| Forbes | 23 | 26 hide | none |
| CNN | 34 | 22 hide + 2 style | none |
| Daily Mail | 28 | 12 hide | none |
| Weather.com | 38 | 11 hide | anti-adblock wall |
| ESPN | 16 | 2 hide | none |
| 9GAG | 49 | 10 hide + 1 style | none |
| IMDb | 16 | 5 hide | none |
| wikiHow | 5 | 3 hide | none |
| Fandom | 30 | 16 hide + 1 style | none |
| BuzzFeed | 15 | 6 hide | none |

A control run with blocking disabled showed Daily Mail's floating video ad and `ADVERTISEMENT` leaderboard, and Weather.com's wall disappeared — so the clean results are real blocking, not ad-free pages.

### Updating lists

- Press <kbd>t</kbd><kbd>a</kbd>, or run `:adblock-update`.
- Edit `~/.config/qutebrowser/brave-lists.txt` to add or comment out lists, then run `:adblock-update`.

### Honest limitations

Qutebrowser does not expose every Brave hook:

- `$redirect` resources and uBO scriptlets are parsed but not injected.
- `$csp` directives are not applied to responses.
- `$removeparam` URL rewriting is not performed.
- Procedural cosmetic filters (`:has-text`, `:xpath`) are ignored.
- An adblock-rust `$generichide` bug affects generic complex selectors; plain `.class` / `#id` hiding is unaffected.
- Some sites detect the blocker and show an anti-adblock wall (Weather.com is one). Most offer a "continue without disabling" link.

---

## 🎬 YouTube

YouTube serves in-stream ads over `googlevideo.com` media chunks rather than as skippable page elements, so the setup combines three layers:

- **Network blocking** — ad/tracking endpoints are blocked by the Brave lists.
- **Cosmetic hiding** — ad slots, mastheads, promoted tiles and companion banners are hidden with CSS.
- **Skip engine** — injected JavaScript mutes ad audio, speeds playback to 16×, and seeks past the ad, then restores volume and speed.

In testing, a watch page loaded with **19 blocked requests and no pre-roll ad**.

---

## 🌙 Dark mode

The default is **native dark-first**:

```python
c.colors.webpage.preferred_color_scheme = "dark"   # follows the Omarchy theme mode
c.colors.webpage.darkmode.enabled = False
```

Sites that ship a dark theme render it themselves — correct toggles, checkboxes and controls. Chromium's forced inversion is a per-element colour flip and can leave controls half-inverted (a white knob turning black while its track stays light), which is exactly the "toggle went fully dark" artifact.

The Omarchy templates keep `preferred_color_scheme` in sync with the active theme mode, so a light theme asks sites for light pages.

**Light-only site?** Press <kbd>t</kbd><kbd>d</kbd> to toggle the CIELAB forced-inversion fallback for the current session. On QtWebEngine ≥ 6.7 it applies immediately; no restart needed.

---

## ⌨️ Keybindings

| Key | Action | Description |
| :--- | :--- | :--- |
| <kbd>o</kbd> | `:open` | Open URL or search in the current tab |
| <kbd>O</kbd> | `:open -t` | Open URL or search in a new tab |
| <kbd>f</kbd> / <kbd>F</kbd> | `:hint` | Show link hints (current tab / background tab) |
| <kbd>d</kbd> | `:tab-close` | Close the active tab |
| <kbd>u</kbd> | `:undo` | Restore the last closed tab |
| <kbd>J</kbd> / <kbd>K</kbd> | `:tab-prev` / `:tab-next` | Previous / next tab |
| <kbd>M</kbd> | `:hint links spawn mpv` | Stream a hinted video link in `mpv` |
| <kbd>,</kbd><kbd>m</kbd> | `:spawn mpv {url}` | Stream the current page's video in `mpv` |
| <kbd>;</kbd><kbd>m</kbd> | `:hint --rapid links` | Rapid multi-video streaming in `mpv` |
| <kbd>t</kbd><kbd>d</kbd> | `darkmode toggle` | Toggle the forced-dark fallback |
| <kbd>t</kbd><kbd>t</kbd> | `tabs toggle` | Toggle the tab bar |
| <kbd>t</kbd><kbd>s</kbd> | `statusbar toggle` | Toggle the status bar |
| <kbd>t</kbd><kbd>r</kbd> | `:config-source` | Reload config and the active Omarchy theme |
| <kbd>t</kbd><kbd>a</kbd> | `:adblock-update` | Redownload Brave lists and rebuild the engine |
| <kbd>Esc</kbd> | `clear-keychain ;; search ;; fullscreen --leave` | Clear selection, search and fullscreen |

---

## 🔍 Search engines

Use a prefix with `:open` (or directly in the prompt):

| Prefix | Engine |
| :--- | :--- |
| `g` | Google |
| `gh` | GitHub |
| `aw` | ArchWiki |
| `yt` | YouTube |
| `r` | Subreddit (`:open r unixporn`) |
| `w` | Wikipedia |
| `om` | Omarchy |
| *(none)* | DuckDuckGo |

---

## 🎨 Omarchy theme synchronization

The hook at `~/.config/omarchy/hooks/theme-set.d/qutebrowser-theme` runs whenever you change themes. It copies the rendered `theme.py` and `startpage.html` into `~/.config/qutebrowser/` and reloads a running instance with `:config-source` — colours change, tabs stay open.

Templates live in `~/.config/omarchy/themed/`:

- `qutebrowser-theme.py.tpl` — UI palette, webpage background, dark-mode policy.
- `qutebrowser-startpage.html.tpl` — the local startpage.

If Omarchy is not detected, `config.py` falls back to Catppuccin-ish colours and DuckDuckGo.

---

## 📁 Repository layout

```
omarchy-qutebrowser/
├── config.py                     # Qutebrowser settings and keybindings
├── brave_adblock.py              # Brave catalog, hosts layer, adblock keybinds
├── brave_cosmetics.py            # Cosmetic filtering + YouTube skip engine
├── brave-lists.txt               # 27-list Brave filter catalog
├── install.sh                    # pacman installer and deployer
├── contrib/
│   ├── brave_adblock/
│   │   └── build_cache.py        # Pre-builds adblock-cache.dat
│   └── omarchy/
│       ├── qutebrowser-theme.py.tpl
│       ├── qutebrowser-startpage.html.tpl
│       └── qutebrowser-theme      # theme-set.d hook
├── hyprland/                     # Hyprland snippet
├── preview.png
└── LICENSE
```

---

## 🧰 Troubleshooting

**Ads are still visible.**
Run `:adblock-update`, then reload the page. Check that `python3 -c 'import adblock'` succeeds and resolves to the pacman package (`/usr/lib/python3*/site-packages/adblock`), not a stale user install.

**`:adblock-update` fails or the cache is empty.**
Re-run the installer, or run `python3 contrib/brave_adblock/build_cache.py --refresh` manually.

**A site shows "disable your adblocker".**
That is the blocker working; use the site's "continue without disabling" link. For a permanent exception, add the domain to `content.blocking.whitelist` in `config.py`.

**Toggle switches look fully dark.**
Forced inversion is off by default for this reason. If you enabled it with <kbd>t</kbd><kbd>d</kbd>, press it again to return to the site's own theme.

**Dark mode changes need a restart.**
Only on QtWebEngine < 6.7. On 6.12, `td` applies live.

**MPV bindings do nothing.**
Install `mpv`; the bindings spawn it on Wayland.

**A harmless portal warning at startup.**
`Failed to register with host portal` can appear when another Qt app already owns the desktop portal app ID. It does not affect browsing.

---

## 🧹 Uninstall

```bash
rm -f ~/.config/qutebrowser/{config.py,brave_adblock.py,brave_cosmetics.py,brave-lists.txt,theme.py,startpage.html}
rm -f ~/.config/omarchy/hooks/theme-set.d/qutebrowser-theme
rm -f ~/.config/omarchy/themed/qutebrowser-{theme.py,startpage.html}.tpl
rm -f ~/.local/share/applications/org.qutebrowser.qutebrowser.desktop
```

Remove `python-adblock` with `sudo pacman -Rns python-adblock` only if nothing else uses it.

---

## 👤 Author

**Mohammed Musharaf (m7sh)**

- GitHub: [@m7sh](https://github.com/m7sh)
- Portfolio: [m7sh.github.io/m7sh](https://m7sh.github.io/m7sh/)

## 📄 License

[MIT License](LICENSE) © 2026 Mohammed Musharaf
