# -*- coding: utf-8 -*-
{
    'name': 'IPLIT GST ODOO',
    'version': '1.0',
    'summary': 'Custom product module to meet bahmni requirement',
    'sequence': 1,
    'description': """
IPLIT Odoo
====================
""",
    'category': '',
    'website': '',
    'images': [],
    'depends': ['base', 'account', 'sale', 'report'],
    'data': ['report/invoice_report_inherit.xml',
             'views/account_invoice.xml',
             'views/iplit_invoice.xml',
             'report/invoice_gst_report.xml',
             ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
