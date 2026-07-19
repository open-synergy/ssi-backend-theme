# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ResUsers(models.Model):
    """Adds a personal backend light/dark color scheme preference.

    Light vs. dark is an eye-comfort choice for a single person, not a
    company-wide visual identity, so it is stored per user here rather
    than on `backend_theme` (the shared preset) — a deliberate
    deviation from that model's usual "configure once, applies to
    everyone" scope. The field's *initial* value only (never a forced
    override) comes from the active theme's `color_scheme_default`;
    once a user has their own value, it always wins. See
    `ir.http.color_scheme()` (models/ir_http.py) for how this field
    ends up selecting which asset bundle (`web.assets_web` /
    `web.assets_web_dark`) the backend loads.
    """

    _inherit = "res.users"

    backend_theme_color_scheme = fields.Selection(
        selection=[("light", "Light"), ("dark", "Dark")],
        string="Backend Color Scheme",
        store=True,
        default=lambda self: self._default_backend_theme_color_scheme(),
        help="Light or dark color scheme applied to your own backend "
        "UI. Takes effect after the browser reloads. Leave empty to "
        "use the active backend theme's default.",
    )

    @api.model
    def _default_backend_theme_color_scheme(self):
        theme = self.env["backend_theme"]._get_active_theme()
        return theme.color_scheme_default or "light"

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ["backend_theme_color_scheme"]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ["backend_theme_color_scheme"]
