# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

HEX_COLOR_RE = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

# A bare "0" (unitless, valid CSS for a zero length) or a number
# followed by one of the CSS units this module supports.
CSS_LENGTH_RE = re.compile(r"^(0|[0-9]+(\.[0-9]+)?(px|rem|em|%))$")

COLOR_FIELD_NAMES = (
    "color_primary",
    "color_navbar_bg",
    "color_navbar_text",
    "color_text_body",
    "color_view_background",
    "color_success",
    "color_info",
    "color_warning",
    "color_danger",
    "color_list_header_bg",
    "color_list_row_hover_bg",
)

# These are sizing/spacing fields, NOT colors: validated by
# `CSS_LENGTH_RE`, never by `HEX_COLOR_RE`, and deliberately excluded
# from `COLOR_FIELD_NAMES` above so the hex-format constraint never
# runs against them.
NAVBAR_SPACING_FIELD_NAMES = (
    "navbar_height",
    "navbar_font_size",
    "navbar_entry_padding_h",
    "navbar_entry_margin_h",
    "navbar_entry_border_radius",
    "paragraph_spacing",
    "form_spacing",
)

# Maps each navbar/spacing field to the Odoo 19 Sass variable it
# overrides, verified directly against core source:
# - $o-navbar-height / $o-navbar-font-size / $o-navbar-entry-padding-h /
#   $o-navbar-entry-margin-h / $o-navbar-entry-border-radius:
#   web/static/src/webclient/navbar/navbar.variables.scss
# - $o-form-spacing-unit: web/static/src/scss/primary_variables.scss
# - $paragraph-margin-bottom: web/static/lib/bootstrap/scss/_variables.scss
#   (Bootstrap's own variable — still safe to override here: it is
#   loaded, via 'web._assets_bootstrap_backend'/plain bundle entries,
#   AFTER 'web._assets_primary_variables' — the bundle this module
#   prepends its regenerated file into — inside `web.assets_backend`,
#   so our `!default` assignment still wins the same way
#   $o-brand-odoo/$o-brand-primary already do).
NAVBAR_SPACING_SCSS_VARIABLES = {
    "navbar_height": "$o-navbar-height",
    "navbar_font_size": "$o-navbar-font-size",
    "navbar_entry_padding_h": "$o-navbar-entry-padding-h",
    "navbar_entry_margin_h": "$o-navbar-entry-margin-h",
    "navbar_entry_border_radius": "$o-navbar-entry-border-radius",
    "paragraph_spacing": "$paragraph-margin-bottom",
    "form_spacing": "$o-form-spacing-unit",
}

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
# Matches $o-main-text-color ($o-gray-900), $o-view-background-color
# (white), and $o-success/$o-info/$o-warning/$o-danger — all verified
# against web/static/src/scss/primary_variables.scss in Odoo 19 core.
# None of these depend on any other themed value, so — unlike the list
# view colors below — they are safe to always resolve to a fixed
# fallback constant, exactly like color_primary/color_navbar_bg above.
DEFAULT_COLOR_TEXT_BODY = "#212529"
DEFAULT_COLOR_VIEW_BACKGROUND = "#ffffff"
DEFAULT_COLOR_SUCCESS = "#28a745"
DEFAULT_COLOR_INFO = "#17a2b8"
DEFAULT_COLOR_WARNING = "#ffac00"
DEFAULT_COLOR_DANGER = "#dc3545"
DEFAULT_FONT_FAMILY = "sans-serif"
# Matches the `sidebar_default` field's own default ("expanded"), applied
# whenever there is no active theme. Any value that is not exactly
# "collapsed" (this default included) is treated as "expanded" by the
# browser-side sidebar component as well — never an error client-side.
DEFAULT_SIDEBAR_STATE = "expanded"

# Matches the `app_submenu_position` field's own default ("navbar"),
# applied whenever there is no active theme. Any value other than exactly
# "sidebar" or "popover" (missing, unset, or any future/unexpected
# selection value included) is treated as "navbar" by the browser-side
# components as well — never an error client-side (issue #17).
DEFAULT_APP_SUBMENU_POSITION = "navbar"

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

