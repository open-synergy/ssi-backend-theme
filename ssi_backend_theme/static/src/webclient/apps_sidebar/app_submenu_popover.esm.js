// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {Component} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

/**
 * Popover content (issue #17) listing the active app's submenu sections,
 * opened by `AppsSidebar.onAppClick()` (apps_sidebar.esm.js) via
 * `usePopover()` -- the existing Odoo 19 popover service, never a bespoke
 * positioning/closing implementation. `close` is injected automatically by
 * `web.Popover` (see `props.close` on `t-component` in
 * addons/web/static/src/core/popover/popover.xml); `sections` is the only
 * prop this module itself passes through `usePopover(...).open()`.
 */
export class AppSubmenuPopover extends Component {
    static template = "ssi_backend_theme.AppSubmenuPopover";
    static props = {
        close: Function,
        sections: Array,
    };

    setup() {
        this.menuService = useService("menu");
    }

    /**
     * @param {Object} section
     */
    onSectionClick(section) {
        this.menuService.selectMenu(section);
        this.props.close();
    }
}
