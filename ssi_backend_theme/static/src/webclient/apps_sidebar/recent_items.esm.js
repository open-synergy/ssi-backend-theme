// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {reactive} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {browser} from "@web/core/browser/browser";

// Per-device history of recently opened records (issue #13). Deliberately
// NOT backed by a model -- writing a table row on every single navigation
// would be wasteful, and this is a per-device preference anyway. Mirrors
// SIDEBAR_STATE_STORAGE_KEY (apps_sidebar.esm.js) in that respect.
export const RECENT_ITEMS_STORAGE_KEY = "ssi_backend_theme.recent_items";
export const RECENT_ITEMS_LIMIT = 15;

function isValidEntry(entry) {
    return Boolean(
        entry &&
            typeof entry.name === "string" &&
            entry.name &&
            typeof entry.url === "string" &&
            entry.url
    );
}

/**
 * Read the persisted recent-items list.
 *
 * Any corrupt/unexpected `localStorage` content (missing key, invalid
 * JSON, not an array, malformed entries) is treated as an empty list and
 * never raises client-side.
 *
 * @returns {Array<{name: string, url: string}>}
 */
function readStoredItems() {
    const raw = browser.localStorage.getItem(RECENT_ITEMS_STORAGE_KEY);
    if (!raw) {
        return [];
    }
    try {
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed) ? parsed.filter(isValidEntry) : [];
    } catch {
        return [];
    }
}

function writeStoredItems(items) {
    browser.localStorage.setItem(RECENT_ITEMS_STORAGE_KEY, JSON.stringify(items));
}

/**
 * Build the `{name, url}` entry for the record the given `action` service
 * controller currently displays, or `undefined` when the controller isn't
 * showing a single saved record (list/kanban view, an unsaved "new"
 * record, a client action, ...).
 *
 * `/odoo/<resModel>/<resId>` mirrors the exact link shape core already
 * uses for internal Many2one links (see `linkHref` in
 * web/static/src/views/fields/many2one/many2one.js), so both this
 * module's own click handling (sidebar_footer.esm.js) and a plain
 * middle-click/new-tab open resolve the same way.
 *
 * @param {object} controller `action` service's `currentController`
 * @returns {{name: string, url: string}|undefined}
 */
export function getControllerRecordEntry(controller) {
    if (!controller || !controller.props || controller.props.type !== "form") {
        return undefined;
    }
    const resId = controller.currentState && controller.currentState.resId;
    const resModel = controller.props.resModel;
    if (!resId || resId === "new" || !resModel) {
        return undefined;
    }
    const url = `/odoo/${resModel}/${resId}`;
    return {name: controller.displayName || url, url};
}

export const recentItemsService = {
    dependencies: ["action"],
    start(env, {action}) {
        // A single reactive array, shared by every component that reads
        // it through `useState()` -- the standard Odoo pattern for
        // service-owned state (e.g. the `menu` service's app list).
        const items = reactive(readStoredItems());

        function recordCurrentController() {
            const entry = getControllerRecordEntry(action.currentController);
            if (!entry) {
                return;
            }
            const next = [entry, ...items.filter((item) => item.url !== entry.url)].slice(
                0,
                RECENT_ITEMS_LIMIT
            );
            items.splice(0, items.length, ...next);
            writeStoredItems(items);
        }

        env.bus.addEventListener("ACTION_MANAGER:UI-UPDATED", recordCurrentController);

        return {
            items,
            getCurrentRecordEntry: () => getControllerRecordEntry(action.currentController),
        };
    },
};

registry.category("services").add("ssi_backend_theme.recent_items", recentItemsService);
