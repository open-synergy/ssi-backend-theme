// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {session} from "@web/session";

// The only three values `backend_theme.chatter_position` (issue #19) can
// resolve to client-side. Shared by chatter_patch.esm.js.
export const CHATTER_POSITIONS = ["auto", "right", "bottom"];

/**
 * Resolve the active theme's requested chatter position.
 *
 * Any value other than exactly "right" or "bottom" (missing
 * `session.backend_theme`, an unset/unknown selection value) is treated as
 * "auto" -- never raises client-side, mirroring the server-side fallback
 * in `backend_theme._get_backend_theme_session_values()`. "auto" means
 * "do not patch anything" -- Odoo's own responsive chatter layout is left
 * untouched.
 *
 * @returns {("auto"|"right"|"bottom")}
 */
export function getEffectiveChatterPosition() {
    const backendTheme = session.backend_theme || {};
    const position = backendTheme.chatter_position;
    return CHATTER_POSITIONS.includes(position) ? position : "auto";
}

/**
 * Whether the active theme wants a fold/unfold button on the chatter.
 *
 * Anything other than exactly `true` (missing `session.backend_theme`, an
 * unset/non-boolean value) is treated as "no button" -- matches the
 * field's own default (`False`).
 *
 * @returns {Boolean}
 */
export function getShowChatterToggle() {
    const backendTheme = session.backend_theme || {};
    return backendTheme.show_chatter_toggle === true;
}
