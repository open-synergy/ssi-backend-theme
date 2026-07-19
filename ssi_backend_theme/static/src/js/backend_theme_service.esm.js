import {registry} from "@web/core/registry";
import {session} from "@web/session";

// Maps a `backend_theme` session_info key to the CSS custom property
// it feeds. `font_family` is consumed by the SCSS bridge file in
// static/src/scss (var(--ssi-font-family, ...) fallback on
// $font-family-sans-serif). `color_list_header_bg`/
// `color_list_row_hover_bg` are consumed the same way by
// backend_theme_list_view.scss (var(--ssi-list-header-bg, ...) /
// var(--ssi-list-row-hover-bg, ...)) — the list renderer's own
// `--ListRenderer-thead-bg-color` is re-declared with a literal value
// on `.o_list_renderer` by Odoo core itself, so setting it directly on
// the document root here would always be shadowed; bridging through a
// property core never touches, then reading it with a `var()`
// fallback in our own SCSS, is the only way a runtime value can reach
// it. `color_primary`/`color_navbar_bg`/`color_text_body`/
// `color_view_background`/`color_success`/`color_info`/
// `color_warning`/`color_danger` are NOT applied here — Odoo core/
// Bootstrap 5 feed those through Sass color functions/variables
// (darken()/tint-color()/shade-color(), `$o-main-text-color`, `$o-view-
// background-color`, `$o-success`/`$o-info`/`$o-warning`/`$o-danger`),
// which reject a `var()` reference outright, so they are instead baked
// into a recompiled asset by `backend_theme._sync_active_theme_scss_asset()`
// (models/backend_theme.py) whenever the active theme changes.
const CSS_VARIABLE_BY_THEME_KEY = {
    font_family: "--ssi-font-family",
    color_list_header_bg: "--ssi-list-header-bg",
    color_list_row_hover_bg: "--ssi-list-row-hover-bg",
};

// Odoo 19's navbar already reads `var(--NavBar-entry-color, ...)`
// natively (web/static/src/webclient/navbar/navbar.variables.scss), so
// the navbar text color is applied directly to that existing custom
// property instead of inventing a new SCSS bridge for it.
const NAVBAR_ENTRY_COLOR_VARIABLE = "--NavBar-entry-color";

export const backendThemeService = {
    start() {
        const theme = session.backend_theme || {};
        const root = document.documentElement;
        for (const [themeKey, cssVariable] of Object.entries(
            CSS_VARIABLE_BY_THEME_KEY
        )) {
            if (theme[themeKey]) {
                root.style.setProperty(cssVariable, theme[themeKey]);
            }
        }
        if (theme.color_navbar_text) {
            root.style.setProperty(
                NAVBAR_ENTRY_COLOR_VARIABLE,
                theme.color_navbar_text
            );
        }
    },
};

registry
    .category("services")
    .add("ssi_backend_theme.backend_theme", backendThemeService);
