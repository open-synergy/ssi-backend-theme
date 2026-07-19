# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from . import models  # noqa: F401


def post_init_hook(env):
    """Regenerate the active theme's compiled-in brand colors.

    Self-healing on install/upgrade: the `ir.attachment`/`ir.asset` pair
    created by `backend_theme._sync_active_theme_scss_asset()` is a pure
    cache derived from the `backend_theme` record and the active-theme
    system parameter, so it is safe (and cheap) to regenerate it every
    time the module is installed or upgraded, in case it was ever lost.
    """
    env["backend_theme"]._sync_active_theme_scss_asset()
