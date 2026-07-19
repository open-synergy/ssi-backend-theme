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


class BackendTheme(models.Model):
    """Represents a reusable backend UI theme preset.

    Stores a preset's brand color palette and typography (name, code,
    colors, font) as master data, so a deployment can pick a preset
    without touching code. This model only manages the presets
    themselves; designating which preset is active and applying it to
    the browser is out of scope and handled by a separate module.
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
