// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {Component, onWillStart, useState} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {browser} from "@web/core/browser/browser";
import {session} from "@web/session";
import {useService} from "@web/core/utils/hooks";

// Persists which of the two tabs (RECENT / BOOKMARKS) is showing, per
// device -- same rationale as SIDEBAR_STATE_STORAGE_KEY (apps_sidebar.esm.js):
// a UI preference, not shared configuration.
export const SIDEBAR_FOOTER_TAB_STORAGE_KEY = "ssi_backend_theme.sidebar_footer_tab";
export const TAB_RECENT = "recent";
export const TAB_BOOKMARKS = "bookmarks";

/**
 * Resolve the initially-active tab.
 *
 * Any value other than exactly `TAB_BOOKMARKS` (missing key, corrupt
 * content, an old/unknown value) is treated as `TAB_RECENT` -- never
 * raises client-side.
 *
 * @returns {String}
 */
function getInitialTab() {
    const stored = browser.localStorage.getItem(SIDEBAR_FOOTER_TAB_STORAGE_KEY);
    return stored === TAB_BOOKMARKS ? TAB_BOOKMARKS : TAB_RECENT;
}

// The only shape this module ever writes to `action_url` / the
// recent-items list (see recent_items.esm.js). Parsed back here so a
// click can reopen the record through the `action` service (in-app
// navigation) instead of a full page reload; a bookmark whose URL
// doesn't match this shape (none, today, but the field is a plain Char)
// simply falls back to a normal browser navigation.
const RECORD_URL_RE = /^\/odoo\/([^/]+)\/(\d+)$/;

export class SidebarFooter extends Component {
    static template = "ssi_backend_theme.SidebarFooter";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.recentItemsService = useService("ssi_backend_theme.recent_items");
        this.recentItems = useState(this.recentItemsService.items);

        // Anything other than exactly `false` is treated as shown — same
        // rule as `showLogo`/`showFooter` (apps_sidebar.esm.js). The parent
        // already guarantees at least one of the two is true whenever this
        // component is even rendered (see `showFooter`), but each is still
        // resolved independently here so hiding one never affects the other.
        const backendTheme = session.backend_theme || {};
        this.showRecentTab = backendTheme.show_sidebar_recent !== false;
        this.showBookmarksTab = backendTheme.show_sidebar_bookmarks !== false;

        // The stored/default tab (issue #13) may point at a tab this
        // theme just turned off (issue #16); fall back to whichever
        // remaining tab is actually shown so a hidden tab's button is
        // never the only thing keeping its content pane selected.
        let initialTab = getInitialTab();
        if (initialTab === TAB_RECENT && !this.showRecentTab) {
            initialTab = TAB_BOOKMARKS;
        } else if (initialTab === TAB_BOOKMARKS && !this.showBookmarksTab) {
            initialTab = TAB_RECENT;
        }

        this.state = useState({
            activeTab: initialTab,
            bookmarks: [],
        });

        onWillStart(() => this.loadBookmarks());
    }

    async loadBookmarks() {
        // The record rule (security/ir_rule/backend_theme_bookmark.xml)
        // already restricts results to the current user's own bookmarks;
        // no extra domain needed here.
        this.state.bookmarks = await this.orm.searchRead(
            "backend_theme_bookmark",
            [],
            ["name", "action_url"]
        );
    }

    get isRecentTab() {
        return this.state.activeTab === TAB_RECENT;
    }

    get isBookmarksTab() {
        return this.state.activeTab === TAB_BOOKMARKS;
    }

    selectTab(tab) {
        this.state.activeTab = tab;
        browser.localStorage.setItem(SIDEBAR_FOOTER_TAB_STORAGE_KEY, tab);
    }

    get currentRecordEntry() {
        return this.recentItemsService.getCurrentRecordEntry();
    }

    get canBookmarkCurrentRecord() {
        return Boolean(this.currentRecordEntry);
    }

    get addBookmarkLabel() {
        return _t("Bookmark this record");
    }

    async addBookmark() {
        const entry = this.currentRecordEntry;
        if (!entry) {
            return;
        }
        await this.orm.create("backend_theme_bookmark", [
            {name: entry.name, action_url: entry.url},
        ]);
        await this.loadBookmarks();
    }

    async removeBookmark(bookmark) {
        await this.orm.unlink("backend_theme_bookmark", [bookmark.id]);
        await this.loadBookmarks();
    }

    openEntry(entry) {
        const match = RECORD_URL_RE.exec(entry.url);
        if (match) {
            const [, resModel, resId] = match;
            this.actionService.doAction({
                type: "ir.actions.act_window",
                res_model: resModel,
                res_id: Number(resId),
                views: [[false, "form"]],
                target: "current",
            });
            return;
        }
        browser.location.href = entry.url;
    }
}
