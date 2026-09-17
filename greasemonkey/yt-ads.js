// ==UserScript==
// for more updated scripts, see: https://greasyfork.org/en/scripts/by-site/youtube.com
// @name         Auto Skip YouTube Ads
// @version      1.2.0
// @description  Speed up and skip YouTube ads automatically (live-stream safe)
// @author       jso8910 and others
// @match        *://*.youtube.com/*
// ==/UserScript==


(function () {
    'use strict';

    const SKIP_SELECTORS = [
        '.videoAdUiSkipButton',
        '.ytp-ad-skip-button',
        '.ytp-ad-skip-button-modern',
        '.ytp-skip-ad-button',
    ].join(',');

    function isLiveStream(video) {
        const player = document.querySelector('.html5-video-player');
        if (player && player.classList.contains('ytp-live')) return true;
        if (document.querySelector('.ytp-live-badge')) return true;

        // Live streams report an infinite (or non-finite) duration. A finite
        // duration means this is a real ad clip we can safely fast-forward.
        return !isFinite(video.duration);
    }

    function skipAd() {
        const btn = document.querySelector(SKIP_SELECTORS);
        if (btn) {
            btn.click();
        }

        if (!document.querySelector('.ad-showing')) return;

        const video = document.querySelector('video');
        if (!video) return;

        // Never seek a live stream: its ad shares the live timeline, so a
        // huge currentTime clamps to the live edge and jumps to the end.
        if (isLiveStream(video) || !isFinite(video.duration) || video.duration <= 0) {
            return;
        }

        video.currentTime = video.duration;
    }

    // Ads can appear at any moment, so react to DOM changes and poll as a
    // fallback instead of relying on the unreliable 'load' event.
    const observer = new MutationObserver(skipAd);
    observer.observe(document.documentElement, { childList: true, subtree: true });
    setInterval(skipAd, 500);
})();
