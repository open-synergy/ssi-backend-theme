# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64

from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged

from ..models.backend_theme import (
    CONFIG_PARAM_ACTIVE_THEME_ID,
    DEFAULT_COLOR_PRIMARY,
    DEFAULT_COLOR_SUCCESS,
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
        self.assertIn(f"$o-brand-primary: {DEFAULT_COLOR_PRIMARY} !default;", content)

    def test_deleting_active_theme_resyncs_to_default(self):
        theme = self.env["backend_theme"].create(
            {"name": "Delete Theme", "code": "SCSS005", "color_primary": "#dddddd"}
        )
        self._set_active_theme_param(theme.id)
        self.env["backend_theme"]._sync_active_theme_scss_asset()

        theme.unlink()

        content = self._get_generated_scss()
        self.assertIn(f"$o-brand-primary: {DEFAULT_COLOR_PRIMARY} !default;", content)

    def test_write_non_active_theme_does_not_resync(self):
        active_theme = self.env["backend_theme"].create(
            {"name": "Still Active", "code": "SCSS006", "color_primary": "#eeeeee"}
        )
        other_theme = self.env["backend_theme"].create(
            {"name": "Not Active", "code": "SCSS007", "color_primary": "#000000"}
        )
        self._set_active_theme_param(active_theme.id)
        self.env["backend_theme"]._sync_active_theme_scss_asset()

        other_theme.write({"color_primary": "#123123"})

        content = self._get_generated_scss()
        self.assertIn("$o-brand-primary: #eeeeee !default;", content)
        self.assertNotIn("#123123", content)

    def test_write_color_without_any_active_theme_does_not_error(self):
        theme = self.env["backend_theme"].create(
            {"name": "No Active Theme Yet", "code": "SCSS008"}
        )
        self._set_active_theme_param(None)

        # Snapshot before: other test methods in this class may have
        # already synced the (global, singleton) SCSS override
        # attachment — this must stay untouched by this write(), not
        # necessarily absent.
        before = (
            self.env["ir.attachment"]
            .sudo()
            .search([("url", "=", SCSS_ASSET_CUSTOM_URL)])
        )
        before_datas = before.datas if before else False

        theme.write({"color_primary": "#456456"})

        after = (
            self.env["ir.attachment"]
            .sudo()
            .search([("url", "=", SCSS_ASSET_CUSTOM_URL)])
        )
        self.assertEqual(len(before), len(after))
        self.assertEqual(before_datas, after.datas if after else False)

    def test_unlink_non_active_theme_does_not_resync(self):
        active_theme = self.env["backend_theme"].create(
            {"name": "Kept Active", "code": "SCSS009", "color_primary": "#777777"}
        )
        other_theme = self.env["backend_theme"].create(
            {"name": "To Be Deleted", "code": "SCSS010"}
        )
        self._set_active_theme_param(active_theme.id)
        self.env["backend_theme"]._sync_active_theme_scss_asset()

        other_theme.unlink()

        content = self._get_generated_scss()
        self.assertIn("$o-brand-primary: #777777 !default;", content)

    def test_sync_creates_asset_with_all_new_color_fields(self):
        """issue #14: text/background/status colors must reach the
        regenerated SCSS as the correct, verified Odoo 19 variable names.
        """
        theme = self.env["backend_theme"].create(
            {
                "name": "Full Palette Theme",
                "code": "SCSS012",
                "color_text_body": "#111111",
                "color_view_background": "#222222",
                "color_success": "#333333",
                "color_info": "#444444",
                "color_warning": "#555555",
                "color_danger": "#666666",
            }
        )
        self._set_active_theme_param(theme.id)
        self.env["backend_theme"]._sync_active_theme_scss_asset()

        content = self._get_generated_scss()
        self.assertIn("$o-main-text-color: #111111 !default;", content)
        self.assertIn("$o-view-background-color: #222222 !default;", content)
        self.assertIn("$o-success: #333333 !default;", content)
        self.assertIn("$o-info: #444444 !default;", content)
        self.assertIn("$o-warning: #555555 !default;", content)
        self.assertIn("$o-danger: #666666 !default;", content)

    def test_write_active_theme_status_color_resyncs(self):
        """issue #14: writing color_success on the active theme must
        resync the compiled asset, exactly like color_primary already
        does — the field is required to be in `write()`'s trigger set.
        """
        theme = self.env["backend_theme"].create(
            {"name": "Status Live Theme", "code": "SCSS013", "color_success": "#aaaaaa"}
        )
        self._set_active_theme_param(theme.id)
        self.env["backend_theme"]._sync_active_theme_scss_asset()

        theme.write({"color_success": "#bbbbbb"})

        content = self._get_generated_scss()
        self.assertIn("$o-success: #bbbbbb !default;", content)

    def test_write_status_color_on_non_active_theme_does_not_resync(self):
        """issue #14: writing color_success on a theme that is NOT the
        active one must leave the compiled asset untouched.
        """
        active_theme = self.env["backend_theme"].create(
            {"name": "Still Active 2", "code": "SCSS014", "color_success": "#cccccc"}
        )
        other_theme = self.env["backend_theme"].create(
            {"name": "Not Active 2", "code": "SCSS015", "color_success": "#000000"}
        )
        self._set_active_theme_param(active_theme.id)
        self.env["backend_theme"]._sync_active_theme_scss_asset()

        other_theme.write({"color_success": "#dddddd"})

        content = self._get_generated_scss()
        self.assertIn("$o-success: #cccccc !default;", content)
        self.assertNotIn("#dddddd", content)

    def test_clearing_status_color_resyncs_to_default(self):
        """issue #14: clearing a color field on the active theme must
        resync the asset back to Odoo's own default value, not leave
        the previous custom value baked in.
        """
        theme = self.env["backend_theme"].create(
            {
                "name": "Status Clear Theme",
                "code": "SCSS016",
                "color_success": "#777777",
            }
        )
        self._set_active_theme_param(theme.id)
        self.env["backend_theme"]._sync_active_theme_scss_asset()

        theme.write({"color_success": False})

        content = self._get_generated_scss()
        self.assertIn(f"$o-success: {DEFAULT_COLOR_SUCCESS} !default;", content)

    def test_active_theme_ignores_non_numeric_parameter(self):
        theme = self.env["backend_theme"].create(
            {
                "name": "Garbage Param Theme",
                "code": "SCSS011",
                "color_primary": "#999999",
            }
        )
        self.env["ir.config_parameter"].sudo().set_param(
            CONFIG_PARAM_ACTIVE_THEME_ID, "not-a-number"
        )

        resolved = self.env["backend_theme"]._get_active_theme()
        self.assertFalse(resolved)

        # write() on `theme` must not blow up trying to int() the
        # garbage parameter value either.
        theme.write({"color_primary": "#888888"})
