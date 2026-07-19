// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {AppsSidebar} from "./apps_sidebar.esm";
import {NavBar} from "@web/webclient/navbar/navbar";
import {getEffectiveAppSubmenuPosition} from "./app_submenu_position.esm";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";

// Only the static `components` registry needs patching so the template
// extension (navbar_patch.xml) can use `<AppsSidebar/>`. `NavBar`'s own
// behavior (state, services, adapt logic, ...) is untouched — the mobile
// off-canvas sidebar (`web.NavBar.AppsMenu.Sidebar`, guarded by
// `this.ui.isSmall`) is a fully separate template branch, left as-is.
patch(NavBar, {
    components: {...NavBar.components, AppsSidebar},
});

patch(NavBar.prototype, {
    /**
     * Whether the active theme's `show_sidebar` (issue #16) allows the
     * desktop sidebar to render at all.
     *
     * Anything other than exactly `false` (missing `session.backend_theme`,
     * an unset/non-boolean value) is treated as shown — never raises
     * client-side. When this is `false`, `<AppsSidebar/>` (navbar_patch.xml)
     * is never mounted, so it never sets the `--o-ssi-apps-sidebar-current-
     * width` custom property (apps_sidebar.esm.js), and `.o_web_client`
     * (apps_sidebar.scss) falls back to its `0` default — the backend
     * returns to Odoo's stock layout with no leftover gap.
     *
     * @returns {Boolean}
     */
    get ssiShowAppsSidebar() {
        const backendTheme = session.backend_theme || {};
        return backendTheme.show_sidebar !== false;
    },

    /**
     * Whether the core horizontal navbar should still render "Current App
     * Sections" (issue #17): only when the active theme's effective
     * `app_submenu_position` resolves to "navbar". "sidebar" and "popover"
     * both move the submenu into `<AppsSidebar/>` instead (apps_sidebar.esm.js)
     * and must never also render here, or the same submenu would show
     * twice at once (navbar_patch.xml).
     *
     * @returns {Boolean}
     */
    get ssiShowNavbarSubmenu() {
        return getEffectiveAppSubmenuPosition() === "navbar";
    },
});
