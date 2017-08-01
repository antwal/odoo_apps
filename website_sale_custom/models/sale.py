# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Walter Antolini (info@antwal.name)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, fields
from openerp.tools.translate import _


class sale_order(models.Model):
    _inherit = "sale.order"

    @api.model
    def create(self, vals):
        vals['user_id'] = self.env.user.company_id.default_salesperson_id.id
        return super(sale_order, self).create(vals)

    @api.v7
    def action_quotation_send_to_test(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi sale template message loaded by default
        '''
        # Unsubscribing the customer to avoid sending the email to himself too
        partner = self.browse(cr, uid, ids)
        partner_ids = [partner.partner_id.id]
        self.message_unsubscribe(cr, uid, ids, partner_ids, context)

        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')

        template_id = self._get_email_template(cr, uid, ids, context)

        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
            å
        ctx = dict()
        ctx.update({
            'default_model': 'sale.order',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

        return True

    @api.v7
    def _get_email_template(self, cr, uid, ids, context=None):
        '''
        Extend this method for change default email template
        '''
        ir_model_data = self.pool['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference(
                                    cr, uid, 'cpn_website_sale', 'custom_mail_template')[1]
        except ValueError:
            template_id = False
        return template_id
