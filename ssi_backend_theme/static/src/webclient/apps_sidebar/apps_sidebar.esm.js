// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {Component, onMounted, onWillUnmount, useState} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {browser} from "@web/core/browser/browser";
import {session} from "@web/session";
import {useService} from "@web/core/utils/hooks";

// Device-local preference: intentionally NOT stored server-side. Only the
// *default* (used the very first time, before this key is ever written)
// comes from the database, via the active `backend_theme.sidebar_default`
// exposed on `session.backend_theme`.
export const SIDEBAR_STATE_STORAGE_KEY = "ssi_backend_theme.sidebar_state";

// Custom property `.o_web_client` (apps_sidebar.scss) reads to shift the
// navbar + content area by the sidebar's *current* width. It always points
// at one of the two width custom properties apps_sidebar.scss sets on
// `:root` (`--o-ssi-apps-sidebar-width` /
// `--o-ssi-apps-sidebar-width-collapsed`) rather than a literal pixel
// value, so the two Sass constants stay the single source of truth.
const CURRENT_WIDTH_PROPERTY = "--o-ssi-apps-sidebar-current-width";

/**
 * Resolve the collapsed/expanded default carried by the active theme.
 *
 * Any value other than exactly "collapsed" — missing `session.backend_theme`,
 * no active theme (module default "expanded"), or any future/unexpected
 * selection value — is treated as "expanded". Never raises client-side.
 *
 * @returns {Boolean}
 */
function isThemeDefaultCollapsed() {
    const backendTheme = session.backend_theme || {};
    return backendTheme.sidebar_default === "collapsed";
}

/**
 * Resolve the sidebar's initial collapsed state.
 *
 * `localStorage` (per-device preference) wins whenever it already holds a
 * value; the theme's `sidebar_default` is only consulted the first time,
 * before anything has ever been persisted on this device.
 *
 * @returns {Boolean}
 */
function getInitialCollapsedState() {
    const stored = browser.localStorage.getItem(SIDEBAR_STATE_STORAGE_KEY);
    if (stored === "collapsed") {
        return true;
    }
    if (stored === "expanded") {
        return false;
    }
    return isThemeDefaultCollapsed();
}

export class AppsSidebar extends Component {
    static template = "ssi_backend_theme.AppsSidebar";
    static props = {};

    setup() {
        this.menuService = useService("menu");
        this.state = useState({collapsed: getInitialCollapsedState()});

        onMounted(() => this.updateCurrentWidthProperty());

        // Re-render when the current app / menu tree changes so the
        // highlighted app stays in sync — the same event core's own NavBar
        // listens to (see web/static/src/webclient/navbar/navbar.js).
        this.onMenusChanged = () => this.render();
        this.env.bus.addEventListener("MENUS:APP-CHANGED", this.onMenusChanged);
        onWillUnmount(() => {
            this.env.bus.removeEventListener("MENUS:APP-CHANGED", this.onMenusChanged);
            // Mirrors the `!ui.isSmall` guard in navbar_patch.xml: once the
            // sidebar stops being rendered (e.g. a responsive resize into
            // `ui.isSmall`, not just a full reload), the shift it caused
            // must go away too, so `.o_web_client` falls back to 0.
            document.documentElement.style.removeProperty(CURRENT_WIDTH_PROPERTY);
        });
    }

    get apps() {
        return this.menuService.getApps();
    }

    get currentApp() {
        return this.menuService.getCurrentApp();
    }

    isCurrentApp(app) {
        return Boolean(this.currentApp) && this.currentApp.id === app.id;
    }

    /**
     * Point `--o-ssi-apps-sidebar-current-width` at whichever of the two
     * width custom properties (apps_sidebar.scss, set on `:root`) matches
     * the current collapsed state.
     */
    updateCurrentWidthProperty() {
        document.documentElement.style.setProperty(
            CURRENT_WIDTH_PROPERTY,
            this.state.collapsed
                ? "var(--o-ssi-apps-sidebar-width-collapsed)"
                : "var(--o-ssi-apps-sidebar-width)"
        );
    }

    get toggleLabel() {
        return this.state.collapsed ? _t("Expand sidebar") : _t("Collapse sidebar");
    }

    getMenuItemHref(menu) {
        return `/odoo/${menu.actionPath || "action-" + menu.actionID}`;
    }

    toggle() {
        this.state.collapsed = !this.state.collapsed;
        browser.localStorage.setItem(
            SIDEBAR_STATE_STORAGE_KEY,
            this.state.collapsed ? "collapsed" : "expanded"
        );
        this.updateCurrentWidthProperty();
    }

    onAppClick(app) {
        this.menuService.selectMenu(app);
    }
}