# color_text_body/color_view_background/color_success/color_info/
# color_warning/color_danger map onto real Sass variables
# ($o-main-text-color, $o-view-background-color, $o-success, $o-info,
# $o-warning, $o-danger — all verified in Odoo 19's own
# primary_variables.scss/bootstrap_overridden.scss), so they are baked
# into the same regenerated SCSS file as color_primary/color_navbar_bg
# above (see `_get_active_theme_primary_variables_scss()`).
#
# color_list_header_bg/color_list_row_hover_bg have NO equivalent Sass
# variable in core — the list renderer only exposes CSS custom
# properties (web/static/src/views/list/list_renderer.scss:
# --ListRenderer-thead-bg-color; no core property exists at all for
# row hover, so static/src/scss/backend_theme_list_view.scss defines
# its own --ListRenderer-data-row-hover-bg). Both are therefore applied
# the same way as color_navbar_text/font_family: the OWL service
# (static/src/js/backend_theme_service.esm.js) sets a `--ssi-list-*`
# bridge custom property on the document root only when the field has
# a value, and that SCSS file reads it with a `var(..., <default>)`
# fallback — never a literal assignment on `:root`, since core's own
# `.o_list_renderer { --ListRenderer-thead-bg-color: ...; }` rule would
# otherwise always shadow a `:root`-level value regardless of
# specificity (a rule that directly targets a descendant element
# always wins over an inherited ancestor value). Crucially, leaving
# color_list_row_hover_bg empty must keep following the *current*
# Primary Color dynamically (`rgba($primary, 0.06)`, itself already
# theme-aware) rather than a fixed constant, which is why — unlike
# every other color field above — these two are never resolved with an
# "or DEFAULT_..." fallback in `_get_backend_theme_session_values()`.


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
    color_text_body = fields.Char(
        string="Body Text Color",
        help="Hex CSS color (#rgb or #rrggbb) used as the main text "
        "color across the backend UI. Leave empty to use the default "
        "color.",
    )
    color_view_background = fields.Char(
        string="View Background Color",
        help="Hex CSS color (#rgb or #rrggbb) used as the background "
        "color of the backend content area (forms, cards, dialogs). "
        "Leave empty to use the default color.",
    )
    color_success = fields.Char(
        string="Success Color",
        help="Hex CSS color (#rgb or #rrggbb) used for success badges, "
        "alerts, and decorations. Leave empty to use the default color.",
    )
    color_info = fields.Char(
        string="Info Color",
        help="Hex CSS color (#rgb or #rrggbb) used for info badges, "
        "alerts, and decorations. Leave empty to use the default color.",
    )
    color_warning = fields.Char(
        string="Warning Color",
        help="Hex CSS color (#rgb or #rrggbb) used for warning badges, "
        "alerts, and decorations. Leave empty to use the default color.",
    )
    color_danger = fields.Char(
        string="Danger Color",
        help="Hex CSS color (#rgb or #rrggbb) used for danger badges, "
        "alerts, and decorations. Leave empty to use the default color.",
    )
    color_list_header_bg = fields.Char(
        string="List Header Background Color",
        help="Hex CSS color (#rgb or #rrggbb) used as the background "
        "color of a list view's header row. Leave empty to use the "
        "default color.",
    )
    color_list_row_hover_bg = fields.Char(
        string="List Row Hover Background Color",
        help="Hex CSS color (#rgb or #rrggbb) used as the background "
        "color of a list view's data row when hovered. Leave empty to "
        "use the default color, which follows the Primary Color.",
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
    navbar_height = fields.Char(
        help="CSS length (px, rem, em, %, or a bare 0) for the top "
        'navigation bar height. Matches Odoo\'s own default of "46px". '
        "Leave empty to use the default height.",
    )
    navbar_font_size = fields.Char(
        help="CSS length (px, rem, em, %, or a bare 0) for the top "
        "navigation bar font size. Matches Odoo's own default of "
        '"1rem". Leave empty to use the default size.',
    )
    navbar_entry_padding_h = fields.Char(
        string="Navbar Entry Horizontal Padding",
        help="CSS length (px, rem, em, %, or a bare 0) for the "
        "horizontal padding of each navbar entry. Matches Odoo's own "
        'default of "0.63em". Leave empty to use the default padding.',
    )
    navbar_entry_margin_h = fields.Char(
        string="Navbar Entry Horizontal Margin",
        help="CSS length (px, rem, em, %, or a bare 0) for the "
        "horizontal margin of each navbar entry. Matches Odoo's own "
        'default of "0". Leave empty to use the default margin.',
    )
    navbar_entry_border_radius = fields.Char(
        help="CSS length (px, rem, em, %, or a bare 0) for the corner "
        "radius of each navbar entry. Matches Odoo's own default of "
        '"0". Leave empty to use the default radius.',
    )
    paragraph_spacing = fields.Char(
        help="CSS length (px, rem, em, %, or a bare 0) for the space "
        "below a paragraph of backend text. Leave empty to use the "
        "default spacing.",
    )
    form_spacing = fields.Char(
        help="CSS length (px, rem, em, %, or a bare 0) for the "
        "density between fields on a form view. Leave empty to use "
        "the default spacing.",
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
    app_submenu_position = fields.Selection(
        selection=[
            ("navbar", "Navbar"),
            ("sidebar", "Sidebar"),
            ("popover", "Popover"),
        ],
        default="navbar",
        help="Where the active app's submenu sections are shown: on the "
        "top horizontal navbar (Odoo's default), inline inside the "
        "sidebar under the active app, or as a popover on the active "
        "app's sidebar item. Sidebar and Popover both fall back to "
        "Navbar while the sidebar itself is hidden (see Show Sidebar "
        "below), and Sidebar behaves like Popover while the sidebar is "
        "collapsed.",
    )
    show_sidebar = fields.Boolean(
        default=True,
        help="Uncheck to hide the entire navigation sidebar and shift "
        "the backend back to Odoo's default layout, with no space left "
        "on the left side. The fields below are ignored while this is "
        "unchecked.",
    )
    show_sidebar_logo = fields.Boolean(
        default=True,
        help="Uncheck to hide the company logo header at the top of the sidebar.",
    )
    show_sidebar_recent = fields.Boolean(
        default=True,
        help="Uncheck to hide the RECENT tab from the sidebar's footer panel.",
    )
    show_sidebar_bookmarks = fields.Boolean(
        default=True,
        help="Uncheck to hide the BOOKMARKS tab from the sidebar's footer panel.",
    )
    group_apps_by_category = fields.Boolean(
        string="Group Apps by Category",
        default=False,
        help="Split the sidebar's app list into titled sections by each "
        "app's module category, instead of one flat list. Apps with no "
        'resolvable category are grouped under "Other". Leave unchecked '
        "to keep the current flat list.",
    )

    @api.constrains(*COLOR_FIELD_NAMES)
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

    @api.constrains(*NAVBAR_SPACING_FIELD_NAMES)
    def _check_css_length_format(self):
        for record in self.sudo():
            for field_name in NAVBAR_SPACING_FIELD_NAMES:
                if not record._check_css_length_format_condition(field_name):
                    error_message = f"""
                    Document Type: {record._description.lower()}
                    Context: Create or update document
                    Database ID: {record.id}
                    Problem: Invalid CSS length value on field "{field_name}"
                    Solution: Use a valid CSS length (a number followed by
                    px/rem/em/%, or a bare 0), or leave the field empty to
                    use the default value
                    """
                    raise ValidationError(record.env._(error_message))

    def _check_css_length_format_condition(self, field_name):
        self.ensure_one()
        value = getattr(self, field_name)
        if not value:
            return True
        return bool(CSS_LENGTH_RE.match(value))

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
    def _get_app_module_categories(self):
        """Map each app's ``ir.ui.menu`` id to its owning module's category.

        Odoo 19's own client-side ``menuService`` payload
        (``load_web_menus()``, ``addons/web/models/ir_ui_menu.py``, and
        ``computeAppsAndMenuItems()``,
        ``addons/web/static/src/webclient/menus/menu_helpers.js``)
        carries no category/category_id key at all — verified directly
        against that source before writing this method (issue #18). So
        the mapping is resolved here instead, server-side: for each
        top-level (``parent_id`` false) menu, the defining module is
        read off its own ``ir.model.data`` xmlid (``module.name``, via
        the core ``_get_menuitems_xmlids()`` helper), then that
        module's ``category_id`` is looked up on ``ir.module.module``.

        Returns ``{menu_id: {"id": int, "name": str, "sequence": int}}``
        for every app that resolves to a category; an app with no
        xmlid, no matching module, or a module with no category is
        simply absent from the result — callers treat a missing key the
        same as "no category" (grouped under "Other"). Deliberately has
        no early-return guard for an empty intermediate step (no apps /
        no module names / no categorized module): each of those states
        degrades to `{}` on its own through the same code path below —
        an empty `search_read([("...", "in", [])])` domain simply
        returns no rows — without a separate branch to test.
        """
        apps = self.env["ir.ui.menu"].sudo().search([("parent_id", "=", False)])
        # `complete_name` (`ir.model.data`, core) is always `"<module>.<name>"`
        # for every entry `_get_menuitems_xmlids()` returns — `partition()`
        # never raises even on an unexpected empty string, and an app that
        # somehow yields an empty module name simply fails to match any
        # module below (falls through to "no category", same as any other
        # app absent from the result).
        module_name_by_app_id = {
            app_id: xmlid.partition(".")[0]
            for app_id, xmlid in apps._get_menuitems_xmlids().items()
        }
        module_names = set(module_name_by_app_id.values())

        category_id_by_module = {}
        for module in (
            self.env["ir.module.module"]
            .sudo()
            .search_read(
                [("name", "in", list(module_names))],
                ["name", "category_id"],
            )
        ):
            if module["category_id"]:
                category_id_by_module[module["name"]] = module["category_id"][0]

        category_info_by_id = {
            category["id"]: {
                "id": category["id"],
                "name": category["name"],
                "sequence": category["sequence"],
            }
            for category in self.env["ir.module.category"]
            .sudo()
            .search_read(
                [("id", "in", list(set(category_id_by_module.values())))],
                ["name", "sequence"],
            )
        }

        result = {}
        for app_id, module_name in module_name_by_app_id.items():
            category_id = category_id_by_module.get(module_name)
            category = category_id and category_info_by_id.get(category_id)
            if category:
                result[app_id] = category
        return result

    @api.model
    def _get_backend_theme_session_values(self):
        """Build the ``backend_theme`` payload exposed via ``session_info()``.

        Always returns concrete values (never ``False``) so the
        browser-side service can apply them unconditionally: when there
        is no active theme, the module's own defaults are used instead.
        """
        theme = self._get_active_theme()
        group_apps_by_category = theme.group_apps_by_category if theme else False
        return {
            "id": theme.id,
            "name": theme.name if theme else False,
            "color_primary": theme.color_primary or DEFAULT_COLOR_PRIMARY,
            "color_navbar_bg": theme.color_navbar_bg or DEFAULT_COLOR_NAVBAR_BG,
            "color_navbar_text": theme.color_navbar_text or DEFAULT_COLOR_NAVBAR_TEXT,
            "color_text_body": theme.color_text_body or DEFAULT_COLOR_TEXT_BODY,
            "color_view_background": (
                theme.color_view_background or DEFAULT_COLOR_VIEW_BACKGROUND
            ),
            "color_success": theme.color_success or DEFAULT_COLOR_SUCCESS,
            "color_info": theme.color_info or DEFAULT_COLOR_INFO,
            "color_warning": theme.color_warning or DEFAULT_COLOR_WARNING,
            "color_danger": theme.color_danger or DEFAULT_COLOR_DANGER,
            # Intentionally NOT resolved with an "or DEFAULT_..." fallback
            # — see the comment above `SCSS_ASSET_CUSTOM_URL` for why.
            "color_list_header_bg": theme.color_list_header_bg or False,
            "color_list_row_hover_bg": theme.color_list_row_hover_bg or False,
            "font_family": theme.font_family or DEFAULT_FONT_FAMILY,
            "sidebar_default": theme.sidebar_default or DEFAULT_SIDEBAR_STATE,
            "app_submenu_position": (
                theme.app_submenu_position or DEFAULT_APP_SUBMENU_POSITION
            ),
            # Boolean fields default to `False` on an empty recordset, so
            # unlike every field above, an `or DEFAULT` fallback would
            # silently turn an intentional `False` on a real theme into
            # `True`. Checking `theme` first is what actually implements
            # "no active theme / field missing -> True" (issue #16).
            "show_sidebar": theme.show_sidebar if theme else True,
            "show_sidebar_logo": theme.show_sidebar_logo if theme else True,
            "show_sidebar_recent": theme.show_sidebar_recent if theme else True,
            "show_sidebar_bookmarks": (theme.show_sidebar_bookmarks if theme else True),
            "group_apps_by_category": group_apps_by_category,
            # Only resolved when actually needed (issue #18): with the
            # toggle off — the default, and the common case — this skips
            # the extra ir.module.module/ir.module.category queries on
            # every session_info() call. A theme change always forces a
            # fresh page load, so there is no stale-payload risk from
            # gating it behind the (already-resolved) toggle value above.
            "app_categories": (
                self._get_app_module_categories() if group_apps_by_category else {}
            ),
        }

    @api.model
    def _get_active_theme_primary_variables_scss(self):
        """Render the $o-brand-odoo/$o-brand-primary override as SCSS text.

        Always produces valid, literal Sass colors (never ``var()``) —
        see the module-level comment above ``SCSS_ASSET_BUNDLE`` for why.

        Navbar/spacing fields (``NAVBAR_SPACING_FIELD_NAMES``) are
        appended below with the opposite fallback rule from the color
        fields above: a blank field is skipped entirely — never
        resolved with a Python fallback constant — so core's own
        ``!default`` declaration (navbar.variables.scss/
        primary_variables.scss/Bootstrap's ``_variables.scss``) applies
        exactly as if this module were not installed.
        """
        theme = self._get_active_theme()
        values = self._get_backend_theme_session_values()
        content = (
            "// Auto-generated by ssi_backend_theme. Do not edit "
            "manually — regenerated by\n"
            "// backend_theme._sync_active_theme_scss_asset() whenever "
            "the active theme changes.\n"
            f"$o-brand-odoo: {values['color_navbar_bg']} !default;\n"
            f"$o-brand-primary: {values['color_primary']} !default;\n"
            f"$o-main-text-color: {values['color_text_body']} !default;\n"
            f"$o-view-background-color: "
            f"{values['color_view_background']} !default;\n"
            f"$o-success: {values['color_success']} !default;\n"
            f"$o-info: {values['color_info']} !default;\n"
            f"$o-warning: {values['color_warning']} !default;\n"
            f"$o-danger: {values['color_danger']} !default;\n"
        )
        for field_name, scss_variable in NAVBAR_SPACING_SCSS_VARIABLES.items():
            value = theme[field_name]
            if value:
                content += f"{scss_variable}: {value} !default;\n"
        return content

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
        # Every color field introduced by this module is included here,
        # regardless of whether it feeds the regenerated SCSS file
        # directly (color_text_body, color_view_background,
        # color_success/info/warning/danger) or the list view's
        # `--ssi-list-*` bridge custom properties (color_list_header_bg,
        # color_list_row_hover_bg) — an unlisted field would be stored
        # but silently never applied. `color_navbar_text` and
        # `font_family` are the only color/typography fields excluded:
        # they are read fresh from `session_info()` on every
        # session/page load instead of being baked into a compiled
        # asset, so no resync is needed for them. All seven
        # `NAVBAR_SPACING_FIELD_NAMES` fields (issue #15) also feed the
        # same regenerated SCSS file, so they are unioned in below —
        # an unlisted one here would be stored but never applied either.
        relevant_fields = {
            "color_primary",
            "color_navbar_bg",
            "color_text_body",
            "color_view_background",
            "color_success",
            "color_info",
            "color_warning",
            "color_danger",
            "color_list_header_bg",
            "color_list_row_hover_bg",
            "active",
        } | set(NAVBAR_SPACING_FIELD_NAMES)
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
