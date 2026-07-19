# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBackendThemeAppModuleCategories(TransactionCase):
    """Python murni -- pemicu P1 (L-01/L-02: yang diuji adalah nilai balik
    method `backend_theme._get_app_module_categories()`, bukan efek
    sampingnya pada sebuah record) dikombinasikan dengan P6 (mock/patch).

    Setiap cabang di bawah (tidak ada app sama sekali, app tanpa xmlid,
    xmlid tanpa prefix modul, modul yang tidak dikenal, modul tanpa
    kategori, modul dengan kategori) mustahil dipicu lewat data instalasi
    normal pada basis data uji -- basis data uji selalu memiliki root menu
    ber-xmlid dari modul yang sudah terinstal. Karena itu setiap skenario
    memalsukan hasil ``ir.ui.menu.search()`` (satu-satunya pemanggilan
    method itu di dalam `_get_app_module_categories()`) agar cabangnya
    deterministik, tanpa memodifikasi data instalasi modul yang
    sesungguhnya -- fixture-nya sendiri (``ir.ui.menu``/``ir.model.data``/
    ``ir.module.module``/``ir.module.category``) tetap dibuat lewat ORM
    biasa di dalam transaksi test yang di-rollback otomatis.
    """

    def _mock_apps(self, apps):
        return patch.object(type(self.env["ir.ui.menu"]), "search", return_value=apps)

    def test_no_apps_returns_empty_dict(self):
        with self._mock_apps(self.env["ir.ui.menu"].browse()):
            result = self.env["backend_theme"]._get_app_module_categories()
        self.assertEqual(result, {})

    def test_app_without_xmlid_returns_empty_dict(self):
        menu = self.env["ir.ui.menu"].create({"name": "P1 No Xmlid App"})
        with self._mock_apps(menu):
            result = self.env["backend_theme"]._get_app_module_categories()
        self.assertEqual(result, {})

    def test_app_xmlid_without_module_prefix_returns_empty_dict(self):
        # A blank `module` (real-world equivalent: a Studio/user-created
        # menu) makes `complete_name` -- and therefore the xmlid this
        # method reads -- a bare name with no "." in it at all.
        menu = self.env["ir.ui.menu"].create({"name": "P1 No Module Prefix App"})
        self.env["ir.model.data"].create(
            {
                "module": "",
                "name": "menu_p1_no_module_prefix",
                "model": "ir.ui.menu",
                "res_id": menu.id,
            }
        )
        with self._mock_apps(menu):
            result = self.env["backend_theme"]._get_app_module_categories()
        self.assertEqual(result, {})

    def test_app_xmlid_unresolvable_module_returns_empty_dict(self):
        menu = self.env["ir.ui.menu"].create({"name": "P1 Unknown Module App"})
        self.env["ir.model.data"].create(
            {
                "module": "ssi_backend_theme_test_p1_missing_module",
                "name": "menu_p1_unknown_module",
                "model": "ir.ui.menu",
                "res_id": menu.id,
            }
        )
        with self._mock_apps(menu):
            result = self.env["backend_theme"]._get_app_module_categories()
        self.assertEqual(result, {})

    def test_app_module_without_category_is_absent_from_result(self):
        module = self.env["ir.module.module"].create(
            {"name": "ssi_backend_theme_test_p1_module_no_category"}
        )
        menu = self.env["ir.ui.menu"].create({"name": "P1 No Category App"})
        self.env["ir.model.data"].create(
            {
                "module": module.name,
                "name": "menu_p1_no_category",
                "model": "ir.ui.menu",
                "res_id": menu.id,
            }
        )
        with self._mock_apps(menu):
            result = self.env["backend_theme"]._get_app_module_categories()
        self.assertEqual(result, {})

    def test_app_module_with_category_is_included_in_result(self):
        category = self.env["ir.module.category"].create(
            {"name": "P1 Test Category", "sequence": 7}
        )
        module = self.env["ir.module.module"].create(
            {
                "name": "ssi_backend_theme_test_p1_module_with_category",
                "category_id": category.id,
            }
        )
        menu = self.env["ir.ui.menu"].create({"name": "P1 Categorized App"})
        self.env["ir.model.data"].create(
            {
                "module": module.name,
                "name": "menu_p1_categorized",
                "model": "ir.ui.menu",
                "res_id": menu.id,
            }
        )
        with self._mock_apps(menu):
            result = self.env["backend_theme"]._get_app_module_categories()
        self.assertEqual(
            result,
            {menu.id: {"id": category.id, "name": "P1 Test Category", "sequence": 7}},
        )

    def test_multiple_apps_mixed_categories_and_other(self):
        category = self.env["ir.module.category"].create(
            {"name": "P1 Mixed Category", "sequence": 3}
        )
        categorized_module = self.env["ir.module.module"].create(
            {
                "name": "ssi_backend_theme_test_p1_mixed_categorized",
                "category_id": category.id,
            }
        )
        uncategorized_module = self.env["ir.module.module"].create(
            {"name": "ssi_backend_theme_test_p1_mixed_uncategorized"}
        )
        categorized_menu = self.env["ir.ui.menu"].create(
            {"name": "P1 Mixed Categorized"}
        )
        uncategorized_menu = self.env["ir.ui.menu"].create(
            {"name": "P1 Mixed Uncategorized"}
        )
        self.env["ir.model.data"].create(
            [
                {
                    "module": categorized_module.name,
                    "name": "menu_p1_mixed_categorized",
                    "model": "ir.ui.menu",
                    "res_id": categorized_menu.id,
                },
                {
                    "module": uncategorized_module.name,
                    "name": "menu_p1_mixed_uncategorized",
                    "model": "ir.ui.menu",
                    "res_id": uncategorized_menu.id,
                },
            ]
        )
        apps = categorized_menu + uncategorized_menu
        with self._mock_apps(apps):
            result = self.env["backend_theme"]._get_app_module_categories()
        self.assertEqual(
            result,
            {
                categorized_menu.id: {
                    "id": category.id,
                    "name": "P1 Mixed Category",
                    "sequence": 3,
                }
            },
        )
        self.assertNotIn(uncategorized_menu.id, result)
