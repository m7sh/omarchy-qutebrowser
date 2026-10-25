# ==============================================================================
# Brave-style cosmetic filtering for qutebrowser
# ==============================================================================
# qutebrowser's `braveadblock` component only filters network requests; its FAQ
# explicitly says element hiding (cosmetic filtering) is not implemented.
#
# Brave's adblock-rust engine does know how to produce cosmetic resources:
#   engine.url_cosmetic_resources(url)      -> hide/style selectors + exceptions
#   engine.hidden_class_id_selectors(...)   -> generic .class/#id hide rules
#
# This module asks the *same* engine qutebrowser already loaded and injects the
# resulting CSS into each page. It is intentionally read-only: it never adds
# rules or changes filtering decisions.
#
# It uses qutebrowser internals (objreg/tab signals), so it is written
# defensively and degrades to a no-op if those internals are unavailable.
# ==============================================================================
import json
import sys
import weakref

from qutebrowser.config import config
from qutebrowser.qt.core import QCoreApplication, QTimer
from qutebrowser.utils import log, objreg

_STYLE_ID = "__brave_cosmetic_filters__"
_TIMER = None
_KNOWN_BROWSERS = weakref.WeakSet()
_ATTACHED_TABS = weakref.WeakSet()
_GENERICHIDE_ENGINE = None
_GENERICHIDE_USABLE = True

# YouTube-specific ad blocking: hides ad slots, banners, mastheads, sponsor boxes
# and skips in-stream video ads that googlevideo media streams deliver.
_YOUTUBE_CSS = """
ytd-ad-slot-renderer,
#masthead-ad,
.ytp-ad-module,
.ytp-ad-overlay-container,
.ytp-ad-overlay-slot,
.ytp-ad-image-overlay,
.ytp-ad-text-overlay,
#player-ads,
ytd-banner-promo-renderer,
ytd-in-feed-ad-layout-renderer,
ytd-action-companion-ad-renderer,
#clarify-box,
ytd-statement-banner-renderer,
ytd-compact-promoted-video-renderer,
ytd-promoted-sparkles-web-renderer,
ytd-promoted-sparkles-text-search-renderer,
.ytd-search-pyv-renderer,
ytd-search-pyv-renderer,
ytd-video-ad-renderer,
.ytp-ad-progress-list,
.ytp-ad-message-container,
#related ytd-ad-slot-renderer,
#secondary ytd-ad-slot-renderer,
ytd-engagement-panel-section-list-renderer[target-id="engagement-panel-ads"],
tp-yt-paper-dialog:has(#feedback.ytd-enforcement-message-view-model) {
  display: none !important;
}
"""

_YOUTUBE_JS = r"""
(function () {
  if (window.__brave_yt_adblock_active) return;
  window.__brave_yt_adblock_active = true;

  const SKIP_SELECTORS = [
    '.ytp-skip-ad-button',
    '.ytp-ad-skip-button',
    '.ytp-ad-skip-button-modern',
    '.videoAdUiSkipButton',
    'button.ytp-ad-skip-button-modern',
    '.ytp-ad-skip-button-slot button',
    '[id^="skip-button:"]',
  ].join(',');

  function skipVideoAd() {
    const skipBtn = document.querySelector(SKIP_SELECTORS);
    if (skipBtn) {
      try { skipBtn.click(); } catch (e) {}
    }

    const player = document.querySelector('.html5-video-player');
    const adShowing = (player && (player.classList.contains('ad-showing') || player.classList.contains('ad-interrupting'))) ||
                      document.querySelector('.ad-showing') ||
                      document.querySelector('.ad-interrupting');
    if (!adShowing) return;

    const video = document.querySelector('video.html5-main-video') || document.querySelector('video');
    if (!video) return;

    if (player && player.classList.contains('ytp-live')) return;
    if (document.querySelector('.ytp-live-badge')) return;
    if (!isFinite(video.duration) || video.duration <= 0) return;

    try {
      video.muted = true;
      video.playbackRate = 16.0;
      video.currentTime = video.duration;
    } catch (e) {}
  }

  const observer = new MutationObserver(skipVideoAd);
  observer.observe(document.documentElement, { childList: true, subtree: true });
  setInterval(skipVideoAd, 300);
  skipVideoAd();
})();
"""

