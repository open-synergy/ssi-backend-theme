# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import HttpCase, tagged

from ..models.backend_theme import (
    CONFIG_PARAM_ACTIVE_THEME_ID,
    DEFAULT_APP_SUBMENU_POSITION,
    DEFAULT_COLOR_NAVBAR_BG,
    DEFAULT_COLOR_NAVBAR_TEXT,
    DEFAULT_COLOR_PRIMARY,
    DEFAULT_FONT_FAMILY,
    DEFAULT_SIDEBAR_STATE,
)


@tagged("post_install", "-at_install")
class TestControllerSessionInfo(HttpCase):
    """Python murni — pemicu P7 (L-19: base class terkunci `TransactionCase`).

    `ir.http.session_info()` reads `request.session`/`request.httprequest`
    (see `addons/web/models/ir_http.py`), which is only bound during a
    real HTTP request. Calling it from a plain `TransactionCase` (which
    `YamlTransactionCase`/YAML scenarios are built on) raises
    `RuntimeError: object unbound`, so this can only be tested through
    an actual HTTP round-trip via `HttpCase`, hitting the core route
    `/web/session/get_session_info` (`addons/web/controllers/session.py`)
    that calls `session_info()` for real.
    """

    def _set_active_theme_param(self, theme_id):
        self.env["ir.config_parameter"].sudo().set_param(
            CONFIG_PARAM_ACTIVE_THEME_ID, theme_id or ""
        )

    def _get_backend_theme_session_info(self):
        self.authenticate("admin", "admin")
        result = self.make_jsonrpc_request("/web/session/get_session_info")
        return result["backend_theme"]

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

        backend_theme = self._get_backend_theme_session_info()

        self.assertEqual(backend_theme["id"], theme.id)
        self.assertEqual(backend_theme["color_primary"], "#123456")
        self.assertEqual(backend_theme["color_navbar_bg"], "#654321")
        self.assertEqual(backend_theme["color_navbar_text"], "#abcdef")
        self.assertEqual(backend_theme["font_family"], "Roboto, sans-serif")

    def test_session_info_no_theme_configured_uses_defaults(self):
        self._set_active_theme_param(None)

        backend_theme = self._get_backend_theme_session_info()

        self.assertFalse(backend_theme["id"])
        self.assertEqual(backend_theme["color_primary"], DEFAULT_COLOR_PRIMARY)
        self.assertEqual(backend_theme["color_navbar_bg"], DEFAULT_COLOR_NAVBAR_BG)
        self.assertEqual(backend_theme["color_navbar_text"], DEFAULT_COLOR_NAVBAR_TEXT)
        self.assertEqual(backend_theme["font_family"], DEFAULT_FONT_FAMILY)
        self.assertEqual(backend_theme["sidebar_default"], DEFAULT_SIDEBAR_STATE)
        self.assertEqual(DEFAULT_SIDEBAR_STATE, "expanded")
        # Issue #16: no active theme -> every visibility field is True.
        self.assertTrue(backend_theme["show_sidebar"])
        self.assertTrue(backend_theme["show_sidebar_logo"])
        self.assertTrue(backend_theme["show_sidebar_recent"])
        self.assertTrue(backend_theme["show_sidebar_bookmarks"])
        # Issue #17: no active theme -> app_submenu_position is "navbar".
        self.assertEqual(
            backend_theme["app_submenu_position"], DEFAULT_APP_SUBMENU_POSITION
        )
        self.assertEqual(DEFAULT_APP_SUBMENU_POSITION, "navbar")

    def test_session_info_active_theme_sidebar_hidden(self):
        theme = self.env["backend_theme"].create(
            {
                "name": "No Sidebar Theme",
                "code": "IRH006",
                "show_sidebar": False,
            }
        )
        self._set_active_theme_param(theme.id)

        backend_theme = self._get_backend_theme_session_info()

        self.assertFalse(backend_theme["show_sidebar"])
        # The three section switches are ignored while show_sidebar is
        # False, but their own stored value (still True here) is still
        # reported as-is -- the client is the one that ignores them.
        self.assertTrue(backend_theme["show_sidebar_logo"])
        self.assertTrue(backend_theme["show_sidebar_recent"])
        self.assertTrue(backend_theme["show_sidebar_bookmarks"])

    def test_session_info_active_theme_sidebar_recent_hidden(self):
        theme = self.env["backend_theme"].create(
            {
                "name": "No Recent Theme",
                "code": "IRH007",
                "show_sidebar_recent": False,
            }
        )
        self._set_active_theme_param(theme.id)

        backend_theme = self._get_backend_theme_session_info()

        self.assertFalse(backend_theme["show_sidebar_recent"])
        self.assertTrue(backend_theme["show_sidebar"])
        self.assertTrue(backend_theme["show_sidebar_logo"])
        self.assertTrue(backend_theme["show_sidebar_bookmarks"])

    def test_session_info_active_theme_sidebar_collapsed(self):
        theme = self.env["backend_theme"].create(
            {
                "name": "Collapsed Sidebar Theme",
                "code": "IRH004",
                "sidebar_default": "collapsed",
            }
        )
        self._set_active_theme_param(theme.id)

        backend_theme = self._get_backend_theme_session_info()

        self.assertEqual(backend_theme["sidebar_default"], "collapsed")

    def test_session_info_active_theme_sidebar_expanded(self):
        theme = self.env["backend_theme"].create(
            {
                "name": "Expanded Sidebar Theme",
                "code": "IRH005",
                "sidebar_default": "expanded",
            }
        )
        self._set_active_theme_param(theme.id)

        backend_theme = self._get_backend_theme_session_info()

        self.assertEqual(backend_theme["sidebar_default"], "expanded")

    def test_session_info_active_theme_app_submenu_position_popover(self):
        theme = self.env["backend_theme"].create(
            {
                "name": "Popover Submenu Theme",
                "code": "IRH008",
                "app_submenu_position": "popover",
            }
        )
        self._set_active_theme_param(theme.id)

        backend_theme = self._get_backend_theme_session_info()

        self.assertEqual(backend_theme["app_submenu_position"], "popover")

    def test_session_info_deleted_theme_uses_defaults(self):
        theme = self.env["backend_theme"].create(
            {"name": "Deleted Theme", "code": "IRH002", "color_primary": "#ff0000"}
        )
        self._set_active_theme_param(theme.id)
        theme.unlink()

        backend_theme = self._get_backend_theme_session_info()

        self.assertFalse(backend_theme["id"])
        self.assertEqual(backend_theme["color_primary"], DEFAULT_COLOR_PRIMARY)

    def test_session_info_archived_theme_uses_defaults(self):
        theme = self.env["backend_theme"].create(
            {"name": "Archived Theme", "code": "IRH003", "color_primary": "#ff0000"}
        )
        self._set_active_theme_param(theme.id)
        theme.active = False

        backend_theme = self._get_backend_theme_session_info()

        self.assertFalse(backend_theme["id"])
        self.assertEqual(backend_theme["color_primary"], DEFAULT_COLOR_PRIMARY)
