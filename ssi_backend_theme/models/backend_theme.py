# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

HEX_COLOR_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

COLOR_FIELD_NAMES = (
    "color_primary",
    "color_navbar_bg",
    "color_navbar_text",
)

# ir.config_parameter key holding the id of the active backend_theme
# record. Intentionally a single pointer (not a boolean `is_active` on
# the theme itself) so "which theme is active" can never become
# inconsistent/duplicated.
CONFIG_PARAM_ACTIVE_THEME_ID = "ssi_backend_theme.active_theme_id"

# Fallback values applied when there is no active theme (parameter
# unset, pointing to a deleted record, or pointing to an archived
# theme). Match Odoo's own defaults ($o-community-color / navbar entry
# color / system font stack) so the backend looks the same whether or
# not this module resolves an active theme.
DEFAULT_COLOR_PRIMARY = "#71639e"
DEFAULT_COLOR_NAVBAR_BG = "#71639e"
DEFAULT_COLOR_NAVBAR_TEXT = "#ffffff"
DEFAULT_FONT_FAMILY = "sans-serif"


class BackendTheme(models.Model):
    """Represents a reusable backend UI theme preset.

    Stores a preset's brand color palette and typography (name, code,
    colors, font) as master data, so a deployment can pick a preset
    without touching code. An administrator designates the active theme
    from Settings (see `res.config.settings`); its values are then
    exposed to the browser through `ir.http.session_info()` and applied
    as CSS custom properties by an OWL service.
    """

    _name = "backend_theme"
    _inherit = ["mixin.master_data"]
    _description = "Backend Theme"

    _show_code_on_display_name = True

    color_primary = fields.Char(
        string="Primary Color",
        help="Hex CSS color (#rgb or #rrggbb) used as the primary brand "
        "color of the backend. Leave empty to use the default color.",
    )
    color_navbar_bg = fields.Char(
        string="Navbar Background Color",
        help="Hex CSS color (#rgb or #rrggbb) used as the top navigation "
        "bar background color. Leave empty to use the default color.",
    )
    color_navbar_text = fields.Char(
        string="Navbar Text Color",
        help="Hex CSS color (#rgb or #rrggbb) used as the top navigation "
        "bar text color. Leave empty to use the default color.",
    )
    font_family = fields.Char(
        help="CSS font-family value applied to the backend UI. Leave "
        "empty to use the default font.",
    )
    font_size_base = fields.Char(
        string="Base Font Size",
        help="CSS base font-size value (e.g. '14px') applied to the "
        "backend UI. Leave empty to use the default size.",
    )
    sidebar_default = fields.Selection(
        string="Default Sidebar State",
        selection=[
            ("expanded", "Expanded"),
            ("collapsed", "Collapsed"),
        ],
        default="expanded",
        help="Default state of the navigation sidebar when this theme "
        "is applied. Not yet consumed by any feature in this module; "
        "reserved for a future sidebar navigation feature.",
    )
    color_scheme_default = fields.Selection(
        string="Default Color Scheme",
        selection=[
            ("light", "Light"),
            ("dark", "Dark"),
        ],
        default="light",
        help="Default light/dark color scheme when this theme is "
        "applied. Not yet consumed by any feature in this module; "
        "reserved for a future dark mode feature.",
    )

    @api.constrains("color_primary", "color_navbar_bg", "color_navbar_text")
    def _check_color_hex_format(self):
        for record in self.sudo():
            for field_name in COLOR_FIELD_NAMES:
                if not record._check_color_hex_format_condition(field_name):
                    error_message = f"""
                    Document Type: {record._description.lower()}
                    Context: Create or update document
                    Database ID: {record.id}
                    Problem: Invalid hex color value on field "{field_name}"
                    Solution: Use a valid CSS hex color (#rgb or #rrggbb),
                    or leave the field empty to use the default color
                    """
                    raise ValidationError(record.env._(error_message))

    def _check_color_hex_format_condition(self, field_name):
        self.ensure_one()
        value = getattr(self, field_name)
        if not value:
            return True
        return bool(HEX_COLOR_RE.match(value))

    @api.model
    def _get_active_theme(self):
        """Resolve the theme pointed to by the active-theme system parameter.

        Any inconsistency (parameter unset, pointing to a deleted
        record, or pointing to an archived theme) is treated as "no
        active theme" — returns an empty recordset instead of raising
        an error, so callers (Settings, ``session_info()``) can safely
        fall back to defaults.
        """
        icp = self.env["ir.config_parameter"].sudo()
        param_value = icp.get_param(CONFIG_PARAM_ACTIVE_THEME_ID)
        if not param_value:
            return self.browse()
        try:
            theme_id = int(param_value)
        except (TypeError, ValueError):
            return self.browse()
        # `browse()` never applies the active domain, so archived
        # themes are still reachable here; `exists()` only guards
        # against a deleted record id.
        theme = self.browse(theme_id).exists()
        if not theme or not theme.active:
            return self.browse()
        return theme

    @api.model
    def _get_backend_theme_session_values(self):
        """Build the ``backend_theme`` payload exposed via ``session_info()``.

        Always returns concrete values (never ``False``) so the
        browser-side service can apply them unconditionally: when there
        is no active theme, the module's own defaults are used instead.
        """
        theme = self._get_active_theme()
        return {
            "id": theme.id,
            "name": theme.name if theme else False,
            "color_primary": theme.color_primary or DEFAULT_COLOR_PRIMARY,
            "color_navbar_bg": theme.color_navbar_bg or DEFAULT_COLOR_NAVBAR_BG,
            "color_navbar_text": theme.color_navbar_text or DEFAULT_COLOR_NAVBAR_TEXT,
            "font_family": theme.font_family or DEFAULT_FONT_FAMILY,
        }