# Collect the class/id tokens that generic cosmetic rules can match against.
# Capped so pathological pages cannot stall the renderer or the IPC channel.
_TOKEN_JS = r"""
(function () {
  try {
    var classes = new Set();
    var ids = new Set();
    var nodes = document.getElementsByTagName('*');
    for (var i = 0; i < nodes.length && i < 6000; i++) {
      var el = nodes[i];
      if (el.id) ids.add(el.id);
      var cl = el.classList;
      if (cl) {
        for (var j = 0; j < cl.length; j++) classes.add(cl[j]);
      }
      if (classes.size > 4000 && ids.size > 1500) break;
    }
    return JSON.stringify({
      classes: Array.from(classes),
      ids: Array.from(ids)
    });
  } catch (e) {
    return '';
  }
})();
"""


def _adblock_module():
    """Return qutebrowser's live braveadblock module, if it exists.

    It is looked up in sys.modules on purpose: qutebrowser removes modules
    imported while reading config.py from sys.modules afterwards, so a
    module-level import here would become a stale copy with no engine.
    """
    return sys.modules.get("qutebrowser.components.braveadblock")


def _engine():
    """Return qutebrowser's live adblock-rust engine, if available."""
    module = _adblock_module()
    blocker = getattr(module, "ad_blocker", None) if module is not None else None
    return getattr(blocker, "_engine", None)


def _honor_generichide(engine):
    """Whether the engine's `$generichide` flag can be trusted.

    adblock-rust 0.5.6 (the version qutebrowser ships) reports
    `generichide=True` for every page once the full Brave/uBO catalog is
    loaded, even for a random `.invalid` host where no `$ghide` exception can
    possibly apply. In that case respecting the flag would silently disable
    all generic cosmetic rules, so probe with a sentinel host and ignore it.
    """
    global _GENERICHIDE_ENGINE, _GENERICHIDE_USABLE
    if engine is _GENERICHIDE_ENGINE:
        return _GENERICHIDE_USABLE
    try:
        usable = not engine.url_cosmetic_resources(
            "https://brave-cosmetics.invalid/").generichide
    except Exception:
        usable = True
    _GENERICHIDE_ENGINE = engine
    _GENERICHIDE_USABLE = usable
    if not usable:
        log.misc.debug(
            "brave-cosmetics: engine reports $generichide for every page; "
            "ignoring the flag")
    return usable


def _enabled_for(url):
    """Whether network blocking (and thus cosmetics) is on for this page."""
    if config.val.content.blocking.method not in ("auto", "adblock", "both"):
        return False
    try:
        return bool(config.get("content.blocking.enabled", url=url))
    except Exception:
        return True


def _css_from_parts(hide_selectors=(), style_selectors=None,
                    generic_selectors=()):
    """Build a CSS stylesheet from adblock-rust cosmetic resources."""
    rules = []
    for selector in hide_selectors:
        selector = selector.strip()
        if selector:
            rules.append(f"{selector}{{display:none !important}}")
    for selector, declarations in (style_selectors or {}).items():
        selector = selector.strip()
        if selector and declarations:
            rules.append(f"{selector}{{{';'.join(declarations)}}}")
    for selector in generic_selectors:
        selector = selector.strip()
        if selector:
            rules.append(f"{selector}{{display:none !important}}")
    return "\n".join(rules)


def _css_from_resources(resources, generic_selectors=()):
    """Turn a UrlSpecificResources object into a CSS stylesheet."""
    return _css_from_parts(resources.hide_selectors,
                           resources.style_selectors,
                           generic_selectors)


def _inject(tab, css, *, append=False):
    """Install/replace the cosmetic stylesheet in the given tab."""
    if not css:
        return
    operation = "s.textContent += %s;" if append else "s.textContent = %s;"
    js = (
        "(function(){var id=%s;var s=document.getElementById(id);"
        "if(!s){s=document.createElement('style');s.id=id;"
        "(document.head||document.documentElement).appendChild(s);}"
        + operation +
        "})();"
    ) % (json.dumps(_STYLE_ID), json.dumps(css))
    try:
        tab.run_js_async(js)
    except Exception:
        log.misc.debug("brave-cosmetics: could not inject into %s",
                       tab.url().toDisplayString(), exc_info=True)


def _apply_generic(tab, page_url, exceptions, result):
    """Second pass: generic .class/#id rules based on the real DOM tokens."""
    if not result:
        return
    if tab.url().toString() != page_url:
        return
    engine = _engine()
    if engine is None:
        return
    try:
        tokens = json.loads(result)
        classes = [str(c) for c in tokens.get("classes", [])]
        ids = [str(i) for i in tokens.get("ids", [])]
        if not classes and not ids:
            return
        selectors = engine.hidden_class_id_selectors(
            classes, ids, set(exceptions))
    except Exception:
        log.misc.debug("brave-cosmetics: generic selector lookup failed",
                       exc_info=True)
        return
    _inject(tab, _css_from_parts(generic_selectors=selectors), append=True)
    log.misc.debug("brave-cosmetics: %d generic selectors for %s",
                   len(selectors), page_url)


