# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm
from openerp.tools.translate import _
from dateutil.relativedelta import relativedelta
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class account_asset_remove_select(orm.TransientModel):
    _name = 'account.asset.remove.select'
    _description = 'Remove Asset'
    
    def _get_invoice_lines(self, cr, uid, context=None):
        if not context:
            context = {}
        inv_line_obj = self.pool.get('account.invoice.line')
        currency_obj = self.pool.get('res.currency')
        asset_id = context.get('active_id')
        sale_value = 0.0
        account_sale_id = False
        domain = [('invoice_id.type', 'in', ['out_invoice']),
                  ('asset_id', '=', asset_id)]
        inv_line_ids = inv_line_obj.search(
            cr, uid, domain, context=context)
        return inv_line_ids
    
    def continue_remove(self, cr, uid, ids, context=None):
        assert len(ids) == 1
        inv_line_ids = []
        wiz = self.browse(cr, uid, ids[0])
            # For now it's possible remove asset without out invoice
            # if not wiz.invoice_line_ids:
            #    raise orm.except_orm(
            #            _('You cannot remove the asset!'),
            #            _("You Must before select a move line."))
        asset_id = context.get('active_id')
        asset = self.pool['account.asset.asset'].browse(cr, uid, asset_id)
        date_remove = False
        sale_value = 0.0
        account_sale_id = False
        if wiz.invoice_line_ids:
            for line in wiz.invoice_line_ids: 
                inv_line_ids.append(line.id)
                if not date_remove or (date_remove and date_invoce < \
                                        line.invoice_id.date_invoice):
                    date_remove = line.invoice_id.date_invoice
                    account_sale_id = line.account_id.id
                sale_value += line.price_subtotal 
        context.update({'invoice_line_ids': inv_line_ids})
        context.update({'invoice_sale_value': sale_value})
        
        # Create wizard for remove
        remove_wiz_id = False
        if wiz.invoice_line_ids:
            vals = {
                'date_remove' : date_remove or False,
                'sale_value' : sale_value or 0,
                'account_sale_id' : account_sale_id or False,
                'account_plus_value_id' : 
                    asset.category_id.account_plus_value_id.id or False,
                'account_min_value_id' : 
                    asset.category_id.account_min_value_id.id or False,
                }
            remove_wiz_id = self.pool['account.asset.remove'].create(cr, uid, 
                                                                     vals)
        
        return {
            'name': _("Generate Asset Removal entries"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.asset.remove',
            'res_id': remove_wiz_id,
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': context,
            'nodestroy': True,
        }
        
    _columns = {
        'invoice_line_ids': fields.many2many('account.invoice.line', 
                                     string='Account Moves')
    }
    
    _defaults = {
        'invoice_line_ids': _get_invoice_lines,
    }
