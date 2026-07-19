import {registry} from "@web/core/registry";
import {session} from "@web/session";

// Maps a `backend_theme` session_info key to the CSS custom property
// it feeds. `font_family` is consumed by the SCSS bridge file in
// static/src/scss (var(--ssi-font-family, ...) fallback on
// $font-family-sans-serif). `color_primary`/`color_navbar_bg` are
// NOT applied here — Odoo core/Bootstrap 5 feed those two through Sass
// color functions (darken()/tint-color()/shade-color()), which reject a
// `var()` reference outright, so they are instead baked into a
// recompiled asset by `backend_theme._sync_active_theme_scss_asset()`
// (models/backend_theme.py) whenever the active theme changes.
const CSS_VARIABLE_BY_THEME_KEY = {
    font_family: "--ssi-font-family",
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
