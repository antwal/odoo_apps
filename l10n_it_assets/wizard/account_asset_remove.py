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


class account_asset_remove(orm.TransientModel):
    _inherit = 'account.asset.remove'
    
    def _posting_regime(self, cr, uid, context=None):
        return[
            ('gain_loss_on_sale', _('Gain/Loss on Sale')),
        ]
    
    _columns = {
        'posting_regime': fields.selection(
            _posting_regime, 'Removal Entry Policy',
            required=True,
            help="Removal Entry Policy \n"
                 "  * Residual Value: The non-depreciated value will be "
                 "posted on the 'Residual Value Account' \n"
                 "  * Gain/Loss on Sale: The Gain or Loss will be posted on "
                 "the 'Plus-Value Account' or 'Min-Value Account' "),
        }
    
    def _prepare_early_removal(self, cr, uid,
                               asset, date_remove, context=None):
        """
        Generate last depreciation entry on the day before the removal date.
        """
        res = {
            'residual_value' : 0,
            'residual_value_fiscal' : 0,
            }
        asset_line_obj = self.pool.get('account.asset.depreciation.line')
        asset_obj = self.pool['account.asset.asset']
        digits = self.pool.get('decimal.precision').precision_get(
            cr, uid, 'Account')
        
        # Step 1: Compute values
        # Normal
        domain = [('asset_id', '=', asset.id), ('type', '=', 'depreciate'), 
                  ('init_entry', '=', False), ('move_check', '=', False)]
        asset_line_obj = self.pool['account.asset.depreciation.line']
        dl_ids = asset_line_obj.search(cr, uid, domain, order='line_date asc')
        first_to_depreciate_dl = asset_line_obj.browse(cr, uid, dl_ids[0])    
        
        first_date = first_to_depreciate_dl.line_date
        if date_remove > first_date:
            raise orm.except_orm(
                _('Error!'),
                _("You can't make an early removal if all the depreciation "
                  "lines for previous periods are not posted."))
        last_depr_date = first_to_depreciate_dl.previous_id.line_date
        period_number_days = (
            datetime.strptime(first_date, '%Y-%m-%d') -
            datetime.strptime(last_depr_date, '%Y-%m-%d')).days
        date_remove_obj = datetime.strptime(date_remove, '%Y-%m-%d')
        new_line_date = date_remove_obj + relativedelta(days=-1)
        to_depreciate_days = (
            new_line_date -
            datetime.strptime(last_depr_date, '%Y-%m-%d')).days
        to_depreciate_amount = round(
            float(to_depreciate_days) / float(period_number_days) *
            first_to_depreciate_dl.amount, digits)
        
        amount_variation = asset._get_amount_variation(False, last_depr_date)
        residual_value = asset.value_residual - to_depreciate_amount 
        
        # Fiscal
        domain = [('asset_id', '=', asset.id), ('type', '=', 'depreciate'), 
                  ('init_entry', '=', False), ('move_check', '=', False)]
        f_asset_line_obj = self.pool['account.asset.depreciation.line.fiscal']
        f_dl_ids = f_asset_line_obj.search(cr, uid, domain, 
                                           order='line_date asc')
        f_first_to_depreciate_dl = f_asset_line_obj.browse(cr, uid, f_dl_ids[0])    

        first_date = f_first_to_depreciate_dl.line_date
        ''' Omit control. Fiscal won't create an account move
        if date_remove > first_date:
            raise orm.except_orm(
                _('Error!'),
                _("You can't make an early removal if all the depreciation "
                  "lines for previous periods are not posted."))
        '''
        last_depr_date = f_first_to_depreciate_dl.previous_id.line_date
        period_number_days = (
            datetime.strptime(first_date, '%Y-%m-%d') -
            datetime.strptime(last_depr_date, '%Y-%m-%d')).days
        date_remove_obj = datetime.strptime(date_remove, '%Y-%m-%d')
        f_new_line_date = date_remove_obj + relativedelta(days=-1)
        to_depreciate_days = (
            f_new_line_date -
            datetime.strptime(last_depr_date, '%Y-%m-%d')).days
        f_to_depreciate_amount = round(
            float(to_depreciate_days) / float(period_number_days) *
            f_first_to_depreciate_dl.amount, digits)
        f_residual_value = asset._get_residual_value('fiscal', date_remove)
        f_residual_value -= f_to_depreciate_amount
        f_residual_value = round(f_residual_value, digits)
        
        # Step 2: Create line remove 
        # Normal   
        if to_depreciate_amount:
            update_vals = {
                'amount': to_depreciate_amount,
                'line_date': new_line_date
            }
            first_to_depreciate_dl.write(update_vals)
            asset_line_obj.create_move(
                cr, uid, [dl_ids[0]], context=context)
            dl_ids.pop(0)
        asset_line_obj.unlink(cr, uid, dl_ids, context=context)
        # fiscal
        if f_to_depreciate_amount:
            update_vals = {
                'amount': f_to_depreciate_amount,
                'line_date': f_new_line_date
            }
            f_first_to_depreciate_dl.write(update_vals)
            #f_asset_line_obj.create_move(
            #    cr, uid, [f_dl_ids[0]], context=context)
            f_dl_ids.pop(0)
        f_asset_line_obj.unlink(cr, uid, f_dl_ids, context=context)
        
        res.update({
            'residual_value' : residual_value,
            'residual_value_fiscal' : f_residual_value
            })
        return res
    
    def _get_removal_data(self, cr, uid, wiz_data, asset, residual_value,
                          context=None):
        dp_line_obj = self.pool['account.asset.depreciation.line']
        move_lines = []
        partner_id = asset.partner_id and asset.partner_id.id or False
        categ = asset.category_id
        # asset and asset depreciation account reversal
        amount_variation = 0
        domain = [('line_date', '<', wiz_data.date_remove),
                  ('type', '=', 'depreciate')]
        dp_line_ids = dp_line_obj.search(cr, uid, domain, 
                                         order='line_date desc')
        if dp_line_ids:
            previous_dp_line = dp_line_obj.browse(cr, uid, dp_line_ids[0])
            amount_variation = asset._get_amount_variation(
                False, previous_dp_line.line_date)
        depr_amount = asset.asset_value + amount_variation - residual_value
        asset_value = asset.asset_value + amount_variation
        move_line_vals = {
            'name': asset.name,
            'account_id': categ.account_depreciation_id.id,
            'debit': depr_amount > 0 and depr_amount or 0.0,
            'credit': depr_amount < 0 and -depr_amount or 0.0,
            'partner_id': partner_id,
            'asset_id': asset.id
        }
        move_lines.append((0, 0, move_line_vals))
        move_line_vals = {
            'name': asset.name,
            'account_id': categ.account_asset_id.id,
            'debit': asset_value < 0 and -asset_value or 0.0,
            'credit': asset_value > 0 and asset_value or 0.0,
            'partner_id': partner_id,
            'asset_id': asset.id
        }
        move_lines.append((0, 0, move_line_vals))

        if residual_value:
            if wiz_data.posting_regime == 'residual_value':
                move_line_vals = {
                    'name': asset.name,
                    'account_id': wiz_data.account_residual_value_id.id,
                    'analytic_account_id': asset.account_analytic_id.id,
                    'debit': residual_value,
                    'credit': 0.0,
                    'partner_id': partner_id,
                    'asset_id': asset.id
                }
                move_lines.append((0, 0, move_line_vals))
            elif wiz_data.posting_regime == 'gain_loss_on_sale':
                if wiz_data.sale_value:
                    sale_value = wiz_data.sale_value
                    move_line_vals = {
                        'name': asset.name,
                        'account_id': wiz_data.account_sale_id.id,
                        'analytic_account_id': asset.account_analytic_id.id,
                        'debit': sale_value,
                        'credit': 0.0,
                        'partner_id': partner_id,
                        'asset_id': asset.id
                    }
                    move_lines.append((0, 0, move_line_vals))
                balance = wiz_data.sale_value - residual_value
                account_id = (wiz_data.account_plus_value_id.id
                              if balance > 0
                              else wiz_data.account_min_value_id.id)
                move_line_vals = {
                    'name': asset.name,
                    'account_id': account_id,
                    'analytic_account_id': asset.account_analytic_id.id,
                    'debit': balance < 0 and -balance or 0.0,
                    'credit': balance > 0 and balance or 0.0,
                    'partner_id': partner_id,
                    'asset_id': asset.id
                }
                move_lines.append((0, 0, move_line_vals))

        return move_lines
    
    def remove(self, cr, uid, ids, context=None):
        asset_obj = self.pool.get('account.asset.asset')
        asset_line_obj = self.pool['account.asset.depreciation.line']
        f_asset_line_obj = self.pool['account.asset.depreciation.line.fiscal']
        move_obj = self.pool.get('account.move')
        period_obj = self.pool.get('account.period')
        
        asset_id = context['active_id']
        asset = asset_obj.browse(cr, uid, asset_id, context=context)
        asset_ref = asset.code and '%s (ref: %s)' \
            % (asset.name, asset.code) or asset.name
        wiz_data = self.browse(cr, uid, ids[0], context=context)
        # Recompute values with invoice selected
        # Those will be removed from amount variation
        context_save = context.copy()
        self.pool['account.asset.asset'].\
                compute_depreciation_board(cr, uid, [asset_id], context)
        context = context_save.copy()
        # Residual and update last dp line proportionally
        res = self._prepare_early_removal(
            cr, uid, asset, wiz_data.date_remove, context=context)
        residual_value = res.get('residual_value')
        residual_value_fiscal = res.get('residual_value_fiscal')
        
        ctx = dict(context, company_id=asset.company_id.id)
        period_id = wiz_data.period_id and wiz_data.period_id.id or False
        if not period_id:
            ctx.update(account_period_prefer_normal=True)
            period_ids = period_obj.find(
                cr, uid, wiz_data.date_remove, context=ctx)
            period_id = period_ids[0]
        dl_ids = asset_line_obj.search(
            cr, uid,
            [('asset_id', '=', asset.id), ('type', '=', 'depreciate')],
            order='line_date desc')
        last_date = asset_line_obj.browse(cr, uid, dl_ids[0]).line_date
        if wiz_data.date_remove < last_date:
            raise orm.except_orm(
                _('Error!'),
                _("The removal date must be after "
                  "the last depreciation date."))
            
        line_name = asset_obj._get_depreciation_entry_name(
            cr, uid, asset, len(dl_ids) + 1, context=context)
        journal_id = asset.category_id.journal_id.id
        
        # create move
        move_vals = {
            'name': asset.name,
            'date': wiz_data.date_remove,
            'ref': line_name,
            'period_id': period_id,
            'journal_id': journal_id,
            'narration': wiz_data.note,
            }
        move_id = move_obj.create(cr, uid, move_vals, context=context)

        # create asset line
        asset_line_vals = {
            'amount': residual_value,
            'asset_id': asset_id,
            'name': line_name,
            'line_date': wiz_data.date_remove,
            'move_id': move_id,
            'type': 'remove',
        }
        dp_line_id = asset_line_obj.create(cr, uid, asset_line_vals, 
                                           context=context)
        asset.write({'state': 'removed', 'date_remove': wiz_data.date_remove})
        # create asset line Fiscal
        asset_line_vals = {
            'amount': residual_value_fiscal,
            'asset_id': asset_id,
            'name': line_name,
            'line_date': wiz_data.date_remove,
            'move_id': move_id,
            'type': 'remove',
            'normal_line_id': dp_line_id
        }
        f_asset_line_obj.create(cr, uid, asset_line_vals, context=context)
        
        # create move lines
        move_lines = self._get_removal_data(
            cr, uid, wiz_data, asset, residual_value, context=context)
        move_obj.write(cr, uid, [move_id], {'line_id': move_lines},
                       context=dict(context, allow_asset=True))
        
        # Sale moves used for remove asset will chain to remove dp line
        remove_sale_moves =[]
        inv_line_ids = context.get('invoice_line_ids')
        if inv_line_ids:
            for inv_line in self.pool['account.invoice.line'].\
                browse(cr, uid, inv_line_ids):
                    remove_sale_moves.append(inv_line.invoice_id.move_id.id)
        if remove_sale_moves:
            move_obj.write(cr, uid, remove_sale_moves, 
                           {'asset_remove_move_id': move_id})

        return {
            'name': _("Asset '%s' Removal Journal Entry") % asset_ref,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': context,
            'nodestroy': True,
            'domain': [('id', '=', move_id)],
        }
        
