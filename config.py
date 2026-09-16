# ==============================================================================
# Qutebrowser Configuration - Omarchy Wayland Rice
# User: Mohammed Musharaf (m7sh)
# Optimized for Hyprland, Wayland, and Dynamic Omarchy Theming
# ==============================================================================
import os

# Do not load GUI autoconfig; manage settings purely in python
config.load_autoconfig(False)

# ------------------------------------------------------------------------------
# Window & Compositor Integration
# ------------------------------------------------------------------------------
# Enable transparency so tab bar, statusbar, and background can be translucent
c.window.transparent = True
c.window.title_format = "{perc}{current_title}{title_sep}qutebrowser"

# ------------------------------------------------------------------------------
# Typography
# ------------------------------------------------------------------------------
c.fonts.default_family = ["JetBrains Mono", "DejaVu Sans Mono", "monospace"]
c.fonts.default_size = "10pt"

c.fonts.tabs.selected = "bold 10pt default_family"
c.fonts.tabs.unselected = "10pt default_family"
c.fonts.statusbar = "10pt default_family"
c.fonts.downloads = "9pt default_family"
c.fonts.hints = "bold 10pt default_family"
c.fonts.keyhint = "9pt default_family"
c.fonts.messages.error = "10pt default_family"
c.fonts.messages.warning = "10pt default_family"
c.fonts.messages.info = "10pt default_family"
c.fonts.prompts = "10pt default_family"
c.fonts.completion.entry = "10pt default_family"
c.fonts.completion.category = "bold 10pt default_family"

# ------------------------------------------------------------------------------
# Tab Bar Configuration
# ------------------------------------------------------------------------------
c.tabs.position = "top"
c.tabs.show = "always"
c.tabs.title.format = "{index}: {audio}{current_title}"
c.tabs.title.format_pinned = "{index}"
c.tabs.favicons.show = "always"
c.tabs.padding = {"top": 6, "bottom": 6, "left": 10, "right": 10}
c.tabs.indicator.width = 2
c.tabs.select_on_remove = "prev"
c.tabs.mousewheel_switching = True

# ------------------------------------------------------------------------------
# Statusbar Configuration
# ------------------------------------------------------------------------------
c.statusbar.show = "always"
c.statusbar.position = "bottom"
c.statusbar.padding = {"top": 5, "bottom": 5, "left": 8, "right": 8}
c.statusbar.widgets = ["keypress", "search_match", "url", "scroll", "history", "tabs", "progress"]

# ------------------------------------------------------------------------------
# Navigation & Search Engines
# ------------------------------------------------------------------------------
startpage_path = os.path.expanduser("~/.config/qutebrowser/startpage.html")
if os.path.exists(startpage_path):
    c.url.default_page = f"file://{startpage_path}"
    c.url.start_pages = [f"file://{startpage_path}"]
else:
    c.url.default_page = "https://duckduckgo.com"
    c.url.start_pages = ["https://duckduckgo.com"]

c.url.searchengines = {
    "DEFAULT": "https://duckduckgo.com/?q={}",
    "g": "https://www.google.com/search?q={}",
    "gh": "https://github.com/search?q={}",
    "aw": "https://wiki.archlinux.org/?search={}",
    "yt": "https://www.youtube.com/results?search_query={}",
    "r": "https://www.reddit.com/r/{}",
    "w": "https://en.wikipedia.org/wiki/Special:Search?search={}",
    "om": "https://omarchy.org/?q={}",
}

# ------------------------------------------------------------------------------
# Smooth Scrolling & Dark Mode Engine
# ------------------------------------------------------------------------------
c.scrolling.smooth = True
c.colors.webpage.darkmode.algorithm = "lightness-cielab"
c.colors.webpage.darkmode.policy.images = "never"
c.colors.webpage.darkmode.enabled = True

# Content & Downloads
c.content.blocking.method = "auto"
c.content.notifications.enabled = True
c.downloads.location.prompt = False
c.downloads.position = "bottom"

# ------------------------------------------------------------------------------
# Keybindings (Vim-style & Omarchy desktop power keys)
# ------------------------------------------------------------------------------
# Dark mode toggle
config.bind("td", "config-cycle colors.webpage.darkmode.enabled")

# Tabs and statusbar toggles
config.bind("tt", "config-cycle tabs.show always switching")
config.bind("ts", "config-cycle statusbar.show always in-mode")

# Reload config & Omarchy theme
config.bind("tr", "config-source")

# Stream video in MPV (Direct Wayland player integration)
config.bind("M", "hint links spawn mpv {hint-url}")
config.bind(";m", "hint --rapid links spawn mpv {hint-url}")
config.bind(",m", "spawn mpv {url}")

# Quick escape to clear selection and cancel modes
config.bind("<Escape>", "clear-keychain ;; search ;; fullscreen --leave")

# ------------------------------------------------------------------------------
# Dynamic Omarchy Theme Sourcing
# ------------------------------------------------------------------------------
theme_file = os.path.expanduser("~/.config/qutebrowser/theme.py")
if os.path.exists(theme_file):
    config.source("theme.py")
else:
    # Graceful fallback if theme.py is not yet generated
    c.colors.statusbar.normal.bg = "#1e1e2e"
    c.colors.statusbar.normal.fg = "#cdd6f4"
    c.colors.tabs.bar.bg = "#11111b"
    c.colors.tabs.selected.even.bg = "#1e1e2e"
    c.colors.tabs.selected.even.fg = "#cba6f7"
    c.colors.tabs.even.bg = "#181825"
    c.colors.tabs.even.fg = "#6c7086"
