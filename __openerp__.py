# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

{
    'name': 'User registration with billing data',
    'version': '9.0.1.0.0',
    'category': 'Extra Tools',
    'author': 'Humanytek',
    'website': "http://www.humanytek.com",
    'license': 'AGPL-3',
    'depends': ['auth_signup', ],
    'data': [
        'views/mx_auth_signup_templates.xml',
    ],
    'installable': True,
    'auto_install': False
}
