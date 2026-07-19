# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Backend Theme",
    "version": "19.0.1.4.0",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "contributors": [
        "Andhitia Rama <andhitia.r@gmail.com>",
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "post_init_hook": "post_init_hook",
    "depends": [
        "ssi_master_data_mixin",
        "web",
        "base_setup",
    ],
    "data": [
        "security/ir_module_category/backend_theme.xml",
        "security/res_groups/backend_theme.xml",
        "security/ir_model_access/backend_theme.xml",
        "ir_sequence/backend_theme.xml",
        "sequence_template/backend_theme.xml",
        "menu.xml",
        "views/backend_theme.xml",
        "views/res_config_settings.xml",
        "views/res_users.xml",
    ],
    "assets": {
        "web._assets_primary_variables": [
            (
                "prepend",
                "ssi_backend_theme/static/src/scss/"
                "backend_theme_primary_variables.scss",
            ),
        ],
        "web._assets_backend_helpers": [
            (
                "prepend",
                "ssi_backend_theme/static/src/scss/backend_theme_backend_helpers.scss",
            ),
        ],
        "web.assets_backend": [
            "ssi_backend_theme/static/src/js/*",
            "ssi_backend_theme/static/src/webclient/apps_sidebar/*",
            "ssi_backend_theme/static/src/webclient/color_scheme/*",
            "ssi_backend_theme/static/src/scss/backend_theme_list_view.scss",
            "ssi_backend_theme/static/src/scss/backend_theme_form_view.scss",
        ],
    },
}
