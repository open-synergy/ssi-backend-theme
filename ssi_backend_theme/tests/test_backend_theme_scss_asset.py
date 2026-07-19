# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64

from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged

from ..models.backend_theme import (
    CONFIG_PARAM_ACTIVE_THEME_ID,
    DEFAULT_COLOR_PRIMARY,
    SCSS_ASSET_BUNDLE,
    SCSS_ASSET_CUSTOM_URL,
    SCSS_ASSET_TARGET_PATH,
)


@tagged("post_install", "-at_install")
class TestBackendThemeScssAsset(YamlTransactionCase):
    """Python murni — pemicu P4 (L-08: isi field binary/attachment tak
    bisa di-assert lewat YAML `assert` — setiap test di bawah men-decode
    base64 `ir.attachment.datas` untuk memverifikasi SCSS yang
    ter-generate oleh `backend_theme._sync_active_theme_scss_asset()`
    memuat warna tema aktif yang benar).
    """

    def _set_active_theme_param(self, theme_id):
        self.env["ir.config_parameter"].sudo().set_param(
            CONFIG_PARAM_ACTIVE_THEME_ID, theme_id or ""
        )

    def _get_generated_scss(self):
        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .search([("url", "=", SCSS_ASSET_CUSTOM_URL)], limit=1)
        )
        self.assertTrue(attachment, "SCSS override attachment was not created")
        return base64.b64decode(attachment.datas).decode("utf-8")

    def _get_replace_assets(self):
        return (
            self.env["ir.asset"]
            .sudo()
            .search(
                [
                    ("bundle", "=", SCSS_ASSET_BUNDLE),
                    ("target", "=", SCSS_ASSET_TARGET_PATH),
                    ("directive", "=", "replace"),
                ]
            )
        )

    def test_sync_creates_asset_and_attachment(self):
        theme = self.env["backend_theme"].create(
            {
                "name": "Sync Theme",
                "code": "SCSS001",
                "color_primary": "#010203",
                "color_navbar_bg": "#040506",
            }
        )
        self._set_active_theme_param(theme.id)
        self.env["backend_theme"]._sync_active_theme_scss_asset()

        content = self._get_generated_scss()
        self.assertIn("$o-brand-primary: #010203 !default;", content)
        self.assertIn("$o-brand-odoo: #040506 !default;", content)
        self.assertEqual(len(self._get_replace_assets()), 1)

    def test_sync_is_idempotent(self):
        theme = self.env["backend_theme"].create(
            {"name": "Idempotent Theme", "code": "SCSS002", "color_primary": "#111111"}
        )
        self._set_active_theme_param(theme.id)

        self.env["backend_theme"]._sync_active_theme_scss_asset()
        self.env["backend_theme"]._sync_active_theme_scss_asset()

        attachments = (
            self.env["ir.attachment"]
            .sudo()
            .search([("url", "=", SCSS_ASSET_CUSTOM_URL)])
        )
        self.assertEqual(len(attachments), 1)
        self.assertEqual(len(self._get_replace_assets()), 1)

    def test_write_active_theme_color_resyncs(self):
        theme = self.env["backend_theme"].create(
            {"name": "Live Theme", "code": "SCSS003", "color_primary": "#aaaaaa"}
        )
        self._set_active_theme_param(theme.id)
        self.env["backend_theme"]._sync_active_theme_scss_asset()

        theme.write({"color_primary": "#bbbbbb"})

        content = self._get_generated_scss()
        self.assertIn("$o-brand-primary: #bbbbbb !default;", content)

    def test_archiving_active_theme_resyncs_to_default(self):
        theme = self.env["backend_theme"].create(
            {"name": "Archive Theme", "code": "SCSS004", "color_primary": "#cccccc"}
        )
        self._set_active_theme_param(theme.id)
        self.env["backend_theme"]._sync_active_theme_scss_asset()

        theme.write({"active": False})

        content = self._get_generated_scss()
        self.assertIn(
            f"$o-brand-primary: {DEFAULT_COLOR_PRIMARY} !default;", content
        )

    def test_deleting_active_theme_resyncs_to_default(self):
        theme = self.env["backend_theme"].create(
            {"name": "Delete Theme", "code": "SCSS005", "color_primary": "#dddddd"}
        )
        self._set_active_theme_param(theme.id)
        self.env["backend_theme"]._sync_active_theme_scss_asset()

        theme.unlink()

        content = self._get_generated_scss()
        self.assertIn(
            f"$o-brand-primary: {DEFAULT_COLOR_PRIMARY} !default;", content
        )
