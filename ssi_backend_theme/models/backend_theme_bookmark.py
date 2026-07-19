# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class BackendThemeBookmark(models.Model):
    """A single user's personal sidebar bookmark (issue #13).

    Deliberately NOT a `mixin.master_data`: this is disposable, per-user
    data managed entirely from the sidebar's BOOKMARKS panel (no backend
    menu, action window, or form view for it), not shared configuration
    -- so it skips the sequence/code machinery that mixin brings.
    Visibility is restricted to each bookmark's own owner by the
    accompanying `ir.rule` (security/ir_rule/backend_theme_bookmark.xml),
    not by any dedicated group -- every internal user already has full
    CRUD on the model itself (security/ir_model_access/
    backend_theme_bookmark.xml); the rule is what keeps users from
    reaching each other's rows.
    """

    _name = "backend_theme_bookmark"
    _description = "Backend Theme Sidebar Bookmark"
    _order = "sequence, name"

    user_id = fields.Many2one(
        comodel_name="res.users",
        required=True,
        default=lambda self: self.env.user,
        ondelete="cascade",
        help="Owner of this bookmark. Only this user can see or manage "
        "it -- enforced by the record rule, not by any group.",
    )
    name = fields.Char(
        required=True,
        help="Label shown for this bookmark in the sidebar's BOOKMARKS panel.",
    )
    action_url = fields.Char(
        string="URL",
        required=True,
        help="Backend path (e.g. '/odoo/res.partner/12') this bookmark "
        "opens when clicked.",
    )
    sequence = fields.Integer(
        default=10,
        help="Determines the display order of bookmarks in the sidebar "
        "panel, ascending, then by name.",
    )
