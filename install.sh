#!/usr/bin/env bash
# ==============================================================================
# Omarchy Qutebrowser Installer
# Author: Mohammed Musharaf (m7sh)
# Repository: https://github.com/m7sh/omarchy-qutebrowser
# ==============================================================================
set -euo pipefail

BOLD="\033[1m"
GREEN="\033[38;2;166;227;161m"
BLUE="\033[38;2;137;180;250m"
YELLOW="\033[38;2;250;179;135m"
CYAN="\033[38;2;137;220;235m"
PURPLE="\033[38;2;203;166;247m"
RESET="\033[0m"

echo -e "${PURPLE}${BOLD}"
cat << 'EOF'
  ___                           _             ___        _       _                                
 / _ \ _ __ ___   __ _ _ __ ___| |__  _   _  / _ \ _   _| |_ ___| |__  _ __ _____      _____  ___ _ __ 
| | | | '_ ` _ \ / _` | '__/ __| '_ \| | | || | | | | | | __/ _ \ '_ \| '__/ _ \ \ /\ / / __|/ _ \ '__|
| |_| | | | | | | (_| | | | (__| | | | |_| || |_| | |_| | ||  __/ |_) | | | (_) \ V  V /\__ \  __/ |   
 \___/|_| |_| |_|\__,_|_|  \___|_| |_|\__, | \__\_\\__,_|\__\___|_.__/|_|  \___/ \_/\_/ |___/\___|_|   
                                       |___/                                                              
EOF
echo -e "${RESET}${CYAN}Dynamic Theming & Wayland Transparency for Omarchy Linux${RESET}\n"

# Directory paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUTE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/qutebrowser"
OMARCHY_THEMED="${XDG_CONFIG_HOME:-$HOME/.config}/omarchy/themed"
OMARCHY_HOOKS="${XDG_CONFIG_HOME:-$HOME/.config}/omarchy/hooks/theme-set.d"
HYPR_CONF="${XDG_CONFIG_HOME:-$HOME/.config}/hypr/hyprland.lua"

# 1. Ensure Qutebrowser and Brave's adblock engine are installed
if ! command -v qutebrowser >/dev/null 2>&1 || ! python3 -c 'import adblock' >/dev/null 2>&1; then
    echo -e "${YELLOW}➜ qutebrowser and/or python-adblock are not installed.${RESET}"
    INSTALLED=0
    if command -v omarchy >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
        echo -e "${BLUE}Installing qutebrowser + Brave adblock engine via Omarchy...${RESET}"
        if omarchy pkg add qutebrowser python-adblock 2>/dev/null; then
            INSTALLED=1
        fi
    elif command -v pacman >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
        echo -e "${BLUE}Installing qutebrowser + python-adblock via pacman...${RESET}"
        if sudo pacman -S --noconfirm --needed qutebrowser python-adblock 2>/dev/null; then
            INSTALLED=1
        fi
    fi

    if [[ $INSTALLED -eq 0 ]] && command -v uv >/dev/null 2>&1; then
        echo -e "${BLUE}Installing qutebrowser + python-adblock via uv (user environment)...${RESET}"
        uv tool install --with adblock --with PyQt6 --with PyQt6-WebEngine qutebrowser >/dev/null 2>&1 || true
        uv pip install --target "$HOME/.local/lib/python$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')/site-packages" adblock >/dev/null 2>&1 || true
    fi

    if ! command -v qutebrowser >/dev/null 2>&1 || ! python3 -c 'import adblock' >/dev/null 2>&1; then
        echo -e "${YELLOW}Please install qutebrowser and python-adblock first and re-run this script.${RESET}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ qutebrowser + Brave adblock engine are installed.${RESET}"

# 2. Setup ~/.config/qutebrowser and install config.py
mkdir -p "$QUTE_DIR"
if [[ -f "$QUTE_DIR/config.py" ]]; then
    BACKUP="$QUTE_DIR/config.py.bak.$(date +%s)"
    echo -e "${YELLOW}➜ Backing up existing config.py to $(basename "$BACKUP")...${RESET}"
    cp "$QUTE_DIR/config.py" "$BACKUP"
fi

echo -e "${BLUE}➜ Installing qutebrowser config.py...${RESET}"
cp "$SCRIPT_DIR/config.py" "$QUTE_DIR/config.py"
chmod 644 "$QUTE_DIR/config.py"

# Brave adblock: settings, catalog and cosmetic-filtering layer
echo -e "${BLUE}➜ Installing Brave adblock integration...${RESET}"
cp "$SCRIPT_DIR/brave_adblock.py" "$QUTE_DIR/brave_adblock.py"
cp "$SCRIPT_DIR/brave_cosmetics.py" "$QUTE_DIR/brave_cosmetics.py"
cp "$SCRIPT_DIR/brave-lists.txt" "$QUTE_DIR/brave-lists.txt"
chmod 644 "$QUTE_DIR/brave_adblock.py" "$QUTE_DIR/brave_cosmetics.py" "$QUTE_DIR/brave-lists.txt"
echo -e "${GREEN}✓ Config installed to $QUTE_DIR/config.py${RESET}"

# Clean up obsolete Greasemonkey scripts if previously installed
if [[ -f "$QUTE_DIR/greasemonkey/yt-ads.js" ]]; then
    rm -f "$QUTE_DIR/greasemonkey/yt-ads.js"
    rmdir "$QUTE_DIR/greasemonkey" 2>/dev/null || true
fi

# 3. Pre-build the adblock engine cache so blocking works on first launch
if python3 -c 'import adblock' >/dev/null 2>&1; then
    echo -e "${BLUE}➜ Building Brave adblock cache (downloads ~9 MB of filter lists)...${RESET}"
    if python3 "$SCRIPT_DIR/contrib/brave_adblock/build_cache.py" \
            --lists "$QUTE_DIR/brave-lists.txt" --refresh; then
        echo -e "${GREEN}✓ Brave adblock cache ready.${RESET}"
    else
        echo -e "${YELLOW}Note: cache build failed; run :adblock-update in qutebrowser.${RESET}"
    fi
else
    echo -e "${YELLOW}Note: python-adblock is missing; network ad blocking will be unavailable.${RESET}"
fi

# 4. Install Omarchy theme templates
if [[ -d "${XDG_CONFIG_HOME:-$HOME/.config}/omarchy" ]]; then
    mkdir -p "$OMARCHY_THEMED"
    echo -e "${BLUE}➜ Installing Omarchy theme templates...${RESET}"
    cp "$SCRIPT_DIR/contrib/omarchy/qutebrowser-theme.py.tpl" "$OMARCHY_THEMED/"
    cp "$SCRIPT_DIR/contrib/omarchy/qutebrowser-startpage.html.tpl" "$OMARCHY_THEMED/"
    echo -e "${GREEN}✓ Templates installed to $OMARCHY_THEMED/${RESET}"

    # 5. Install theme synchronization hook
    mkdir -p "$OMARCHY_HOOKS"
    echo -e "${BLUE}➜ Installing Omarchy theme-set hook...${RESET}"
    cp "$SCRIPT_DIR/contrib/omarchy/qutebrowser-theme" "$OMARCHY_HOOKS/"
    chmod +x "$OMARCHY_HOOKS/qutebrowser-theme"
    echo -e "${GREEN}✓ Hook installed to $OMARCHY_HOOKS/qutebrowser-theme${RESET}"

    # 6. Trigger theme sync for active theme
    if command -v omarchy >/dev/null 2>&1; then
        CURRENT_THEME="$(omarchy theme current 2>/dev/null || echo '')"
        if [[ -n "$CURRENT_THEME" ]]; then
            echo -e "${BLUE}➜ Syncing active Omarchy theme: ${BOLD}${CURRENT_THEME}${RESET}..."
            omarchy theme set "$CURRENT_THEME" >/dev/null 2>&1 || true
            echo -e "${GREEN}✓ Palette generated for $CURRENT_THEME${RESET}"
        fi
    fi
else
    echo -e "${YELLOW}Note: ~/.config/omarchy not detected. Standalone fallback colors will be used.${RESET}"
fi

# 7. Configure Hyprland Window Rule (Terminal 0.90 Opacity)
if [[ -f "$HYPR_CONF" ]]; then
    if ! grep -q "qutebrowser" "$HYPR_CONF"; then
        echo -e "${BLUE}➜ Adding 0.90 window opacity rule to $HYPR_CONF...${RESET}"
        cat << 'EOF' >> "$HYPR_CONF"

-- Qutebrowser window rules: match terminal 0.90 transparency
o.window("([oO]rg\\.[qQ]utebrowser\\.[qQ]utebrowser|[qQ]utebrowser)", {
  tag = "-default-opacity",
  opacity = "0.90 0.85",
})
EOF
        if command -v hyprctl >/dev/null 2>&1; then
            hyprctl reload >/dev/null 2>&1 || true
        fi
        echo -e "${GREEN}✓ Hyprland window rule added and reloaded.${RESET}"
    else
        echo -e "${GREEN}✓ Hyprland already contains qutebrowser window rules.${RESET}"
    fi
fi

# 8. Install desktop entry & launcher icon
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICONS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"
mkdir -p "$APPS_DIR" "$ICONS_DIR"
ICON_SOURCE="$(find /home/mush/.local/share/uv/tools/qutebrowser /usr/share/icons -name "qutebrowser.svg" 2>/dev/null | head -n 1 || true)"
if [[ -n "$ICON_SOURCE" && -f "$ICON_SOURCE" ]]; then
    cp "$ICON_SOURCE" "$ICONS_DIR/qutebrowser.svg"
fi
cat << 'EOF' > "$APPS_DIR/org.qutebrowser.qutebrowser.desktop"
[Desktop Entry]
Name=Qutebrowser
Comment=Keyboard-driven Vim browser with Brave-grade ad blocking
GenericName=Web Browser
Exec=qutebrowser %u
Terminal=false
Type=Application
Icon=qutebrowser
Categories=Network;WebBrowser;
MimeType=text/html;text/xml;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;x-scheme-handler/qute;
StartupWMClass=qutebrowser
EOF
chmod 644 "$APPS_DIR/org.qutebrowser.qutebrowser.desktop"
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" >/dev/null 2>&1 || true
fi
echo -e "${GREEN}✓ Desktop launcher entry installed.${RESET}"

echo -e "\n${GREEN}${BOLD}🎉 Installation Complete!${RESET}"
echo -e "Launch with: ${CYAN}qutebrowser${RESET}"
echo -e "Update adblock lists: ${CYAN}ta${RESET} (or ${CYAN}:adblock-update${RESET})"
echo -e "Vim shortcuts: ${YELLOW}o/O${RESET} (open), ${YELLOW}f/F${RESET} (hints), ${YELLOW}d/u${RESET} (close/undo tab), ${YELLOW}M${RESET} (stream in MPV), ${YELLOW}td${RESET} (toggle darkmode)\n"
