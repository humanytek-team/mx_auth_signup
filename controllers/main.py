# -*- coding: utf-8 -*-
# Copyright 2017 Humanytek - Manuel Marquez <manuel@humanytek.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging
import werkzeug

import openerp
from openerp.addons.auth_signup.res_users import SignupError
from openerp import http
from openerp.http import request
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class AuthSignupHome(openerp.addons.auth_signup.controllers.main.AuthSignupHome):

    @http.route()
    def web_auth_signup(self, *args, **kw):
        ResCountry = request.env['res.country']
        ResState = request.env['res.country.state']

        qcontext = self.get_auth_signup_qcontext()

        try:
            ResCountryZipSatCode = request.env['res.country.zip.sat.code']
            ResCountryTownshipSatCode = request.env[
                'res.country.township.sat.code']
            ResCountryLocalitySatCode = request.env[
                'res.country.locality.sat.code']

            qcontext.update({
                'townships': ResCountryTownshipSatCode.sudo().search([]),
                'localities': ResCountryLocalitySatCode.sudo().search([]),
            })

        except Exception:
            pass

        qcontext.update({'countries': ResCountry.search([])})
        qcontext.update({'states': ResState.search([])})

        if not qcontext.get('billing_data', False):

            qcontext['billing_data'] = dict()

            mx = ResCountry.search([('code', '=', 'MX')])
            if mx:
                qcontext['billing_data']['country_id'] = mx[0].id

            if qcontext.get('vat'):
                qcontext['billing_data']['vat'] = qcontext['vat']

            if qcontext.get('phone'):
                qcontext['billing_data']['phone'] = qcontext['phone']

            if qcontext.get('street'):
                qcontext['billing_data']['street'] = qcontext['street']

            if qcontext.get('l10n_mx_street3'):
                qcontext['billing_data']['l10n_mx_street3'] = qcontext['l10n_mx_street3']

            if qcontext.get('l10n_mx_street4'):
                qcontext['billing_data']['l10n_mx_street4'] = qcontext['l10n_mx_street4']

            if qcontext.get('street2'):
                qcontext['billing_data']['street2'] = qcontext['street2']

            if qcontext.get('city'):
                qcontext['billing_data']['city'] = qcontext['city']

            if qcontext.get('zip_sat_id'):
                qcontext['billing_data']['zip_sat_id'] = qcontext['zip_sat_id']

            if qcontext.get('country_id'):
                qcontext['billing_data']['country_id'] = int(qcontext['country_id'])

            if qcontext.get('state_id'):
                qcontext['billing_data']['state_id'] = int(qcontext['state_id'])

            if qcontext.get('township_sat_id'):
                qcontext['billing_data']['township_sat_id'] = int(qcontext['township_sat_id'])

            if qcontext.get('locality_sat_id'):
                qcontext['billing_data']['locality_sat_id'] = int(qcontext['locality_sat_id'])

            if qcontext.get('shipping_name'):
                qcontext['billing_data']['shipping_name'] = qcontext['shipping_name']

            if qcontext.get('shipping_phone'):
                qcontext['billing_data']['shipping_phone'] = qcontext['shipping_phone']

            if qcontext.get('shipping_street'):
                qcontext['billing_data']['shipping_street'] = qcontext['shipping_street']

            if qcontext.get('shipping_city'):
                qcontext['billing_data']['shipping_city'] = qcontext['shipping_city']

            if qcontext.get('shipping_zip_sat_id'):
                qcontext['billing_data']['shipping_zip_sat_id'] = qcontext['shipping_zip_sat_id']

            if qcontext.get('shipping_country_id'):
                qcontext['billing_data']['shipping_country_id'] = int(qcontext['shipping_country_id'])

            if qcontext.get('shipping_state_id'):
                qcontext['billing_data']['shipping_state_id'] = int(qcontext['shipping_state_id'])

            if qcontext.get('shipping_township_sat_id'):
                qcontext['billing_data']['shipping_township_sat_id'] = int(qcontext['shipping_township_sat_id'])

            if qcontext.get('shipping_locality_sat_id'):
                qcontext['billing_data']['shipping_locality_sat_id'] = int(qcontext['shipping_locality_sat_id'])

            if qcontext.get('generate_invoice', False) == 'on':
                qcontext['billing_data']['generate_invoice'] = qcontext['generate_invoice']

        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':

            if qcontext.get('generate_invoice', False) == 'on':

                vat = qcontext.get('vat', False)
                zip_code = qcontext.get('zip_code', False)

                if not vat:
                    qcontext['error'] = _('Debe indicar su RFC')
                    return request.render('auth_signup.signup', qcontext)

                else:

                    ResPartner = request.env['res.partner']
                    partner = ResPartner.search([('vat', '=', vat)])

                    if partner:
                        qcontext.update({'partner_exists': True})

            try:
                self.do_signup(qcontext)
                return super(AuthSignupHome, self).web_login(*args, **kw)

            except (SignupError, AssertionError), e:

                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _(
                        "Another user is already registered using this email address.")

                else:
                    _logger.error(e.message)
                    qcontext['error'] = _(
                        "Could not create a new account. %s" % e.message)

        return request.render('auth_signup.signup', qcontext)

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """

        values = dict((key, qcontext.get(key))
                      for key in ('login', 'name', 'password'))
        assert any([k for k in values.values()]
                   ), "The form was not properly filled in."
        assert values.get('password') == qcontext.get(
            'confirm_password'), "Passwords do not match; please retype them."
        supported_langs = [lang['code'] for lang in request.registry[
            'res.lang'].search_read(request.cr, openerp.SUPERUSER_ID, [], ['code'])]
        if request.lang in supported_langs:
            values['lang'] = request.lang

        if qcontext.get('generate_invoice') == 'on' and qcontext.get('partner_exists', False):
            ResPartner = request.env['res.partner']
            partner = ResPartner.search([('vat', '=', qcontext['vat'])])
            if partner:
                partner_id = partner[0].id
                values.update({'partner_id': partner_id})
                del values['name']

        elif qcontext.get('generate_invoice') == 'on' and not qcontext.get('partner_exists', False):

            if qcontext.get('vat', False):
                values['vat'] = qcontext['vat']

            if qcontext.get('phone', False):
                values['phone'] = qcontext['phone']

            if qcontext.get('street', False):
                values['street'] = qcontext['street']

            if qcontext.get('l10n_mx_street3', False):
                values['l10n_mx_street3'] = qcontext['l10n_mx_street3']

            if qcontext.get('l10n_mx_street4', False):
                values['l10n_mx_street4'] = qcontext['l10n_mx_street4']

            if qcontext.get('street2', False):
                values['street2'] = qcontext['street2']

            if qcontext.get('city', False):
                values['city'] = qcontext['city']

            if qcontext.get('zip_sat_id', False):
                values['zip_sat_id'] = qcontext['zip_sat_id']

            if qcontext.get('country_id', False):
                values['country_id'] = qcontext['country_id']

            if qcontext.get('state_id', False):
                values['state_id'] = qcontext['state_id']

            if qcontext.get('township_sat_id', False):
                values['township_sat_id'] = qcontext['township_sat_id']

            if qcontext.get('locality_sat_id', False):
                values['locality_sat_id'] = qcontext['locality_sat_id']

            shipping_info = dict()

            if qcontext.get('shipping_name', False):
                shipping_info['name'] = qcontext['shipping_name']

            if qcontext.get('shipping_phone', False):
                shipping_info['phone'] = qcontext['shipping_phone']

            if qcontext.get('shipping_street', False):
                shipping_info['street'] = qcontext['shipping_street']

            if qcontext.get('shipping_city', False):
                shipping_info['city'] = qcontext['shipping_city']

            if qcontext.get('shipping_zip_sat_id', False):
                shipping_info['zip_sat_id'] = qcontext[
                    'shipping_zip_sat_id']

            if qcontext.get('shipping_country_id', False):
                shipping_info['country_id'] = qcontext[
                    'shipping_country_id']

            if qcontext.get('shipping_state_id', False):
                shipping_info[
                    'state_id'] = qcontext['shipping_state_id']

            if qcontext.get('shipping_township_sat_id', False):
                shipping_info[
                    'township_sat_id'] = qcontext['shipping_township_sat_id']

            if qcontext.get('shipping_locality_sat_id', False):
                shipping_info['locality_sat_id'] = qcontext[
                    'shipping_locality_sat_id']

            if shipping_info:
                shipping_info['type'] = 'delivery'
                values['child_ids'] = [(0, 0, shipping_info)]

        else:

            contact_invoice = dict()
            contact_invoice['vat'] = 'MXXAXX010101000'
            contact_invoice['name'] = _('PUBLICO GENERAL')
            contact_invoice['type'] = 'invoice'
            values['child_ids'] = [(0, 0, contact_invoice)]

        values['customer'] = True

        self._signup_with_values(qcontext.get('token'), values)
        request.cr.commit()
