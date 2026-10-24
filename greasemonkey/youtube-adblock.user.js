// ==UserScript==
// @name         Brave-Grade YouTube AdBlocker
// @namespace    https://github.com/m7sh/omarchy-qutebrowser
// @version      2.0.0
// @description  Fast-forward and skip YouTube video ads, strip ad slots and hide ad banners
// @match        *://*.youtube.com/*
// @run-at       document-start
// @grant        none
// ==/UserScript==

(function() {
  'use strict';

  // 1. Intercept ytInitialPlayerResponse before YouTube player initializes
  function pruneAds(obj) {
    if (!obj || typeof obj !== 'object') return obj;
    try {
      delete obj.adPlacements;
      delete obj.playerAds;
      delete obj.adSlots;
      if (obj.playerResponse) {
        delete obj.playerResponse.adPlacements;
        delete obj.playerResponse.playerAds;
        delete obj.playerResponse.adSlots;
      }
    } catch(e) {}
    return obj;
  }

  let originalPlayerResponse = window.ytInitialPlayerResponse;
  try {
    Object.defineProperty(window, 'ytInitialPlayerResponse', {
      get() { return originalPlayerResponse; },
      set(val) { originalPlayerResponse = pruneAds(val); },
      configurable: true
    });
  } catch(e) {}

  // 2. Inject CSS element hiding immediately
  function injectCosmetics() {
    if (document.getElementById('__brave_yt_cosmetics__')) return;
    const style = document.createElement('style');
    style.id = '__brave_yt_cosmetics__';
    style.textContent = `
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
    `;
    (document.head || document.documentElement).appendChild(style);
  }

  if (document.head || document.documentElement) {
    injectCosmetics();
  } else {
    document.addEventListener('DOMContentLoaded', injectCosmetics);
  }

  // 3. Fast-forward & skip video ads if any slip through
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
    injectCosmetics();

    const skipBtn = document.querySelector(SKIP_SELECTORS);
    if (skipBtn) {
      try { skipBtn.click(); } catch(e) {}
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
    } catch(e) {}
  }

  const observer = new MutationObserver(skipVideoAd);
  observer.observe(document.documentElement, { childList: true, subtree: true });
  setInterval(skipVideoAd, 300);
})();