def _apply(tab):
    """Inject all cosmetic resources for the tab's current URL."""
    engine = _engine()
    if engine is None:
        return
    try:
        url = tab.url()
    except Exception:
        return
    if not url.isValid() or url.scheme() not in ("http", "https"):
        return
    if not _enabled_for(url):
        return
    page_url = url.toString()
    host = url.host().lower()
    is_youtube = host == "youtube.com" or host.endswith(".youtube.com")
    try:
        resources = engine.url_cosmetic_resources(page_url)
    except Exception:
        log.misc.debug("brave-cosmetics: cosmetic lookup failed for %s",
                       page_url, exc_info=True)
        return

    css = _css_from_resources(resources)
    if is_youtube:
        css = "\n".join(part for part in (css, _YOUTUBE_CSS.strip()) if part)
    _inject(tab, css)
    if css:
        log.misc.debug("brave-cosmetics: %d hide + %d style selectors for %s",
                       len(resources.hide_selectors),
                       len(resources.style_selectors), page_url)

    # `$generichide` means generic class/id rules must not be applied here.
    if not (resources.generichide and _honor_generichide(engine)):
        try:
            tab.run_js_async(
                _TOKEN_JS,
                lambda result: _apply_generic(
                    tab, page_url, resources.exceptions, result))
        except Exception:
            log.misc.debug("brave-cosmetics: token scan failed for %s",
                           page_url, exc_info=True)

    # Dedicated YouTube in-stream ad skipping. The CSS above is replaced on
    # every pass, so SPA navigation cannot accumulate duplicate rules.
    if is_youtube:
        try:
            tab.run_js_async(_YOUTUBE_JS)
        except Exception:
            log.misc.debug("brave-cosmetics: youtube adblock injection failed",
                           exc_info=True)


def _attach(tab):
    """Connect a newly created (or existing) tab exactly once."""
    if tab in _ATTACHED_TABS:
        return
    _ATTACHED_TABS.add(tab)
    tab.load_finished.connect(
        lambda ok, t=tab: _apply(t) if ok else None)
    # SPA navigations (YouTube, Reddit, ...) change the URL without a reload.
    tab.url_changed.connect(
        lambda _url, t=tab: QTimer.singleShot(700, lambda: _apply(t)))
    if not tab.url().isEmpty():
        _apply(tab)


def _scan():
    """Attach to every existing tab and every future tab/window."""
    try:
        windows = list(objreg.window_registry.values())
    except Exception:
        return
    for window in windows:
        browser = getattr(window, "tabbed_browser", None)
        if browser is None:
            continue
        if browser not in _KNOWN_BROWSERS:
            _KNOWN_BROWSERS.add(browser)
            browser.new_tab.connect(lambda tab, _idx: _attach(tab))
        try:
            tab_widget = browser.widget
            for idx in range(tab_widget.count()):
                _attach(tab_widget.widget(idx))
        except Exception:
            log.misc.debug("brave-cosmetics: tab scan failed", exc_info=True)


def _install():
    """Start the scanner once the event loop and main window exist."""
    global _TIMER
    module = _adblock_module()
    if _TIMER is not None or (module is not None and getattr(
            module, "_omarchy_cosmetics_timer", None) is not None):
        return
    if _engine() is None:
        if module is None:
            # Config is read before qutebrowser's components are initialized.
            QTimer.singleShot(500, _install)
            return
        if getattr(module, "adblock", None) is None:
            log.misc.debug("brave-cosmetics: python-adblock is not installed; "
                           "cosmetic filtering disabled")
            return
        QTimer.singleShot(500, _install)
        return
    log.misc.debug("brave-cosmetics: adblock engine ready; scanning tabs")
    _scan()
    _TIMER = QTimer()
    _TIMER.timeout.connect(_scan)
    _TIMER.start(2000)
    # Keep the timer alive across :config-source reloads too.
    setattr(module, "_omarchy_cosmetics_timer", _TIMER)


def _hook_app_init():
    """Run _install after qutebrowser has created its components and window."""
    from qutebrowser import app as qbapp

    if getattr(qbapp, "_omarchy_cosmetics_hooked", False):
        return
    setattr(qbapp, "_omarchy_cosmetics_hooked", True)
    original = qbapp.init

    def init(*args, **kwargs):
        result = original(*args, **kwargs)
        QTimer.singleShot(0, _install)
        return result

    qbapp.init = init


_hook_app_init()

# On a later :config-source, app.init() already ran; schedule directly.
if QCoreApplication.instance() is not None:
    QTimer.singleShot(0, _install)
