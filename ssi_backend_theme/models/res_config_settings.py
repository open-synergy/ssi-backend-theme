# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

from .backend_theme import CONFIG_PARAM_ACTIVE_THEME_ID


class ResConfigSettings(models.TransientModel):
    """Extends Settings with a pointer to the active backend theme.

    The field is intentionally non-stored: its value lives entirely in
    the `ssi_backend_theme.active_theme_id` system parameter, read and
    written through `get_values()`/`set_values()` so an active theme
    that gets deleted or archived is reported back as "no theme"
    instead of a dangling reference.
    """

    _inherit = "res.config.settings"

    backend_theme_active_id = fields.Many2one(
        comodel_name="backend_theme",
        string="Active Backend Theme",
        help="Backend theme preset applied to the backend UI. Takes "
        "effect for every user after the browser reloads. Leave empty "
        "to use the default look.",
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        theme = self.env["backend_theme"]._get_active_theme()
        res.update(backend_theme_active_id=theme.id)
        return res

    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            CONFIG_PARAM_ACTIVE_THEME_ID,
            self.backend_theme_active_id.id or "",
        )
