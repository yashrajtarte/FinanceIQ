"""
modules/animations.py
======================
Drop-in animation helpers: page-enter transitions, a branded loading
animation (to replace st.spinner), and skeleton shimmer placeholders.

All colors match the app's existing dark theme (#6366f1 / #34d399 / #13132a
/ #2a2a4a) so nothing looks bolted-on.

USAGE
-----
1. Page transitions — call once at the very top of each render_*() function:

    from modules.animations import page_enter

    def render_forecast():
        page_enter()
        st.markdown("# 📈 Forecast & Projections")
        ...

2. Custom loader — swap st.spinner(...) for loader(...):

    from modules.animations import loader

    with loader("Crunching your numbers..."):
        df = get_snapshots()

3. Skeleton shimmer — show placeholder cards while data loads:

    from modules.animations import skeleton_cards
    ph = skeleton_cards(n=4)
    df = get_assets()          # slow call
    ph.empty()                 # replace with real KPI pills
"""

import streamlit as st
import streamlit.components.v1 as components
from contextlib import contextmanager

# ── Shared palette (matches forecast.py / net_worth.py / reports.py) ───────
ACCENT = "#6366f1"
ACCENT_2 = "#34d399"
CARD_BG = "#13132a"
BORDER = "#2a2a4a"
MUTED = "#8080aa"


def _inject_once(key: str, css: str):
    """Inject a <style> block only once per session to avoid bloating the DOM."""
    flag = f"_anim_injected_{key}"
    if not st.session_state.get(flag):
        st.markdown(css, unsafe_allow_html=True)
        st.session_state[flag] = True


# ── 1. Page-enter transition (splash loader + content fade-in) ─────────────
_PAGE_ICONS = {
    "forecast": "📈",
    "net_worth": "🏦",
    "reports": "📊",
    "roadmap": "🗺️",
}


