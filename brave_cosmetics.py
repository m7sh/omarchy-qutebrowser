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
import weakref

from qutebrowser.config import config
from qutebrowser.qt.core import QTimer, QUrl
from qutebrowser.utils import log, objreg
from qutebrowser.components import braveadblock

_STYLE_ID = "__brave_cosmetic_filters__"
_TIMER = None
_KNOWN_BROWSERS = weakref.WeakSet()
_ATTACHED_TABS = weakref.WeakSet()

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


def _engine():
    """Return qutebrowser's live adblock-rust engine, if available."""
    blocker = getattr(braveadblock, "ad_blocker", None)
    return getattr(blocker, "_engine", None)


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
    try:
        resources = engine.url_cosmetic_resources(page_url)
    except Exception:
        log.misc.debug("brave-cosmetics: cosmetic lookup failed for %s",
                       page_url, exc_info=True)
        return

    css = _css_from_resources(resources)
    _inject(tab, css)
    if css:
        log.misc.debug("brave-cosmetics: %d hide + %d style selectors for %s",
                       len(resources.hide_selectors),
                       len(resources.style_selectors), page_url)

    # `$generichide` means generic class/id rules must not be applied here.
    if not resources.generichide:
        try:
            tab.run_js_async(
                _TOKEN_JS,
                lambda result: _apply_generic(
                    tab, page_url, resources.exceptions, result))
        except Exception:
            log.misc.debug("brave-cosmetics: token scan failed for %s",
                           page_url, exc_info=True)


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
    if getattr(braveadblock, "_omarchy_cosmetics_installed", False):
        return
    setattr(braveadblock, "_omarchy_cosmetics_installed", True)
    if _engine() is None:
        log.misc.debug("brave-cosmetics: adblock engine unavailable; "
                       "install python-adblock and restart qutebrowser")
        return
    _scan()
    _TIMER = QTimer()
    _TIMER.timeout.connect(_scan)
    _TIMER.start(2000)


# config.py is read before qutebrowser's components are initialized, so defer
# the first scan until the event loop is running (ad_blocker exists by then).
QTimer.singleShot(0, _install)
