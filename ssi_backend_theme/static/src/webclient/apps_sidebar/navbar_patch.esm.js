// Copyright 2026 OpenSynergy Indonesia
// Copyright 2026 PT. Simetri Sinergi Indonesia
// License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import {AppsSidebar} from "./apps_sidebar.esm";
import {NavBar} from "@web/webclient/navbar/navbar";
import {patch} from "@web/core/utils/patch";

// Only the static `components` registry needs patching so the template
// extension (navbar_patch.xml) can use `<AppsSidebar/>`. `NavBar`'s own
// behavior (state, services, adapt logic, ...) is untouched — the mobile
// off-canvas sidebar (`web.NavBar.AppsMenu.Sidebar`, guarded by
// `this.ui.isSmall`) is a fully separate template branch, left as-is.
patch(NavBar, {
    components: {...NavBar.components, AppsSidebar},
});