def page_enter(
    page_key: str,
    label: str | None = None,
    distance_px: int = 14,
    duration: str = "0.45s",
    splash_ms: int = 1500,
):
    """
    Call at the very top of every render_*() function, before any other
    st.* calls:

        def render_forecast():
            page_enter("forecast", "Forecast")
            st.markdown("# 📈 Forecast & Projections")
            ...

    On a REAL page switch (page_key differs from the last one seen this
    session), this shows a full-screen branded splash — spinning ring +
    pulsing icon + label — for exactly `splash_ms` milliseconds (default
    1000 = 1 second), then fades it out and reveals the page content,
    which itself fades/slides up in a light stagger. Widget-triggered
    reruns on the *same* page (sliders, buttons) don't re-show the splash.

    IMPLEMENTATION NOTE — why this uses a tiny injected script instead of
    pure CSS: a `position: fixed` overlay placed via st.markdown lives
    inside Streamlit's own component tree, and Streamlit sometimes applies
    a CSS `transform` to an ancestor of that tree (e.g. for its own
    animations). Per the CSS spec, `position: fixed` becomes fixed
    relative to the nearest transformed ancestor instead of the real
    browser viewport whenever one exists upstream — which is exactly what
    makes an overlay show up squashed, offset, or only covering part of
    the screen. Attaching the overlay directly to the top-level
    `document.body` (reached via `window.parent.document` from the
    component iframe) sidesteps that entirely, and a real JS timer gives
    an exact, guessable-free duration instead of tuned keyframe percentages.
    """
    last_key = "_anim_last_page"
    nonce_key = "_anim_page_nonce"

    is_new_page = st.session_state.get(last_key) != page_key
    if is_new_page:
        st.session_state[last_key] = page_key
        st.session_state[nonce_key] = st.session_state.get(nonce_key, 0) + 1

    nonce = st.session_state.get(nonce_key, 0)
    anim_name = f"fpFadeSlideIn_{nonce}"
    icon = _PAGE_ICONS.get(page_key, "💰")
    display_label = label or page_key.replace("_", " ").title()

    if is_new_page:
        fade_ms = 280
        hold_ms = max(splash_ms - fade_ms, 50)
        components.html(
            f"""
            <script>
            (function() {{
                var doc = window.parent.document;
                var old = doc.getElementById('fp-splash');
                if (old) old.remove();

                var el = doc.createElement('div');
                el.id = 'fp-splash';
                el.style.cssText = [
                    'position:fixed', 'inset:0', 'z-index:999999',
                    'display:flex', 'flex-direction:column',
                    'align-items:center', 'justify-content:center', 'gap:1rem',
                    'background:radial-gradient(circle at 50% 42%, #14142c 0%, #08081499 100%)',
                    'opacity:1', 'transition:opacity {fade_ms}ms ease'
                ].join(';');

                el.innerHTML = `
                    <style>
                        @keyframes fpSplashSpin_{nonce} {{ to {{ transform: rotate(360deg); }} }}
                        @keyframes fpSplashPulse_{nonce} {{
                            0%, 100% {{ transform: scale(1); }}
                            50%      {{ transform: scale(1.16); }}
                        }}
                    </style>
                    <div style="position:relative;width:64px;height:64px;">
                        <div style="position:absolute;inset:0;border-radius:50%;
                            border:3px solid rgba(99,102,241,0.15);
                            border-top-color:{ACCENT}; border-right-color:{ACCENT_2};
                            animation:fpSplashSpin_{nonce} 0.85s linear infinite;"></div>
                        <div style="position:absolute;inset:0;display:flex;align-items:center;
                            justify-content:center;font-size:1.7rem;
                            animation:fpSplashPulse_{nonce} 1.05s ease-in-out infinite;">{icon}</div>
                    </div>
                    <div style="color:{MUTED};font-family:'DM Sans',sans-serif;font-size:0.82rem;
                        letter-spacing:0.1em;text-transform:uppercase;">Loading {display_label}</div>
                `;

                doc.body.appendChild(el);

                setTimeout(function() {{
                    el.style.opacity = '0';
                    setTimeout(function() {{ el.remove(); }}, {fade_ms});
                }}, {hold_ms});
            }})();
            </script>
            """,
            height=0,
            width=0,
        )

    # Content fade-in is plain CSS on Streamlit's own container (no
    # position:fixed involved), so it isn't affected by the ancestor-
    # transform issue above and can stay a normal st.markdown injection.
    st.markdown(
        f"""
        <style>
        @keyframes {anim_name} {{
            from {{ opacity: 0; transform: translateY({distance_px}px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}
        div.block-container {{
            animation: {anim_name} {duration} cubic-bezier(0.16, 1, 0.3, 1);
        }}
        /* stagger charts/cards slightly so they don't all pop at once */
        div.block-container > div {{
            animation: {anim_name} {duration} cubic-bezier(0.16, 1, 0.3, 1) backwards;
        }}
        div.block-container > div:nth-child(1) {{ animation-delay: 0.00s; }}
        div.block-container > div:nth-child(2) {{ animation-delay: 0.04s; }}
        div.block-container > div:nth-child(3) {{ animation-delay: 0.08s; }}
        div.block-container > div:nth-child(4) {{ animation-delay: 0.12s; }}
        div.block-container > div:nth-child(5) {{ animation-delay: 0.16s; }}

        /* gentle lift on hover for buttons — ties into existing button styling */
        .stButton > button, .stDownloadButton > button {{
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(99,102,241,0.25);
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ── 2. Branded loading animation (replaces st.spinner) ──────────────────────
_LOADER_CSS = f"""
<style>
.fp-loader-wrap {{
    display: flex;
    align-items: center;
    gap: 0.9rem;
    padding: 1.1rem 1.3rem;
    margin: 0.6rem 0;
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}
.fp-ring {{
    width: 26px;
    height: 26px;
    border-radius: 50%;
    border: 3px solid rgba(99,102,241,0.18);
    border-top-color: {ACCENT};
    animation: fpSpin 0.8s linear infinite;
    flex-shrink: 0;
}}
@keyframes fpSpin {{
    to {{ transform: rotate(360deg); }}
}}
.fp-loader-text {{
    color: {MUTED};
    font-family: 'DM Sans', sans-serif;
    font-size: 0.92rem;
}}
.fp-loader-text .fp-dots span {{
    animation: fpBlink 1.4s infinite;
    opacity: 0;
}}
.fp-loader-text .fp-dots span:nth-child(2) {{ animation-delay: 0.2s; }}
.fp-loader-text .fp-dots span:nth-child(3) {{ animation-delay: 0.4s; }}
@keyframes fpBlink {{
    0%, 100% {{ opacity: 0; }}
    50% {{ opacity: 1; }}
}}
</style>
"""


@contextmanager
def loader(message: str = "Loading your data..."):
    """
    Drop-in replacement for `with st.spinner(...)`, styled to match the
    app's dark theme instead of Streamlit's default spinner.

        with loader("Crunching the numbers..."):
            df = get_snapshots()
    """
    placeholder = st.empty()
    placeholder.markdown(
        _LOADER_CSS
        + f"""
        <div class="fp-loader-wrap">
            <div class="fp-ring"></div>
            <div class="fp-loader-text">{message}<span class="fp-dots">
                <span>.</span><span>.</span><span>.</span></span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    try:
        yield
    finally:
        placeholder.empty()


# ── 3. Skeleton shimmer (for KPI pills / cards while data loads) ───────────
_SKELETON_CSS = f"""
<style>
.fp-skel {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 1rem 1rem 0.8rem;
    height: 78px;
    overflow: hidden;
    position: relative;
}}
.fp-skel::after {{
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(
        90deg,
        transparent 0%,
        rgba(99,102,241,0.12) 50%,
        transparent 100%
    );
    animation: fpShimmer 1.3s ease-in-out infinite;
}}
@keyframes fpShimmer {{
    from {{ transform: translateX(-100%); }}
    to   {{ transform: translateX(100%); }}
}}
</style>
"""


def skeleton_cards(n: int = 4):
    """
    Renders `n` shimmering placeholder cards in a row, matching the KPI
    pill dimensions used across the app. Returns the st.empty() container
    so you can call .empty() on it once real data is ready.

        ph = skeleton_cards(4)
        data = slow_fetch()
        ph.empty()
        render_real_kpis(data)
    """
    container = st.empty()
    cards_html = "".join(f'<div class="fp-skel"></div>' for _ in range(n))
    container.markdown(
        _SKELETON_CSS
        + f"""
        <div style="display:grid; grid-template-columns: repeat({n}, 1fr); gap: 0.8rem;">
            {cards_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
    return container
