# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class IrHttp(models.AbstractModel):
    """Exposes the active backend theme values to the browser session.

    Adds a single `backend_theme` key to `session_info()`, carrying the
    active theme's values (or module defaults when there is none), so
    the OWL service on the client side can apply them without an extra
    RPC round-trip.

    Also overrides `color_scheme()` so the backend loads the logged-in
    user's own light/dark preference (`res.users.
    backend_theme_color_scheme`, see models/res_users.py), falling
    back to core's own default ("light") for public/anonymous sessions
    or an unset preference. `webclient_rendering_context()` itself
    (addons/web/models/ir_http.py) is left untouched — it already
    calls `color_scheme()`, which is the only integration point
    needed: it decides, at render time, whether `web.assets_web` or
    `web.assets_web_dark` is loaded (see
    addons/web/views/webclient_templates.xml `web.webclient_bootstrap`).
    """

    _inherit = "ir.http"

    def session_info(self):
        result = super().session_info()
        result["backend_theme"] = self.env[
            "backend_theme"
        ]._get_backend_theme_session_values()
        return result

    def color_scheme(self):
        user = self.env.user
        if not user or user._is_public():
            return super().color_scheme()
        return user.backend_theme_color_scheme or super().color_scheme()
