// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {Component, onMounted, onWillStart, onWillUnmount, useState} from "@odoo/owl";
import {AppSubmenuPopover} from "./app_submenu_popover.esm";
import {SidebarFooter} from "./sidebar_footer.esm";
import {_t} from "@web/core/l10n/translation";
import {browser} from "@web/core/browser/browser";
import {getEffectiveAppSubmenuPosition} from "./app_submenu_position.esm";
import {session} from "@web/session";
import {usePopover} from "@web/core/popover/popover_hook";
import {useService} from "@web/core/utils/hooks";
import {user} from "@web/core/user";

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
    static components = {SidebarFooter};

    setup() {
        this.menuService = useService("menu");
        this.orm = useService("orm");
        // Issue #17: renders the active app's sections as a popover
        // anchored on its sidebar item, only ever opened from `onAppClick`.
        this.submenuPopover = usePopover(AppSubmenuPopover, {position: "right"});
        // Active company id/name: already available client-side via the
        // `user` singleton (populated from `session.user_companies` at
        // webclient boot) — no extra RPC needed just to know *which*
        // company to show.
        this.companyId = user.activeCompany ? user.activeCompany.id : false;
        this.companyName = user.activeCompany ? user.activeCompany.name : "";
        this.state = useState({
            collapsed: getInitialCollapsedState(),
            // Starts hidden: `uses_default_logo` (existing stored field on
            // `res.company`, core `base` module — read here through the
            // ORM's standard, already-existing generic `read` RPC; no new
            // field/model/controller/RPC is introduced) is only known once
            // the read below resolves. True means the company has no logo
            // of its own — either the field is empty or it still holds the
            // generic Odoo default set at company creation — in which case
            // the block must stay empty rather than show that generic mark.
            hasCompanyLogo: false,
        });

        onWillStart(async () => {
            if (!this.companyId) {
                return;
            }
            const [company] = await this.orm.read(
                "res.company",
                [this.companyId],
                ["uses_default_logo"]
            );
            this.state.hasCompanyLogo = Boolean(company && !company.uses_default_logo);
        });

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

    /**
     * Whether the active theme's `show_sidebar_logo` (issue #16) allows the
     * company logo header block to render. Anything other than exactly
     * `false` is treated as shown, matching `ssiShowAppsSidebar`
     * (navbar_patch.esm.js).
     *
     * @returns {Boolean}
     */
    get showLogo() {
        const backendTheme = session.backend_theme || {};
        return backendTheme.show_sidebar_logo !== false;
    }

    /**
     * Whether the active theme's `show_sidebar_recent` (issue #16) allows
     * the RECENT tab in the sidebar's footer panel. Passed down to
     * `SidebarFooter` (sidebar_footer.esm.js), which owns tab-level
     * rendering.
     *
     * @returns {Boolean}
     */
    get showRecentTab() {
        const backendTheme = session.backend_theme || {};
        return backendTheme.show_sidebar_recent !== false;
    }

    /**
     * Whether the active theme's `show_sidebar_bookmarks` (issue #16)
     * allows the BOOKMARKS tab in the sidebar's footer panel.
     *
     * @returns {Boolean}
     */
    get showBookmarksTab() {
        const backendTheme = session.backend_theme || {};
        return backendTheme.show_sidebar_bookmarks !== false;
    }

    /**
     * Whether the footer panel (`<SidebarFooter/>`, issue #13) should be
     * rendered at all: `false` only when BOTH `show_sidebar_recent` and
     * `show_sidebar_bookmarks` (issue #16) are `false`. Tab-level
     * visibility within an already-rendered footer is handled by
     * `SidebarFooter` itself (sidebar_footer.esm.js).
     *
     * @returns {Boolean}
     */
    get showFooter() {
        return this.showRecentTab || this.showBookmarksTab;
    }

    get apps() {
        return this.menuService.getApps();
    }

    /**
     * Whether the app list should render as titled category groups
     * (issue #18): only while the active theme's `group_apps_by_category`
     * is strictly `true` AND the sidebar is expanded — a group title does
     * not fit the collapsed (icon-only) width, so the list falls back to
     * the same flat rendering used before this feature existed
     * (Keputusan Desain, issue #18). Any other value on the session
     * payload (missing key, `false`, or anything non-boolean) is treated
     * as `false`, never raised as an error client-side.
     *
     * @returns {Boolean}
     */
    get isGroupedByCategory() {
        const backendTheme = session.backend_theme || {};
        return backendTheme.group_apps_by_category === true && !this.state.collapsed;
    }

    /**
     * Ordered app groups keyed by module category (issue #18): built from
     * the current app list (`this.apps`, order within a group unchanged)
     * and the `app_categories` map exposed via `session.backend_theme`
     * (server-side — see `backend_theme._get_app_module_categories()`,
     * models/backend_theme.py; Odoo 19's own `menuService` payload
     * carries no category info at all). Ordered by category `sequence`,
     * then category name ascending, with one trailing group ("Other")
     * for apps that have no resolvable category. A group with zero apps
     * is never produced, since a group only ever comes into existence
     * when the first app is pushed into it below.
     *
     * @returns {Array<{key: String, label: String, apps: Array}>}
     */
    get appGroups() {
        const backendTheme = session.backend_theme || {};
        const appCategories = backendTheme.app_categories || {};
        const OTHER_KEY = "__other__";
        const groupsByKey = new Map();
        for (const app of this.apps) {
            const category = appCategories[app.id];
            const hasCategory = Boolean(category && category.name);
            const key = hasCategory ? `category-${category.id}` : OTHER_KEY;
            if (!groupsByKey.has(key)) {
                groupsByKey.set(key, {
                    key,
                    label: hasCategory ? category.name : _t("Other"),
                    sequence: hasCategory
                        ? category.sequence || 0
                        : Number.MAX_SAFE_INTEGER,
                    name: hasCategory ? category.name : "",
                    apps: [],
                });
            }
            groupsByKey.get(key).apps.push(app);
        }
        const groups = [...groupsByKey.values()];
        groups.sort((a, b) => {
            if (a.key === OTHER_KEY || b.key === OTHER_KEY) {
                // "Other" always sorts last, regardless of sequence.
                return a.key === OTHER_KEY ? 1 : -1;
            }
            if (a.sequence !== b.sequence) {
                return a.sequence - b.sequence;
            }
            return a.name.localeCompare(b.name);
        });
        return groups;
    }

    /**
     * Flattened rows for the app `<ul>` (apps_sidebar.xml): one shape for
     * both the flat and the grouped rendering, so the template needs only
     * a single `t-foreach` instead of two branches with duplicated app
     * markup. A "title" row is only ever produced while `isGroupedByCategory`
     * is true.
     *
     * @returns {Array<{key: String, type: ("title"|"app"), label: String=, app: Object=}>}
     */
    get sidebarRows() {
        if (!this.isGroupedByCategory) {
            return this.apps.map((app) => ({key: `app-${app.id}`, type: "app", app}));
        }
        const rows = [];
        for (const group of this.appGroups) {
            rows.push({key: `title-${group.key}`, type: "title", label: group.label});
            for (const app of group.apps) {
                rows.push({key: `app-${app.id}`, type: "app", app});
            }
        }
        return rows;
    }

    get currentApp() {
        return this.menuService.getCurrentApp();
    }

    isCurrentApp(app) {
        return Boolean(this.currentApp) && this.currentApp.id === app.id;
    }

    /**
     * Flat list of the current app's own submenu sections (issue #17),
     * same source `web.NavBar` itself reads for the horizontal navbar
     * (`currentAppSections`, web/static/src/webclient/navbar/navbar.js) --
     * the existing `menuService`, never a bespoke menu RPC.
     *
     * @returns {Array}
     */
    get currentAppSections() {
        return (
            (this.currentApp &&
                this.menuService.getMenuAsTree(this.currentApp.id).childrenTree) ||
            []
        );
    }

    /**
     * Effective submenu position for THIS component: starts from the
     * active theme's resolved `app_submenu_position`
     * (`getEffectiveAppSubmenuPosition()`, already accounting for
     * `show_sidebar`), then additionally degrades "sidebar" to "popover"
     * while the sidebar is collapsed -- an inline list does not fit the
     * collapsed (icon-only) width, and a truncated list reads worse than
     * a popover (Keputusan Desain, issue #17).
     *
     * @returns {("navbar"|"sidebar"|"popover")}
     */
    get appSubmenuPosition() {
        const effective = getEffectiveAppSubmenuPosition();
        if (effective === "sidebar" && this.state.collapsed) {
            return "popover";
        }
        return effective;
    }

    /**
     * Whether the inline "submenu inside the sidebar" block should render
     * below the app list (issue #17): only in "sidebar" mode, and only
     * when the current app actually has sections.
     *
     * @returns {Boolean}
     */
    get showInlineSubmenu() {
        return (
            this.appSubmenuPosition === "sidebar" && this.currentAppSections.length > 0
        );
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

    get companyLogoUrl() {
        return `/web/image/res.company/${this.companyId}/logo`;
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

    /**
     * @param {Object} app
     * @param {MouseEvent} ev
     */
    onAppClick(app, ev) {
        // Issue #17: in "popover" mode, clicking the app that is ALREADY
        // active opens/closes its sections popover instead of re-selecting
        // it (which would just reload the same app). Any other app -- or
        // any other mode -- keeps the existing navigate-to-app behavior.
        if (
            this.appSubmenuPosition === "popover" &&
            this.isCurrentApp(app) &&
            this.currentAppSections.length
        ) {
            if (this.submenuPopover.isOpen) {
                this.submenuPopover.close();
            } else {
                this.submenuPopover.open(ev.currentTarget, {
                    sections: this.currentAppSections,
                });
            }
            return;
        }
        this.menuService.selectMenu(app);
    }

    /**
     * Handles a click on one entry of the inline "sidebar" submenu block
     * (apps_sidebar.xml). The popover's own equivalent lives in
     * app_submenu_popover.esm.js, since that component owns its own popover
     * lifecycle (`props.close()`).
     *
     * @param {Object} section
     */
    onSectionClick(section) {
        this.menuService.selectMenu(section);
    }
}
