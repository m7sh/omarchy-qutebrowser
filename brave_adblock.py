# ==============================================================================
# Brave-style ad blocking for qutebrowser
# ==============================================================================
# qutebrowser's network blocker is Brave's own adblock-rust engine (through the
# `adblock` Python package), so the only thing needed to get Brave's behaviour
# is the same filter-list catalog and the same two-layer setup:
#
#   1. Brave's ABP/uBO engine for network requests  (content.blocking.adblock)
#   2. A hosts-file layer for trackers that never appear in ABP lists
#      (content.blocking.hosts), enabled by method = "both"
#
# Cosmetic filtering (element hiding) is not implemented by qutebrowser; it is
# supplied separately by brave_cosmetics.py using the cosmetic API of the very
# same adblock-rust engine.
# ==============================================================================
import os

_lists_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "brave-lists.txt")

# Minimal fallback if brave-lists.txt is missing (fresh checkout, manual copy).
_fallback_lists = [
    "https://easylist.to/easylist/easylist.txt",
    "https://easylist.to/easylist/easyprivacy.txt",
    "https://raw.githubusercontent.com/brave/adblock-lists/master/brave-lists/brave-specific.txt",
]

try:
    with open(_lists_path, encoding="utf-8") as _f:
        _brave_lists = [
            line.strip()
            for line in _f
            if line.strip() and not line.lstrip().startswith("#")
        ]
except OSError:
    _brave_lists = _fallback_lists

c.content.blocking.enabled = True

# "both" = Brave's ABP engine + the hosts blocker. Brave itself only uses the
# engine; the hosts layer is a cheap second net for trackers that are not in
# the ABP lists yet.
c.content.blocking.method = "both"

# Brave's default catalog (see brave-lists.txt). This replaces qutebrowser's
# stock EasyList/EasyPrivacy-only defaults.
c.content.blocking.adblock.lists = _brave_lists or _fallback_lists

# StevenBlack is qutebrowser's default; kept explicit for the "both" method.
c.content.blocking.hosts.lists = [
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts",
]

# `ta` = adblock update (the repo already uses the `t` prefix for toggles).
config.bind("ta", "adblock-update")
