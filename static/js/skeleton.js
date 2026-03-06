/**
 * AI Invigilator — Loading & Skeleton Helpers
 * Handles: skeleton show/hide, image loading states,
 *          button loading states, page loader
 */
(function () {
    'use strict';

    /* ── Image loading state ───────────────────────────────── */
    document.addEventListener('DOMContentLoaded', function () {
        // Live feed images — show shimmer until loaded
        document.querySelectorAll('img[src*="get_snapshot"]').forEach(function (img) {
            img.classList.add('img-loading');
            img.addEventListener('load',  function () { img.classList.remove('img-loading'); });
            img.addEventListener('error', function () {
                img.classList.remove('img-loading');
                // Replace broken image with feed-loading placeholder
                const placeholder = document.createElement('div');
                placeholder.className = 'feed-loading';
                placeholder.innerHTML = `
                    <div class="feed-spinner"></div>
                    <span class="feed-label">No Feed</span>
                `;
                if (img.parentNode) img.parentNode.replaceChild(placeholder, img);
            });
        });

        // Generic images
        document.querySelectorAll('img:not([src*="get_snapshot"])').forEach(function (img) {
            if (!img.complete) {
                img.style.opacity = '0';
                img.style.transition = 'opacity 0.3s ease';
                img.addEventListener('load', function () {
                    img.style.opacity = '1';
                });
            }
        });
    });

    /* ── Button loading state ──────────────────────────────── */
    window.Loader = window.Loader || {};

    /**
     * Put a button into loading state
     * Usage: Loader.buttonLoad(btn)
     */
    window.Loader.buttonLoad = function (btn) {
        if (!btn) return;
        const label = btn.innerHTML;
        btn._originalLabel = label;
        btn.classList.add('btn-loading');
        btn.innerHTML = `<span class="btn-text">${label}</span>`;
    };

    /**
     * Restore button from loading state
     * Usage: Loader.buttonDone(btn)
     */
    window.Loader.buttonDone = function (btn) {
        if (!btn) return;
        btn.classList.remove('btn-loading');
        if (btn._originalLabel) btn.innerHTML = btn._originalLabel;
    };

    /**
     * Auto-load: attach to any form submit button with data-loading
     * Usage: <button class="btn-modern" data-loading="Scheduling...">Schedule</button>
     */
    document.addEventListener('DOMContentLoaded', function () {
        document.querySelectorAll('form').forEach(function (form) {
            form.addEventListener('submit', function () {
                const btn = form.querySelector('button[type="submit"][data-loading]');
                if (btn) window.Loader.buttonLoad(btn);
            });
        });
    });

    /* ── Skeleton helpers ──────────────────────────────────── */

    /**
     * Replace a container with skeleton rows
     * Usage: Loader.showSkeleton('#container', 'session', 3)
     */
    window.Loader.showSkeleton = function (selector, type, count) {
        const container = document.querySelector(selector);
        if (!container) return;
        container._originalContent = container.innerHTML;
        count = count || 3;

        const html = Array.from({ length: count }).map(function () {
            if (type === 'session') {
                return `
                <div class="skeleton-session">
                    <div class="skeleton sk-rect sk-thumb"></div>
                    <div class="sk-body">
                        <div class="skeleton sk-line sk-w-2/3"></div>
                        <div class="skeleton sk-line sk-line-sm sk-w-1/2"></div>
                        <div class="skeleton sk-line sk-line-sm sk-w-1/3"></div>
                    </div>
                </div>`;
            }
            if (type === 'row') {
                return `
                <div class="skeleton-row">
                    <div class="skeleton sk-circle sk-avatar"></div>
                    <div style="flex:1;display:flex;flex-direction:column;gap:6px;">
                        <div class="skeleton sk-line sk-w-1/2"></div>
                        <div class="skeleton sk-line sk-line-sm sk-w-1/3"></div>
                    </div>
                    <div class="skeleton sk-rect" style="width:60px;height:24px;"></div>
                </div>`;
            }
            if (type === 'alert') {
                return `
                <div class="skeleton-alert">
                    <div class="skeleton sk-circle" style="width:8px;height:8px;flex-shrink:0;"></div>
                    <div style="flex:1;display:flex;flex-direction:column;gap:6px;">
                        <div class="skeleton sk-line sk-w-3/4"></div>
                        <div class="skeleton sk-line sk-line-sm sk-w-1/2"></div>
                    </div>
                    <div class="skeleton sk-rect" style="width:50px;height:20px;border-radius:4px;"></div>
                </div>`;
            }
            if (type === 'stat') {
                return `
                <div class="skeleton-stat">
                    <div class="skeleton sk-icon"></div>
                    <div class="skeleton sk-value"></div>
                    <div class="skeleton sk-label"></div>
                </div>`;
            }
            // Default: simple lines
            return `
            <div style="padding:var(--sp-3) 0;display:flex;flex-direction:column;gap:8px;">
                <div class="skeleton sk-line sk-w-3/4"></div>
                <div class="skeleton sk-line sk-line-sm sk-w-1/2"></div>
            </div>`;
        }).join('');

        container.innerHTML = html;
    };

    /**
     * Restore container from skeleton
     * Usage: Loader.hideSkeleton('#container')
     */
    window.Loader.hideSkeleton = function (selector) {
        const container = document.querySelector(selector);
        if (!container || !container._originalContent) return;
        container.innerHTML = container._originalContent;
        delete container._originalContent;
    };

    /* ── Page loader ───────────────────────────────────────── */

    /**
     * Show full-page loader
     * Usage: Loader.pageStart('Loading sessions...')
     */
    window.Loader.pageStart = function (message) {
        let overlay = document.getElementById('pageLoader');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'pageLoader';
            overlay.className = 'page-loading';
            overlay.innerHTML = `
                <div class="pl-logo">🎓 AI Invigilator</div>
                <div class="pl-bar"><div class="pl-fill"></div></div>
                <div class="pl-text">${message || 'Loading...'}</div>
            `;
            document.body.appendChild(overlay);
        }
        overlay.classList.remove('hidden');
    };

    /**
     * Hide full-page loader
     * Usage: Loader.pageEnd()
     */
    window.Loader.pageEnd = function () {
        const overlay = document.getElementById('pageLoader');
        if (!overlay) return;
        overlay.classList.add('hidden');
        setTimeout(function () { overlay.remove(); }, 350);
    };

    /* ── Auto-hide page loader on full load ────────────────── */
    window.addEventListener('load', function () {
        window.Loader.pageEnd();
    });

})();