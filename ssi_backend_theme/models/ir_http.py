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
    """

    _inherit = "ir.http"

    def session_info(self):
        result = super().session_info()
        result["backend_theme"] = self.env[
            "backend_theme"
        ]._get_backend_theme_session_values()
        return result
