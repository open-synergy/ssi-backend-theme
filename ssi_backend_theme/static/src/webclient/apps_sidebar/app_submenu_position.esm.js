// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {session} from "@web/session";

// The only three values `backend_theme.app_submenu_position` (issue #17)
// can resolve to client-side. Shared by navbar_patch.esm.js (deciding
// whether the core horizontal navbar still renders "Current App Sections")
// and apps_sidebar.esm.js (deciding what the sidebar itself renders), so
// the two never disagree and a submenu is never shown twice at once.
export const APP_SUBMENU_POSITIONS = ["navbar", "sidebar", "popover"];

/**
 * Resolve where the active app's submenu sections should be shown.
 *
 * Any value other than exactly "sidebar" or "popover" (missing
 * `session.backend_theme`, an unset/unknown selection value) is treated
 * as "navbar" -- never raises client-side, mirroring the server-side
 * fallback in `backend_theme._get_backend_theme_session_values()`.
 *
 * "sidebar" and "popover" both require the sidebar itself to be visible:
 * whenever the active theme's `show_sidebar` is `false`, both degrade to
 * "navbar" since neither mode has anywhere left to render (Keputusan
 * Desain, issue #17) -- otherwise the submenu would disappear entirely.
 *
 * @returns {("navbar"|"sidebar"|"popover")}
 */
export function getEffectiveAppSubmenuPosition() {
    const backendTheme = session.backend_theme || {};
    if (backendTheme.show_sidebar === false) {
        return "navbar";
    }
    const position = backendTheme.app_submenu_position;
    return APP_SUBMENU_POSITIONS.includes(position) ? position : "navbar";
}
