# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from ast import literal_eval
import logging

from openerp import api, models
from openerp.addons.auth_signup.res_users import SignupError
from openerp.exceptions import UserError
from openerp.tools.misc import ustr

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.v7
    def _signup_create_user(self, cr, uid, values, context=None):
        """ create a new user from the template user """
        ir_config_parameter = self.pool.get('ir.config_parameter')
        template_user_id = literal_eval(ir_config_parameter.get_param(
            cr, uid, 'auth_signup.template_user_id', 'False'))
        assert template_user_id and self.exists(
            cr, uid, template_user_id, context=context), 'Signup: invalid template user'

        # check that uninvited users may sign up
        if 'partner_id' not in values:
            if not literal_eval(ir_config_parameter.get_param(cr, uid, 'auth_signup.allow_uninvited', 'False')):
                raise SignupError('Signup is not allowed for uninvited users')

        assert values.get('login'), "Signup: no login given for new user"
        assert values.get('partner_id') or values.get(
            'name'), "Signup: no name or partner given for new user"

        values['active'] = True
        context = dict(context or {}, no_reset_password=True)

        values2 = dict()

        if values.get('l10n_mx_street3', False):
            values2['l10n_mx_street3'] = values['l10n_mx_street3']
            del values['l10n_mx_street3']

        if values.get('l10n_mx_street4', False):
            values2['l10n_mx_street4'] = values['l10n_mx_street4']
            del values['l10n_mx_street4']

        if values.get('zip_sat_id', False):
            values2['zip_sat_id'] = values['zip_sat_id']
            del values['zip_sat_id']

        if values.get('township_sat_id', False):
            values2['township_sat_id'] = values['township_sat_id']
            del values['township_sat_id']

        if values.get('locality_sat_id', False):
            values2['locality_sat_id'] = values['locality_sat_id']
            del values['locality_sat_id']

        try:
            with cr.savepoint():
                new_user_id = self.copy(
                    cr, uid, template_user_id, values, context=context)

                try:
                    self.write(cr, uid, new_user_id, values2, context=context)
                except Exception:
                    pass

                return new_user_id
        except Exception, e:
            # copy may failed if asked login is not available.
            raise SignupError(ustr(e))
