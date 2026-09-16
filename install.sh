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

# 1. Ensure Qutebrowser is installed
if ! command -v qutebrowser >/dev/null 2>&1; then
    echo -e "${YELLOW}➜ qutebrowser is not installed.${RESET}"
    if command -v omarchy >/dev/null 2>&1; then
        echo -e "${BLUE}Installing qutebrowser via Omarchy...${RESET}"
        omarchy pkg add qutebrowser
    elif command -v pacman >/dev/null 2>&1; then
        echo -e "${BLUE}Installing qutebrowser via pacman...${RESET}"
        sudo pacman -S --noconfirm qutebrowser
    else
        echo -e "${YELLOW}Please install qutebrowser first and re-run this script.${RESET}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ qutebrowser is installed.${RESET}"

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
echo -e "${GREEN}✓ Config installed to $QUTE_DIR/config.py${RESET}"

# 3. Install Omarchy theme templates
if [[ -d "${XDG_CONFIG_HOME:-$HOME/.config}/omarchy" ]]; then
    mkdir -p "$OMARCHY_THEMED"
    echo -e "${BLUE}➜ Installing Omarchy theme templates...${RESET}"
    cp "$SCRIPT_DIR/contrib/omarchy/qutebrowser-theme.py.tpl" "$OMARCHY_THEMED/"
    cp "$SCRIPT_DIR/contrib/omarchy/qutebrowser-startpage.html.tpl" "$OMARCHY_THEMED/"
    echo -e "${GREEN}✓ Templates installed to $OMARCHY_THEMED/${RESET}"

    # 4. Install theme synchronization hook
    mkdir -p "$OMARCHY_HOOKS"
    echo -e "${BLUE}➜ Installing Omarchy theme-set hook...${RESET}"
    cp "$SCRIPT_DIR/contrib/omarchy/qutebrowser-theme" "$OMARCHY_HOOKS/"
    chmod +x "$OMARCHY_HOOKS/qutebrowser-theme"
    echo -e "${GREEN}✓ Hook installed to $OMARCHY_HOOKS/qutebrowser-theme${RESET}"

    # 5. Trigger theme sync for active theme
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

# 6. Configure Hyprland Window Rule (Terminal 0.90 Opacity)
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

echo -e "\n${GREEN}${BOLD}🎉 Installation Complete!${RESET}"
echo -e "Launch with: ${CYAN}qutebrowser${RESET}"
echo -e "Vim shortcuts: ${YELLOW}o/O${RESET} (open), ${YELLOW}f/F${RESET} (hints), ${YELLOW}d/u${RESET} (close/undo tab), ${YELLOW}M${RESET} (stream in MPV), ${YELLOW}td${RESET} (toggle darkmode)\n"
