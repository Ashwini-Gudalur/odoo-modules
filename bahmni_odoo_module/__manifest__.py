# -*- coding: utf-8 -*-
{
    'name': "bahmni_odoo_module",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'bahmni_atom_feed', 'bahmni_sale', 'bahmni_stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/bahmni_odoo_module_report_mapping.xml',
        'views/bahmni_account_payment_view.xml',
        'report/bahmni_account_payment_report.xml',
        'report/bahmni_insurance_print_report.xml',
        'report/bahmni_account_invoice_payment_report.xml',
        'report/iplit_advance_print_report.xml'
    ]
}
