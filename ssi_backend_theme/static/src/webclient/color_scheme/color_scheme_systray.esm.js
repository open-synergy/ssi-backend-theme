// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {Component, onWillStart, useState} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {browser} from "@web/core/browser/browser";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {user} from "@web/core/user";

/**
 * Systray toggle for the current user's own backend light/dark
 * preference (`res.users.backend_theme_color_scheme`).
 *
 * The current value isn't exposed anywhere on `session`/`user` (it
 * only ever feeds server-side `ir.http.color_scheme()` at page-render
 * time — see models/ir_http.py), so it is fetched once on mount via a
 * plain `read()`.
 *
 * `web.assets_web` and `web.assets_web_dark` are two separate,
 * pre-compiled bundles picked at render time (see
 * `web.webclient_bootstrap` in
 * addons/web/views/webclient_templates.xml) — there is no live way to
 * swap between them client-side, so a full page reload is required
 * right after the preference is saved.
 */
export class ColorSchemeSystrayItem extends Component {
    static template = "ssi_backend_theme.ColorSchemeSystrayItem";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.state = useState({scheme: "light"});
        onWillStart(async () => {
            const [record] = await this.orm.read(
                "res.users",
                [user.userId],
                ["backend_theme_color_scheme"]
            );
            this.state.scheme = record.backend_theme_color_scheme || "light";
        });
    }

    get isDark() {
        return this.state.scheme === "dark";
    }

    get label() {
        return this.isDark ? _t("Switch to light mode") : _t("Switch to dark mode");
    }

    async onClick() {
        const scheme = this.isDark ? "light" : "dark";
        await this.orm.write("res.users", [user.userId], {
            backend_theme_color_scheme: scheme,
        });
        browser.location.reload();
    }
}

export const colorSchemeSystrayItem = {Component: ColorSchemeSystrayItem};

registry
    .category("systray")
    .add("ssi_backend_theme.color_scheme", colorSchemeSystrayItem, {sequence: 20});
