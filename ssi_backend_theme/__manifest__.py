# Copyright 2026 OpenSynergy Indonesia
# Copyright 2026 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Backend Theme",
    "version": "19.0.1.0.0",
    "website": "https://simetri-sinergi.id",
    "author": "OpenSynergy Indonesia, PT. Simetri Sinergi Indonesia",
    "contributors": [
        "Andhitia Rama <andhitia.r@gmail.com>",
    ],
    "license": "AGPL-3",
    "installable": True,
    "application": False,
    "depends": [
        "ssi_master_data_mixin",
    ],
    "data": [
        "security/ir_module_category/backend_theme.xml",
        "security/res_groups/backend_theme.xml",
        "security/ir_model_access/backend_theme.xml",
        "ir_sequence/backend_theme.xml",
        "sequence_template/backend_theme.xml",
        "menu.xml",
        "views/backend_theme.xml",
    ],
}
