# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo_yaml_test import YamlTransactionCase

from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestIrHttpColorScheme(YamlTransactionCase):
    """Covers `ir.http.color_scheme()` (models/ir_http.py).

    Python murni — pemicu P1 (L-01: `action: call` membuang nilai
    balik method dan tidak menyediakan `save_as`). `color_scheme()`
    tidak memberi efek samping pada record apa pun untuk diperiksa
    lewat `asserts` — satu-satunya hal yang diuji ADALAH nilai
    baliknya itu sendiri, jadi harus dipanggil langsung dari Python.
    `ir.http` juga sebuah `AbstractModel` (tidak punya record ber-id),
    sehingga tak bisa dijadikan `target:` YAML sama sekali.
    """

    def test_color_scheme_returns_dark_for_user_with_dark_preference(self):
        user = self.env["res.users"].create(
            {
                "name": "Dark Mode User",
                "login": "color_scheme_dark_user@example.com",
                "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
                "backend_theme_color_scheme": "dark",
            }
        )
        scheme = self.env["ir.http"].with_user(user).color_scheme()
        self.assertEqual(scheme, "dark")

    def test_color_scheme_falls_back_to_light_when_preference_is_empty(self):
        user = self.env["res.users"].create(
            {
                "name": "No Preference User",
                "login": "color_scheme_empty_user@example.com",
                "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
                "backend_theme_color_scheme": False,
            }
        )
        scheme = self.env["ir.http"].with_user(user).color_scheme()
        self.assertEqual(scheme, "light")

    def test_color_scheme_falls_back_to_light_for_public_user(self):
        public_user = self.env.ref("base.public_user")
        scheme = self.env["ir.http"].with_user(public_user).color_scheme()
        self.assertEqual(scheme, "light")
