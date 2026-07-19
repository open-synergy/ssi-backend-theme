# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
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
# Matches the `sidebar_default` field's own default ("expanded"), applied
# whenever there is no active theme. Any value that is not exactly
# "collapsed" (this default included) is treated as "expanded" by the
# browser-side sidebar component as well — never an error client-side.
DEFAULT_SIDEBAR_STATE = "expanded"

# $o-brand-odoo/$o-brand-primary cannot be bridged through a CSS custom
# property like the rest of the active theme's values: Odoo core and
# Bootstrap 5 both feed them through Sass color functions (darken() in
# web/static/src/webclient/navbar/navbar.variables.scss and
# web/static/src/scss/primary_variables.scss, plus Bootstrap 5's own
# tint-color()/shade-color() subtle-color system), which require a real
# Sass color operand and reject a `var()` reference outright — verified
# by an actual asset-compile failure across every backend/frontend
# bundle. So these two are instead applied by regenerating our own small
# SCSS file (never a core file) with the active theme's literal colors,
# using `ir.asset`'s `replace` directive whenever the active theme
# changes — the same ORM-native mechanism Odoo 19 core itself uses for
# `website`'s dynamic Theme Colors (see
# addons/website/models/assets.py: WebsiteAssets.save_asset()/
# make_scss_customization()).
SCSS_ASSET_BUNDLE = "web._assets_primary_variables"
SCSS_ASSET_TARGET_PATH = (
    "ssi_backend_theme/static/src/scss/backend_theme_primary_variables.scss"
)
SCSS_ASSET_CUSTOM_URL = (
    "/ssi_backend_theme/dynamic/backend_theme_primary_variables.scss"
)


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
            "sidebar_default": theme.sidebar_default or DEFAULT_SIDEBAR_STATE,
        }

    @api.model
    def _get_active_theme_primary_variables_scss(self):
        """Render the $o-brand-odoo/$o-brand-primary override as SCSS text.

        Always produces valid, literal Sass colors (never ``var()``) —
        see the module-level comment above ``SCSS_ASSET_BUNDLE`` for why.
        """
        values = self._get_backend_theme_session_values()
        return (
            "// Auto-generated by ssi_backend_theme. Do not edit "
            "manually — regenerated by\n"
            "// backend_theme._sync_active_theme_scss_asset() whenever "
            "the active theme changes.\n"
            f"$o-brand-odoo: {values['color_navbar_bg']} !default;\n"
            f"$o-brand-primary: {values['color_primary']} !default;\n"
        )

    @api.model
    def _sync_active_theme_scss_asset(self):
        """Regenerate the compiled-in brand color override, if needed.

        Creates/updates one ``ir.attachment`` (holding the generated
        SCSS text from `_get_active_theme_primary_variables_scss()`) and
        one ``ir.asset`` record (``directive='replace'``) that swaps our
        own static default SCSS file for that attachment inside
        ``web._assets_primary_variables``. Both records are pure,
        disposable cache: the source of truth stays the `backend_theme`
        record and the active-theme system parameter, so if this pair is
        ever lost (e.g. across an upgrade) the next theme change simply
        regenerates it identically — unlike a customization whose only
        copy lives in the attachment itself.
        """
        content = self._get_active_theme_primary_variables_scss()
        datas = base64.b64encode(content.encode("utf-8"))

        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .search([("url", "=", SCSS_ASSET_CUSTOM_URL)], limit=1)
        )
        if attachment:
            attachment.write({"datas": datas})
            # Mirror website.assets's own WebsiteAssets.save_asset(): a
            # write() on ir.attachment alone does not clear the 'assets'
            # ormcache, only ir.asset create/write/unlink does.
            self.env.registry.clear_cache("assets")
        else:
            self.env["ir.attachment"].sudo().create(
                {
                    "name": SCSS_ASSET_CUSTOM_URL.rsplit("/", 1)[-1],
                    "type": "binary",
                    "mimetype": "text/scss",
                    "datas": datas,
                    "url": SCSS_ASSET_CUSTOM_URL,
                }
            )

        asset = (
            self.env["ir.asset"]
            .sudo()
            .search(
                [
                    ("bundle", "=", SCSS_ASSET_BUNDLE),
                    ("target", "=", SCSS_ASSET_TARGET_PATH),
                    ("directive", "=", "replace"),
                ],
                limit=1,
            )
        )
        if not asset:
            self.env["ir.asset"].sudo().create(
                {
                    "name": "ssi_backend_theme: active theme brand colors",
                    "bundle": SCSS_ASSET_BUNDLE,
                    "directive": "replace",
                    "target": SCSS_ASSET_TARGET_PATH,
                    "path": SCSS_ASSET_CUSTOM_URL,
                }
            )

    @api.model
    def _get_raw_active_theme_id(self):
        """Read the active-theme system parameter as a plain int, if set.

        Unlike `_get_active_theme()`, this does NOT check `exists()`/
        `active` — it is used by `write()`/`unlink()` to detect whether
        a record being touched IS the configured pointer, regardless of
        whether the change just archived it or it is about to be
        deleted (in both of which cases `_get_active_theme()` would
        already (correctly) resolve to nothing, which is precisely the
        transition that needs to trigger a resync).
        """
        param_value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(CONFIG_PARAM_ACTIVE_THEME_ID)
        )
        try:
            return int(param_value) if param_value else False
        except (TypeError, ValueError):
            return False

    def write(self, vals):
        affected_ids = set(self.ids)
        result = super().write(vals)
        relevant_fields = {"color_primary", "color_navbar_bg", "active"}
        active_theme_id = self._get_raw_active_theme_id()
        if (
            relevant_fields.intersection(vals)
            and active_theme_id
            and active_theme_id in affected_ids
        ):
            self.env["backend_theme"]._sync_active_theme_scss_asset()
        return result

    def unlink(self):
        affected_ids = set(self.ids)
        active_theme_id = self._get_raw_active_theme_id()
        result = super().unlink()
        if active_theme_id and active_theme_id in affected_ids:
            self.env["backend_theme"]._sync_active_theme_scss_asset()
        return result
