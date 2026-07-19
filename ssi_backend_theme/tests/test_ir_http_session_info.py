# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged

from ..models.backend_theme import (
    CONFIG_PARAM_ACTIVE_THEME_ID,
    DEFAULT_COLOR_NAVBAR_BG,
    DEFAULT_COLOR_NAVBAR_TEXT,
    DEFAULT_COLOR_PRIMARY,
    DEFAULT_FONT_FAMILY,
)


@tagged("post_install", "-at_install")
class TestIrHttpSessionInfo(YamlTransactionCase):
    """Python murni — pemicu P1 (L-01/L-02).

    `session_info()` is a plain method on the abstract model `ir.http`
    (no backing table), so its returned dict cannot be populated onto
    any record and therefore cannot be reached by YAML `assert`
    (dotted-getattr on a registry record). Every case below is an
    assertion on that method's return value, not on a record's field
    state, so it does not qualify for the YAML DSL at all (`case.py`
    L-01/L-02: `action: call` discards return values and `assert`
    always targets a record in the registry).
    """

    def _set_active_theme_param(self, theme_id):
        self.env["ir.config_parameter"].sudo().set_param(
            CONFIG_PARAM_ACTIVE_THEME_ID, theme_id or ""
        )

    def test_session_info_active_theme(self):
        theme = self.env["backend_theme"].create(
            {
                "name": "Session Theme",
                "code": "IRH001",
                "color_primary": "#123456",
                "color_navbar_bg": "#654321",
                "color_navbar_text": "#abcdef",
                "font_family": "Roboto, sans-serif",
            }
        )
        self._set_active_theme_param(theme.id)

        backend_theme = self.env["ir.http"].session_info()["backend_theme"]

        self.assertEqual(backend_theme["id"], theme.id)
        self.assertEqual(backend_theme["color_primary"], "#123456")
        self.assertEqual(backend_theme["color_navbar_bg"], "#654321")
        self.assertEqual(backend_theme["color_navbar_text"], "#abcdef")
        self.assertEqual(backend_theme["font_family"], "Roboto, sans-serif")

    def test_session_info_no_theme_configured_uses_defaults(self):
        self._set_active_theme_param(None)

        backend_theme = self.env["ir.http"].session_info()["backend_theme"]

        self.assertFalse(backend_theme["id"])
        self.assertEqual(backend_theme["color_primary"], DEFAULT_COLOR_PRIMARY)
        self.assertEqual(
            backend_theme["color_navbar_bg"], DEFAULT_COLOR_NAVBAR_BG
        )
        self.assertEqual(
            backend_theme["color_navbar_text"], DEFAULT_COLOR_NAVBAR_TEXT
        )
        self.assertEqual(backend_theme["font_family"], DEFAULT_FONT_FAMILY)

    def test_session_info_deleted_theme_uses_defaults(self):
        theme = self.env["backend_theme"].create(
            {"name": "Deleted Theme", "code": "IRH002", "color_primary": "#ff0000"}
        )
        self._set_active_theme_param(theme.id)
        theme.unlink()

        backend_theme = self.env["ir.http"].session_info()["backend_theme"]

        self.assertFalse(backend_theme["id"])
        self.assertEqual(backend_theme["color_primary"], DEFAULT_COLOR_PRIMARY)

    def test_session_info_archived_theme_uses_defaults(self):
        theme = self.env["backend_theme"].create(
            {"name": "Archived Theme", "code": "IRH003", "color_primary": "#ff0000"}
        )
        self._set_active_theme_param(theme.id)
        theme.active = False

        backend_theme = self.env["ir.http"].session_info()["backend_theme"]

        self.assertFalse(backend_theme["id"])
        self.assertEqual(backend_theme["color_primary"], DEFAULT_COLOR_PRIMARY)
