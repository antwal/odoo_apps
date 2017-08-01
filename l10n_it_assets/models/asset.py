# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Abstract (http://www.abstract.it)
#                       Openforce di Camilli Alessandro - www.openforce.it
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import models, fields, api, _
from openerp.exceptions import except_orm, ValidationError
import openerp.addons.decimal_precision as dp
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

class account_asset_category(models.Model):
    _inherit = "account.asset.category"
    
    method = fields.Selection(selection='_get_method', required=True,
        default='linear',
        help="Choose the method to use to compute "
                 "the amount of depreciation lines.\n"
                 "  * Linear: Calculated on basis of: "
                 "Gross Value / Number of Depreciations\n"
                 "  * Degressive: Calculated on basis of: "
                 "Residual Value * Degressive Factor"
                 "  * Degressive-Linear (only for Time Method = Year): "
                 "Degressive becomes linear when the annual linear "
                 "depreciation exceeds the annual degressive depreciation")
    method_time = fields.Selection(selection='_get_method_time', required=True,
        default='percentage',
        help="Choose the method to use to compute the dates and "
                 "number of depreciation lines.\n"
                 "  * Number of Years: Specify the number of years "
                 "for the depreciation.\n")
    method_period = fields.Selection(
        selection=[('year', 'Year')],
                    string='Period Length', required=True, default='year',
                    help="Period length for the depreciation accounting \
                    entries")
    method_percentage = fields.Float(string='Percentage')
    depreciation_property_id = fields.Many2many('account.asset.property',
        'account_asset_category_property_rel', 'category_id', 'property_id',
        string='Category Depreciation Property')
    fiscal_different_method = fields.Boolean(string='Fiscal different Method',
        default=False,
        help="It enable you to specify another Depreciation method for\
            fiscal values" ) 
    fiscal_method = fields.Selection(selection='_get_method', required=True,
        default='linear',
        help="Choose the method to use to compute "
                 "the amount of depreciation lines.\n"
                 "  * Linear: Calculated on basis of: "
                 "Gross Value / Number of Depreciations\n"
                 "  * Degressive: Calculated on basis of: "
                 "Residual Value * Degressive Factor"
                 "  * Degressive-Linear (only for Time Method = Year): "
                 "Degressive becomes linear when the annual linear "
                 "depreciation exceeds the annual degressive depreciation")
    fiscal_method_number = fields.Integer(string='Number of Years',
            help="The number of years needed to depreciate your asset",
            default=5)
    fiscal_method_period = fields.Selection(
        selection=[('year', 'Year')],
                    string='Period Length', required=True, default='year',
                    help="Period length for the depreciation accounting \
                    entries")
    fiscal_method_percentage = fields.Float(string='Percentage')
    fiscal_method_progress_factor = fields.Float(string='Degressive Factor',
        default=0.3)
    fiscal_method_time = fields.Selection(selection='_get_method_time',
        required=True,
        help="Choose the method to use to compute the dates and "
                 "number of depreciation lines.\n"
                 "  * Number of Years: Specify the number of years "
                 "for the depreciation.\n")
    fiscal_prorata = fields.Boolean(string='Prorata Temporis',
        help="Indicates that the first depreciation entry for this asset "
                 "has to be done from the depreciation start date instead of "
                 "the first day of the fiscal year.") 
    
    @api.onchange('fiscal_method_time')
    def change_fiscal_method_time(self):
        if self.fiscal_method_time not in ['year', 'percentage']:
            self.fiscal_prorata = True
            
    @api.onchange('fiscal_different_method')
    def change_fiscal_different_method(self):
        if not self.fiscal_different_method:
            self.fiscal_method = self.method 
            self.fiscal_method_number = self.method_number 
            self.fiscal_method_percentage = self.method_percentage 
            self.fiscal_method_period = self.method_period 
            self.fiscal_method_progress_factor = \
                self.method_progress_factor 
            self.fiscal_method_time = self.method_time 
            self.fiscal_prorata = self.prorata
    
    def _get_method(self, cr, uid, context=None):
        return[
            ('linear', _('Linear')),
        ]
        
    def _get_method_time(self, cr, uid, context=None):
        return [
            ('year', _('Number of Years')),
            ('percentage', _('Percentage')),
            # ('number', _('Number of Depreciations')),
            # ('end', _('Ending Date'))
        ]

class account_asset_asset(models.Model):
    _inherit = "account.asset.asset"
    
    @api.one
    @api.depends('depreciation_line_fiscal_ids.amount', 
                 'depreciation_line_fiscal_ids.init_entry',
                 'purchase_value', 'salvage_value', 'parent_id', 
                 'depreciation_line_ids')
    def _compute_depreciation_fiscal(self):
        cr = self.env.cr
        domain = [('parent_id', 'child_of', [self.id]), ('type', '=', 'normal')]
        childs = self.search(domain)
        child_ids = [x.id for x in childs]
        if child_ids:
            cr.execute(
                "SELECT COALESCE(SUM(amount),0.0) AS amount "
                "FROM account_asset_depreciation_line_fiscal "
                "WHERE asset_id in %s "
                "AND type in ('depreciate','remove') "
                "AND move_check=TRUE ",
                (tuple(child_ids),))
            value_depreciated = cr.fetchone()[0]
        else:
            value_depreciated = 0.0 
        self.fiscal_value_residual = self.fiscal_amount_to_depreciate - \
            value_depreciated
        self.fiscal_value_depreciated = value_depreciated
    
    @api.model
    def _get_amount_variation(self, date_start=None, date_stop=None, 
                              context=None):
        cr = self.env.cr
        uid = self.env.uid
        if not context:
            context = {}
        # Invoice lines with asset remove
        sale_value = 0
        invoice_line_ids = context.get('invoice_line_ids', [])
        if invoice_line_ids:
            domain = [('asset_id', '=', self.id),
                      ('id', 'in', invoice_line_ids)]
            if date_start:
                domain.append(('invoice_id.move_id.date', '>=', date_start))
            if date_stop:
                domain.append(('invoice_id.move_id.date', '<=', date_stop))
            inv_line_ids = self.pool['account.invoice.line'].search(cr, uid, 
                                                                    domain)
            for inv_line in self.pool['account.invoice.line'].browse(
                cr, uid, inv_line_ids):
                sale_value += inv_line.price_subtotal
        # Depreciation lines
        domain = [('asset_id', '=', self.id), ('move_id', '!=', False)]
        dp_line_ids = self.pool['account.asset.depreciation.line']\
            .search(cr, uid, domain)
        dp_line_move_ids = []
        for dp_line in self.pool['account.asset.depreciation.line']\
            .browse(cr, uid, dp_line_ids):
            dp_line_move_ids.append(dp_line.move_id.id)
        # Moves not in depreciation lines are variations
        amount_variation = sale_value   
        domain = [('asset_id', '=', self.id),
                  ('move_id', 'not in', dp_line_move_ids),
                  ('move_id.asset_remove_move_id', '=', False)]
        if date_start:
            domain.append(('move_id.date', '>=', date_start))
        if date_stop:
            domain.append(('move_id.date', '<=', date_stop))
        line_ids = self.pool['account.move.line'].search(cr, uid, domain)
        for line in self.pool['account.move.line'].browse(cr, uid, 
                                                          line_ids):
            if line.debit :
                amount_variation += line.debit
            else:
                amount_variation -= line.credit
        return amount_variation
    
    @api.model
    def _get_residual_value(self, type='fiscal', date_limit=None):
        cr = self.env.cr
        uid = self.env.uid
        digits = self.pool.get('decimal.precision').precision_get(
            cr, uid, 'Account')
        domain = [('asset_id', '=', self.id),
                   ('type', 'in', ['depreciate'])]
        if date_limit:
            domain.append(('line_date', '<=', date_limit))
        if type == 'fiscal':
            dp_line_obj = self.pool['account.asset.depreciation.line.fiscal']
            domain.append(('move_check', '!=', False))
        else:
            dp_line_obj = self.pool['account.asset.depreciation.line']
            domain.append(('move_id', '!=', False))
        # Depreciation lines
        dp_line_ids = dp_line_obj.search(cr, uid, domain)
        residual_value = self.asset_value
        for dp_line in dp_line_obj.browse(cr, uid, dp_line_ids):
            residual_value -= dp_line.amount 
            residual_value += dp_line.amount_variation 
            residual_value = round(residual_value, digits)
        residual_value = round(residual_value, digits) 
        return residual_value
    
    @api.one
    @api.depends('depreciation_line_fiscal_ids.amount_variation')    
    def _compute_variation(self):
        self.value_variation = self._get_amount_variation()
    
    @api.one
    @api.depends('depreciation_line_ids.amount', 
                 'depreciation_line_ids.init_entry', 
                 'depreciation_line_ids.move_id',
                 'purchase_value', 'salvage_value', 'parent_id', 
                 'depreciation_line_ids')    
    def _compute_depreciation(self):
        self.value_residual = self._get_residual_value('normal')
        cr = self.env.cr
        childs = self.search([('parent_id', 'child_of', [self.id]),
                                 ('type', '=', 'normal')])
        if childs:
            child_ids = [child.id for child in childs]
            cr.execute(
                "SELECT COALESCE(SUM(amount),0.0) AS amount "
                "FROM account_asset_depreciation_line "
                "WHERE asset_id in %s "
                "AND type in ('depreciate','remove') "
                "AND (init_entry=TRUE OR move_check=TRUE)",
                (tuple(child_ids),))
            self.value_depreciated = cr.fetchone()[0]
        else:
            self.value_depreciated = 0.0
    
    category_id = fields.Many2one(
        'account.asset.category', 'Asset Category', change_default=True, 
        readonly=True, states={'draft': [('readonly', False)]}, 
        ondelete='restrict')
    value_residual = fields.Float(
        string='Residual Value', store=True, readonly=True,
        compute='_compute_depreciation')
    value_depreciated = fields.Float(
        string='Depreciated Value', store=True, readonly=True,
        compute='_compute_depreciation')
    value_variation = fields.Float(
        string='Value Variations', store=True, readonly=True,
        compute='_compute_variation')
    depreciation_property_id = fields.Many2many('account.asset.property',
        'account_asset_property_rel', 'asset_id', 'property_id',
        string='Asset Depreciation Property',
        readonly=True, states={'draft': [('readonly', False)]})
    depreciation_line_fiscal_ids = fields.One2many(
            comodel_name='account.asset.depreciation.line.fiscal', 
            inverse_name='asset_id',
            string="Depreciation Lines", readonly=True, 
            states={'draft': [('readonly', False)]})
    method_period = fields.Selection(
        selection=[('year', 'Year')],
                    string='Period Length', required=True, default='year',
                    readonly=True, states={'draft': [('readonly', False)]},
                    help="Period length for the depreciation accounting \
                    entries")
    method_percentage = fields.Float(string='Percentage')
    fiscal_amount_to_depreciate = fields.Float(string='Fiscal Amount To Depreciate',
        readonly=True, states={'draft': [('readonly', False)]})
    fiscal_value_residual = fields.Float(
        string='Fiscal Residual Value', store=True, readonly=True,
        compute='_compute_depreciation_fiscal')
    fiscal_value_depreciated = fields.Float(
        string='Fiscal Depreciated Value', store=True, readonly=True,
        compute='_compute_depreciation_fiscal')
    fiscal_different_method = fields.Boolean(string='Fiscal different Method',
        default=False, readonly=True, states={'draft': [('readonly', False)]},
        help="It enable you to specify another Depreciation method for\
            fiscal values" ) 
    fiscal_method = fields.Selection(selection='_get_method', required=True,
        default='linear', readonly=True, 
        states={'draft': [('readonly', False)]},
        help="Choose the method to use to compute "
                 "the amount of depreciation lines.\n"
                 "  * Linear: Calculated on basis of: "
                 "Gross Value / Number of Depreciations\n"
                 "  * Degressive: Calculated on basis of: "
                 "Residual Value * Degressive Factor"
                 "  * Degressive-Linear (only for Time Method = Year): "
                 "Degressive becomes linear when the annual linear "
                 "depreciation exceeds the annual degressive depreciation")
    fiscal_method_number = fields.Integer(string='Number of Years',
            default=5, readonly=True, states={'draft': [('readonly', False)]},
            help="The number of years needed to depreciate your asset",
            )
    fiscal_method_period = fields.Selection(
        selection=[('year', 'Year')],
                    string='Period Length', required=True, default='year',
                    readonly=True, states={'draft': [('readonly', False)]},
                    help="Period length for the depreciation accounting \
                    entries")
    fiscal_method_percentage = fields.Float(string='Percentage')
    fiscal_method_end = fields.Date(string='Ending Date', readonly=True,
        states={'draft': [('readonly', False)]})
    fiscal_method_progress_factor = fields.Float(string='Degressive Factor',
        default=0.3, readonly=True, states={'draft': [('readonly', False)]})
    fiscal_method_time = fields.Selection(selection='_get_method_time',
        readonly=True, states={'draft': [('readonly', False)]},
        help="Choose the method to use to compute the dates and "
                 "number of depreciation lines.\n"
                 "  * Number of Years: Specify the number of years "
                 "for the depreciation.\n")
    fiscal_prorata = fields.Boolean(string='Prorata Temporis',
        readonly=True, states={'draft': [('readonly', False)]},
        help="Indicates that the first depreciation entry for this asset "
                 "has to be done from the depreciation start date instead of "
                 "the first day of the fiscal year.") 
    
    @api.onchange('fiscal_different_method')
    def change_fiscal_different_method(self):
        if not self.fiscal_different_method:
            self.fiscal_method = self.method 
            self.fiscal_method_number = self.method_number 
            self.fiscal_method_period = self.method_period 
            self.fiscal_method_progress_factor = \
                self.method_progress_factor 
            self.fiscal_method_time = self.method_time 
            self.fiscal_prorata = self.prorata
    
    def create(self, cr, uid, vals, context=None):
        '''
        Create init line depreciation fiscal 
        '''
        if not context:
            context = {}
        if vals.get('method_time') not in ['year','percentage'] \
                and not vals.get('prorata'):
            vals['prorata'] = True
        asset_id = super(account_asset_asset, self).create(
            cr, uid, vals, context=context)
        asset = self.browse(cr, uid, asset_id, context)
        if asset.type == 'normal':
            # Fiscal amount to depreciate from property
            amount_to_depreciate = asset.asset_value
            for property in asset.category_id.depreciation_property_id:
                if property.fiscal_coeff_asset_depreciable:
                    amount_to_depreciate = amount_to_depreciate * \
                        property.fiscal_coeff_asset_depreciable
            # Fiscal e other values from category
            vals = {
                'depreciation_property_id': [(6, 0, \
                    [x.id for x in \
                     asset.category_id.depreciation_property_id])],
                'method_percentage' : asset.category_id.method_percentage,
                'fiscal_amount_to_depreciate' : amount_to_depreciate,
                'fiscal_different_method' : \
                    asset.category_id.fiscal_different_method,
                'fiscal_method' : asset.category_id.fiscal_method,
                'fiscal_method_number' : asset.category_id.fiscal_method_number,
                'fiscal_method_period' : asset.category_id.fiscal_method_period,
                'fiscal_method_percentage' : \
                    asset.category_id.fiscal_method_percentage,
                'fiscal_method_progress_factor' : \
                    asset.category_id.fiscal_method_progress_factor,
                'fiscal_method_time' : asset.category_id.fiscal_method_time,
                'fiscal_prorata' : asset.category_id.fiscal_prorata,
                }
            self.write(cr, uid, [asset_id], vals)
            # create first asset line
            asset_line_obj = self.pool['account.asset.depreciation.line.fiscal']
            line_name = self._get_depreciation_entry_name(
                cr, uid, asset, 0, context=context)
            asset_line_vals = {
                'amount': amount_to_depreciate,
                'asset_id': asset_id,
                'name': line_name,
                'line_date': asset.date_start,
                'init_entry': True,
                'type': 'create',
            }
            asset_line_id = asset_line_obj.create(
                cr, uid, asset_line_vals, context=context)
        return asset_id
    
    @api.v7 
    def remove(self, cr, uid, ids, context=None):
        for asset in self.browse(cr, uid, ids, context):
            ctx = dict(context, active_ids=ids, active_id=ids[0])
            if asset.value_residual:
                ctx.update({'early_removal': True})
        return {
            'name': _("Select Moves for Asset Removal entries"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.asset.remove.select',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'nodestroy': True,
        }

    @api.v7
    def onchange_category_id(self, cr, uid, ids, category_id, context=None):
        res = super(account_asset_asset, self).onchange_category_id(
            cr, uid, ids, category_id, context)
        
        asset_categ_obj = self.pool.get('account.asset.category')
        if category_id:
            category = asset_categ_obj.browse(
                cr, uid, category_id, context=context)
            res['value']['depreciation_property_id'] =\
                 [x.id for x in category.depreciation_property_id]
 
        return res
    
    @api.v7
    def _get_fy_duration_factor(self, cr, uid, entry,
                                asset, firstyear, context=None):
        """
        localization: override this method to change the logic used to
        calculate the impact of extended/shortened fiscal years
        """
        if context.get('fiscal_methods'):
            asset_prorata = asset.fiscal_prorata
        else:
            asset_prorata = asset.prorata
            
        duration_factor = 1.0
        fy_id = entry['fy_id']
        if asset_prorata:
            if firstyear:
                depreciation_date_start = datetime.strptime(
                    asset.date_start, '%Y-%m-%d')
                fy_date_stop = entry['date_stop']
                first_fy_asset_days = \
                    (fy_date_stop - depreciation_date_start).days + 1
                if fy_id:
                    first_fy_duration = self._get_fy_duration(
                        cr, uid, fy_id, option='days')
                    first_fy_year_factor = self._get_fy_duration(
                        cr, uid, fy_id, option='years')
                    duration_factor = \
                        float(first_fy_asset_days) / first_fy_duration \
                        * first_fy_year_factor
                else:
                    first_fy_duration = \
                        calendar.isleap(entry['date_start'].year) \
                        and 366 or 365
                    duration_factor = \
                        float(first_fy_asset_days) / first_fy_duration
            elif fy_id:
                duration_factor = self._get_fy_duration(
                    cr, uid, fy_id, option='years')
        elif fy_id:
            fy_months = self._get_fy_duration(
                cr, uid, fy_id, option='months')
            duration_factor = float(fy_months) / 12
        return duration_factor
    
    @api.v7
    def _get_depreciation_start_date(self, cr, uid, asset, fy, context=None):
        """
        In case of 'Linear': the first month is counted as a full month
        if the fiscal year starts in the middle of a month.
        """
        if context.get('fiscal_methods'):
            asset_prorata = asset.fiscal_prorata
        else:
            asset_prorata = asset.prorata
        
        if asset_prorata:
            depreciation_start_date = datetime.strptime(
                asset.date_start, '%Y-%m-%d')
        else:
            fy_date_start = datetime.strptime(fy.date_start, '%Y-%m-%d')
            depreciation_start_date = datetime(
                fy_date_start.year, fy_date_start.month, 1)
        return depreciation_start_date

    @api.v7
    def _get_depreciation_stop_date(self, cr, uid, asset,
                                    depreciation_start_date, context=None):
        if context.get('fiscal_methods'):
            asset_method_number = asset.fiscal_method_number
            asset_method_percentage = asset.fiscal_method_percentage
            asset_method_time = asset.fiscal_method_time
            asset_method_end = asset.fiscal_method_end
        else:
            asset_method_number = asset.method_number
            asset_method_percentage = asset.method_percentage
            asset_method_time = asset.method_time
            asset_method_end = asset.method_end
            
        if asset_method_time == 'year':
            depreciation_stop_date = depreciation_start_date + \
                relativedelta(years=asset_method_number, days=-1)
        elif asset_method_time == 'percentage':
            # The property with percentage: the lenght may be changed
            years_number = 0
            count = 0
            i = 0
            while count < 100:
                i += 1
                property_coeff = 1
                for property in asset.depreciation_property_id:
                    l_last = int(100 / asset_method_percentage + .5)
                    role = property._compute_role(1, i, l_last)
                    if role and role['coeff']:
                        if context.get('fiscal_methods') and \
                                role['fiscal_depreciation']:
                            property_coeff = role['coeff']
                        elif not context.get('fiscal_methods') and \
                                role['normal_depreciation']:
                            property_coeff = role['coeff']
                count += round((asset_method_percentage * property_coeff), )
                years_number += 1
            depreciation_stop_date = depreciation_start_date + \
                relativedelta(years=years_number, days=-1)
            
        elif asset_method_time == 'number':
            if asset_method_period == 'month':
                depreciation_stop_date = depreciation_start_date + \
                    relativedelta(months=asset_method_number, days=-1)
            elif asset_method_period == 'quarter':
                depreciation_stop_date = depreciation_start_date + \
                    relativedelta(months=asset_method_number * 3, days=-1)
            elif asset.method_period == 'year':
                depreciation_stop_date = depreciation_start_date + \
                    relativedelta(years=asset_method_number, days=-1)
        elif asset_method_time == 'end':
            depreciation_stop_date = datetime.strptime(
                asset_method_end, '%Y-%m-%d')
        return depreciation_stop_date
    
    @api.v7
    def _compute_year_amount(self, cr, uid, asset, amount_to_depr,
                             residual_amount, context=None):
        """
        Localization: override this method to change the degressive-linear
        calculation logic according to local legislation.
        """
        fiscal_method = context.get('fiscal_methods', False)
        if fiscal_method:
            asset_method = asset.fiscal_method
            asset_method_number = asset.fiscal_method_number
            asset_method_time = asset.fiscal_method_time
            asset_method_percentage = asset.fiscal_method_percentage
            asset_method_end = asset.fiscal_method_end
            asset_method_period = asset.fiscal_method_period
            asset_method_progress_factor = asset.fiscal_method_progress_factor
        else:
            asset_method = asset.method
            asset_method_number = asset.method_number
            asset_method_time = asset.method_time
            asset_method_percentage = asset.method_percentage
            asset_method_end = asset.method_end
            asset_method_period = asset.method_period
            asset_method_progress_factor = asset.method_progress_factor
        # For variation recompute with remaining numbers
        if context.get('variation_asset_method_number'):
            asset_method_number = context.get('variation_asset_method_number')
        if context.get('variation_amount_to_depr'):
            amount_to_depr = context.get('variation_amount_to_depr')
        
        if asset_method_time == 'year':
            divisor = asset_method_number
        elif asset_method_time == 'percentage':
            divisor = 100 / asset_method_percentage
        elif asset_method_time == 'number':
            if asset_method_period == 'month':
                divisor = asset_method_number / 12.0
            elif asset_method_period == 'quarter':
                divisor = asset_method_number * 3 / 12.0
            elif asset_method_period == 'year':
                divisor = asset_method_number
        elif asset_method_time == 'end':
            duration = \
                (datetime.strptime(asset_method_end, '%Y-%m-%d') -
                 datetime.strptime(asset.date_start, '%Y-%m-%d')).days + 1
            divisor = duration / 365.0
        year_amount_linear = amount_to_depr / divisor
        # Apply property
        line_competence = context.get('depreciation_line_number')
        line_max = context.get('depreciation_line_max')
        for property in asset.depreciation_property_id:
            if (fiscal_method and property.fiscal_depreciation)\
                or (not fiscal_method and property.normal_depreciation):
                role = property._compute_role(year_amount_linear or 0, 
                                              line_competence,
                                              line_max)
                if role :
                    year_amount_linear = role['amount']
        
        if asset_method == 'linear':
            return year_amount_linear
        year_amount_degressive = residual_amount * \
            asset_method_progress_factor
        if asset_method == 'degressive':
            return year_amount_degressive
        if asset_method == 'degr-linear':
            if year_amount_linear > year_amount_degressive:
                return year_amount_linear
            else:
                return year_amount_degressive
        else:
            raise except_orm(
                _('Programming Error!'),
                _("Illegal value %s in asset.method.") % asset_method)
            
    @api.v7
    def _normalize_depreciation_table(self, cr, uid, asset, table, 
                                      context=None):
        # Date with move of variation ( Not delete line if exists)
        domain = [('asset_id', '=', asset.id)]
        line_ids = self.pool['account.move.line'].search(cr, uid, domain, 
                                                         order='date desc')
        date_last_account_move = False
        if line_ids:
            acc_move_line = self.pool['account.move.line'].browse(cr, uid, 
                                                                  line_ids[0])
            date_last_account_move = datetime.strptime(acc_move_line.date, 
                                                       '%Y-%m-%d')
        return table
   
    @api.v7
    def _compute_depreciation_table(self, cr, uid, asset, context=None):
        if not context:
            context = {}
            
        table = []
        if not asset.method_number:
            return table
        
        context['company_id'] = asset.company_id.id
        fy_obj = self.pool.get('account.fiscalyear')
        init_flag = False
        try:
            fy_id = fy_obj.find(cr, uid, asset.date_start, context=context)
            fy = fy_obj.browse(cr, uid, fy_id)
            if fy.state == 'done':
                init_flag = True
            fy_date_start = datetime.strptime(fy.date_start, '%Y-%m-%d')
            fy_date_stop = datetime.strptime(fy.date_stop, '%Y-%m-%d')
        except:
            # The following logic is used when no fiscalyear
            # is defined for the asset start date:
            # - We lookup the first fiscal year defined in the system
            # - The 'undefined' fiscal years are assumed to be years
            # with a duration equals to calendar year
            cr.execute(
                "SELECT id, date_start, date_stop "
                "FROM account_fiscalyear ORDER BY date_stop ASC LIMIT 1")
            first_fy = cr.dictfetchone()
            first_fy_date_start = datetime.strptime(
                first_fy['date_start'], '%Y-%m-%d')
            asset_date_start = datetime.strptime(asset.date_start, '%Y-%m-%d')
            fy_date_start = first_fy_date_start
            if asset_date_start > fy_date_start:
                asset_ref = asset.code and '%s (ref: %s)' \
                    % (asset.name, asset.code) or asset.name
                raise except_orm(
                    _('Error!'),
                    _("You cannot compute a depreciation table for an asset "
                      "starting in an undefined future fiscal year."
                      "\nPlease correct the start date for asset '%s'.")
                    % asset_ref)
            while asset_date_start < fy_date_start:
                fy_date_start = fy_date_start - relativedelta(years=1)
            fy_date_stop = fy_date_start + relativedelta(years=1, days=-1)
            fy_id = False
            fy = dummy_fy(
                date_start=fy_date_start.strftime('%Y-%m-%d'),
                date_stop=fy_date_stop.strftime('%Y-%m-%d'),
                id=False,
                state='done',
                dummy=True)
            init_flag = True
        
        depreciation_start_date = self._get_depreciation_start_date(
            cr, uid, asset, fy, context=context)
        depreciation_stop_date = self._get_depreciation_stop_date(
            cr, uid, asset, depreciation_start_date, context=context)
        while fy_date_start <= depreciation_stop_date:
            table.append({
                'fy_id': fy_id,
                'date_start': fy_date_start,
                'date_stop': fy_date_stop,
                'init': init_flag})
            fy_date_start = fy_date_stop + relativedelta(days=1)
            try:
                fy_id = fy_obj.find(cr, uid, fy_date_start, context=context)
                init_flag = False
            except:
                fy_id = False
            if fy_id:
                fy = fy_obj.browse(cr, uid, fy_id)
                if fy.state == 'done':
                    init_flag = True
                fy_date_stop = datetime.strptime(fy.date_stop, '%Y-%m-%d')
            else:
                fy_date_stop = fy_date_stop + relativedelta(years=1)

        digits = self.pool.get('decimal.precision').precision_get(
            cr, uid, 'Account')
        
        if context.get('fiscal_methods'):
            amount_to_depr = residual_amount = \
                asset.fiscal_amount_to_depreciate
        else:
            amount_to_depr = residual_amount = asset.asset_value
        
        # step 1: compute variation and value of asset 
        # ... depreciation lines to exclude
        domain = [('asset_id', '=', asset.id), ('move_id', '!=', False)]
        dp_line_ids = self.pool['account.asset.depreciation.line']\
            .search(cr, uid, domain)
        dp_line_move_ids = []
        for dp_line in self.pool['account.asset.depreciation.line']\
            .browse(cr, uid, dp_line_ids):
            dp_line_move_ids.append(dp_line.move_id.id)
        i_max = len(table) - 1
        for i, entry in enumerate(table):
            entry['amount_variation'] = asset._get_amount_variation(
                entry['date_start'], entry['date_stop'], context)

        # step 2: calculate depreciation amount per fiscal year
        fy_residual_amount = residual_amount
        #i_max = len(table) - 1
        i_max = len(table)
        asset_sign = asset.asset_value >= 0 and 1 or -1
        asset_with_variation = False
        for i, entry in enumerate(table):
            # Compute depreciation with amount variation
            if entry['amount_variation']:
                asset_with_variation
            fy_residual_amount += entry['amount_variation']
            # In case of sell
            if fy_residual_amount < 0:
                fy_residual_amount = 0
            amount_to_depr += entry['amount_variation']
            if amount_to_depr < 0:
                amount_to_depr = 0
            context.update({
                'variation_asset_method_number' : len(table),
                #'variation_fy_residual_amount' : fy_residual_amount,
                'variation_amount_to_depr' : amount_to_depr,
                'depreciation_line_number' : i + 1,
                'depreciation_line_max' : i_max + 1
                })
            year_amount = self._compute_year_amount(
                cr, uid, asset, amount_to_depr,
                fy_residual_amount, context=context)
            if asset.method_period == 'year':
                period_amount = year_amount
            elif asset.method_period == 'quarter':
                period_amount = year_amount/4
            elif asset.method_period == 'month':
                period_amount = year_amount/12
            if i == i_max:
                fy_amount = fy_residual_amount
            else:
                firstyear = i == 0 and True or False
                fy_factor = self._get_fy_duration_factor(
                    cr, uid, entry, asset, firstyear, context=context)
                fy_amount = year_amount * fy_factor
            if asset_sign * (fy_amount - fy_residual_amount) > 0:
                fy_amount = fy_residual_amount
            period_amount = round(period_amount, digits)
            fy_amount = round(fy_amount, digits)
            entry.update({
                'period_amount': period_amount,
                'fy_amount': fy_amount,
                'asset_historical_value': amount_to_depr,
            })
            fy_residual_amount -= fy_amount
        i_max = i
        ##table = table[:i_max + 1]
        
        # step 3: spread depreciation amount per fiscal year
        # over the depreciation periods
        fy_residual_amount = residual_amount
        line_date = False
        for i, entry in enumerate(table):
            residual_amount += entry['amount_variation']
            vals = {
                'residual_amount': entry['asset_historical_value'],
                'fy_amount': entry['fy_amount'],
                'period_amount': entry['period_amount'],
                'date_stop': entry['date_stop'],
                'line_id': i,
            }
            context.update({'spread_params': vals})
            lines = self._spread_depreciation_lines(cr, uid, asset, context)
            for line in lines:
                line['amount_variation'] = entry['amount_variation']
                line['depreciated_value'] = entry['asset_historical_value'] \
                    - residual_amount
                residual_amount -= line['amount']
                residual_amount = round(residual_amount, digits)
                line['remaining_value'] = residual_amount
            entry['lines'] = lines
        
        # step 4: Remove lines without amounts
        table = self._normalize_depreciation_table(cr, uid, asset, table, 
                                                   context)
         
        return table
  
    def _spread_depreciation_lines(self, cr, uid, asset, context=None):
        '''
        Spread only amount value second method
        '''
        if not context:
            return False
        
        if context.get('fiscal_methods'):
            asset_method_period = asset.fiscal_method_period
        else:
            asset_method_period = asset.method_period
        
        spread_params = context.get('spread_params')
        
        fy_residual_amount = spread_params['residual_amount']
        period_amount = spread_params['period_amount']
        fy_amount = spread_params['fy_amount']
        
        asset_sign = asset.asset_value >= 0 and 1 or -1
        period_duration = (asset_method_period == 'year' and 12) \
            or (asset_method_period == 'quarter' and 3) or 1
        if period_duration == 12:
            if asset_sign * (fy_amount - fy_residual_amount) > 0:
                fy_amount = fy_residual_amount
            lines = [{'date': spread_params['date_stop'], 'amount': fy_amount}]
            fy_residual_amount -= fy_amount
        elif period_duration in [1, 3]:
            lines = []
            fy_amount_check = 0.0
            if not line_date:
                if period_duration == 3:
                    m = [x for x in [3, 6, 9, 12]
                         if x >= depreciation_start_date.month][0]
                    line_date = depreciation_start_date + \
                        relativedelta(month=m, day=31)
                else:
                    line_date = depreciation_start_date + \
                        relativedelta(months=0, day=31)
            while line_date <= \
                    min(entry['date_stop'], depreciation_stop_date) and \
                    asset_sign * (fy_residual_amount - period_amount) > 0:
                lines.append({'date': line_date, 'amount': period_amount})
                fy_residual_amount -= period_amount
                fy_amount_check += period_amount
                line_date = line_date + \
                    relativedelta(months=period_duration, day=31)
            if i == i_max and \
                    (not lines or
                     depreciation_stop_date > lines[-1]['date']):
                # last year, last entry
                period_amount = fy_residual_amount
                lines.append({'date': line_date, 'amount': period_amount})
                fy_amount_check += period_amount
            if round(fy_amount_check - fy_amount, digits) != 0:
                # handle rounding and extended/shortened
                # fiscal year deviations
                diff = fy_amount_check - fy_amount
                fy_residual_amount += diff
                if i == 0:  # first year: deviation in first period
                    lines[0]['amount'] = period_amount - diff
                else:       # other years: deviation in last period
                    lines[-1]['amount'] = period_amount - diff
        else:
            raise except_orm(
                _('Programming Error!'),
                _("Illegal value %s in asset.method_period.")
                % asset_method_period)
        return lines
    
    @api.v7
    def compute_depreciation_board(self, cr, uid, ids, context=None):
        self.compute_depreciation_board_fiscal(cr, uid, ids, context)
        
        if not context:
            context = {}
        depreciation_lin_obj = self.pool.get(
            'account.asset.depreciation.line')
        digits = self.pool.get('decimal.precision').precision_get(
            cr, uid, 'Account')
        # setting context for compute relative methods
        context.update({'fiscal_methods': False})

        for asset in self.browse(cr, uid, ids, context=context):
            if asset.value_residual == 0.0:
                continue
            domain = [
                ('asset_id', '=', asset.id),
                ('type', '=', 'depreciate'),
                '|', ('move_check', '=', True), ('init_entry', '=', True)]
            posted_depreciation_line_ids = depreciation_lin_obj.search(
                cr, uid, domain, order='line_date desc')
            if (len(posted_depreciation_line_ids) > 0):
                last_depreciation_line = depreciation_lin_obj.browse(
                    cr, uid, posted_depreciation_line_ids[0], context=context)
            else:
                last_depreciation_line = False
            domain = [
                ('asset_id', '=', asset.id),
                ('type', '=', 'depreciate'),
                ('move_id', '=', False),
                ('init_entry', '=', False)]
            old_depreciation_line_ids = depreciation_lin_obj.search(
                cr, uid, domain)
            if old_depreciation_line_ids:
                depreciation_lin_obj.unlink(
                    cr, uid, old_depreciation_line_ids, context=context)
            context['company_id'] = asset.company_id.id

            table = self._compute_depreciation_table(
                cr, uid, asset, context=context)
            if not table:
                continue
            # group lines prior to depreciation start period
            depreciation_start_date = datetime.strptime(
                asset.date_start, '%Y-%m-%d')
            lines = table[0]['lines']
            lines1 = []
            lines2 = []
            flag = lines[0]['date'] < depreciation_start_date
            for line in lines:
                if flag:
                    lines1.append(line)
                    if line['date'] >= depreciation_start_date:
                        flag = False
                else:
                    lines2.append(line)
            if lines1:
                def group_lines(x, y):
                    y.update({'amount': x['amount'] + y['amount']})
                    y.update({'amount_variation': x['amount_variation'] \
                              + y['amount_variation']})
                    return y
                lines1 = [reduce(group_lines, lines1)]
                lines1[0]['depreciated_value'] = 0.0
            table[0]['lines'] = lines1 + lines2
            
            # check table with posted entries and
            # recompute in case of deviation
            if (len(posted_depreciation_line_ids) > 0):
                last_depreciation_date = datetime.strptime(
                    last_depreciation_line.line_date, '%Y-%m-%d')
                last_date_in_table = table[-1]['lines'][-1]['date']
                if last_date_in_table <= last_depreciation_date:
                    raise except_orm(
                        _('Error!'),
                        _("The duration of the asset conflicts with the "
                          "posted depreciation table entry dates."))

                for table_i, entry in enumerate(table):
                    residual_amount_table = \
                        entry['lines'][-1]['remaining_value']
                    if entry['date_start'] <= last_depreciation_date \
                            <= entry['date_stop']:
                        break
                if entry['date_stop'] == last_depreciation_date:
                    table_i += 1
                    line_i = 0
                else:
                    entry = table[table_i]
                    date_min = entry['date_start']
                    for line_i, line in enumerate(entry['lines']):
                        residual_amount_table = line['remaining_value']
                        if date_min <= last_depreciation_date <= line['date']:
                            break
                        date_min = line['date']
                    if line['date'] == last_depreciation_date:
                        line_i += 1
                table_i_start = table_i
                line_i_start = line_i

                # check if residual value corresponds with table
                # and adjust table when needed
                cr.execute(
                    "SELECT COALESCE(SUM(amount), 0.0), "
                    "    COALESCE(SUM(amount_variation), 0.0) "
                    "FROM account_asset_depreciation_line "
                    "WHERE id IN %s",
                    (tuple(posted_depreciation_line_ids),))
                res = cr.fetchone()
                depreciated_value = res[0]
                amount_variation = res[1]
                residual_amount = asset.asset_value + amount_variation \
                    - depreciated_value
                amount_diff = round(
                    residual_amount_table - residual_amount, digits)
                if amount_diff:
                    entry = table[table_i_start]
                    if entry['fy_id']:
                        cr.execute(
                            "SELECT COALESCE(SUM(amount), 0.0) "
                            "FROM account_asset_depreciation_line "
                            "WHERE id in %s "
                            "      AND line_date >= %s and line_date <= %s",
                            (tuple(posted_depreciation_line_ids),
                             entry['date_start'],
                             entry['date_stop']))
                        res = cr.fetchone()
                        fy_amount_check = res[0]
                    else:
                        fy_amount_check = 0.0
                    lines = entry['lines']
                    for line in lines[line_i_start:-1]:
                        line['depreciated_value'] = depreciated_value
                        depreciated_value += line['amount']
                        fy_amount_check += line['amount']
                        residual_amount -= line['amount']
                        line['remaining_value'] = residual_amount
                    lines[-1]['depreciated_value'] = depreciated_value
                    lines[-1]['amount'] = entry['fy_amount'] - fy_amount_check

            else:
                table_i_start = 0
                line_i_start = 0

            seq = len(posted_depreciation_line_ids)
            depr_line_id = last_depreciation_line and last_depreciation_line.id
            last_date = table[-1]['lines'][-1]['date']
            for entry in table[table_i_start:]:
                for line in entry['lines'][line_i_start:]:
                    seq += 1
                    name = self._get_depreciation_entry_name(
                        cr, uid, asset, seq, context=context)
                    if line['date'] == last_date:
                        # ensure that the last entry of the table always
                        # depreciates the remaining value
                        cr.execute(
                            "SELECT COALESCE(SUM(amount), 0.0), "
                            "    COALESCE(SUM(amount_variation), 0.0) "
                            "FROM account_asset_depreciation_line "
                            "WHERE type = 'depreciate' AND line_date < %s "
                            "AND asset_id = %s ",
                            (last_date, asset.id))
                        res = cr.fetchone()
                        amount = (asset.asset_value + res[1]) - res[0]
                        # In case of sell
                        if amount < 0:
                            amount = 0
                    else:
                        amount = line['amount']
                    vals = {
                        'asset_historical_value': \
                            entry['asset_historical_value'],
                        'previous_id': depr_line_id,
                        'amount': amount,
                        'amount_variation': line['amount_variation'],
                        'asset_id': asset.id,
                        'name': name,
                        'line_date': line['date'].strftime('%Y-%m-%d'),
                        'init_entry': entry['init'],
                    }
                    depr_line_id = depreciation_lin_obj.create(
                        cr, uid, vals, context=context)
                line_i_start = 0
                
        return True
    
    @api.v7
    def compute_depreciation_board_fiscal(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        depreciation_lin_obj = self.pool.get(
            'account.asset.depreciation.line.fiscal')
        digits = self.pool.get('decimal.precision').precision_get(
            cr, uid, 'Account')
        # setting context for compute relative methods
        context.update({'fiscal_methods': True})
        
        for asset in self.browse(cr, uid, ids, context=context):
            if asset.value_residual == 0.0:
                continue
            domain = [
                ('asset_id', '=', asset.id),
                ('type', '=', 'depreciate'),
                ('init_entry', '=', True)]
            posted_depreciation_line_ids = depreciation_lin_obj.search(
                cr, uid, domain, order='line_date desc')
            if (len(posted_depreciation_line_ids) > 0):
                last_depreciation_line = depreciation_lin_obj.browse(
                    cr, uid, posted_depreciation_line_ids[0], context=context)
            else:
                last_depreciation_line = False
            domain = [
                ('asset_id', '=', asset.id),
                ('type', '=', 'depreciate'),
                ('init_entry', '=', False)]
            old_depreciation_line_ids = depreciation_lin_obj.search(
                cr, uid, domain)
            if old_depreciation_line_ids:
                depreciation_lin_obj.unlink(
                    cr, uid, old_depreciation_line_ids, context=context)
            context['company_id'] = asset.company_id.id
            
            table = self._compute_depreciation_table(
                cr, uid, asset, context=context)
            if not table:
                continue
            
            # group lines prior to depreciation start period
            depreciation_start_date = datetime.strptime(
                asset.date_start, '%Y-%m-%d')
            lines = table[0]['lines']
            lines1 = []
            lines2 = []
            flag = lines[0]['date'] < depreciation_start_date
            for line in lines:
                if flag:
                    lines1.append(line)
                    if line['date'] >= depreciation_start_date:
                        flag = False
                else:
                    lines2.append(line)
            if lines1:
                def group_lines(x, y):
                    y.update({'amount': x['amount'] + y['amount']})
                    y.update({'amount_variation': x['amount_variation'] \
                              + y['amount_variation']})
                    return y
                lines1 = [reduce(group_lines, lines1)]
                lines1[0]['depreciated_value'] = 0.0
            table[0]['lines'] = lines1 + lines2
            
            # check table with posted entries and
            # recompute in case of deviation
            if (len(posted_depreciation_line_ids) > 0):
                last_depreciation_date = datetime.strptime(
                    last_depreciation_line.line_date, '%Y-%m-%d')
                last_date_in_table = table[-1]['lines'][-1]['date']
                if last_date_in_table <= last_depreciation_date:
                    raise except_orm(
                        _('Error!'),
                        _("The duration of the asset conflicts with the "
                          "posted depreciation table entry dates."))

                for table_i, entry in enumerate(table):
                    residual_amount_table = \
                        entry['lines'][-1]['remaining_value']
                    if entry['date_start'] <= last_depreciation_date \
                            <= entry['date_stop']:
                        break
                if entry['date_stop'] == last_depreciation_date:
                    table_i += 1
                    line_i = 0
                else:
                    entry = table[table_i]
                    date_min = entry['date_start']
                    for line_i, line in enumerate(entry['lines']):
                        residual_amount_table = line['remaining_value']
                        if date_min <= last_depreciation_date <= line['date']:
                            break
                        date_min = line['date']
                    if line['date'] == last_depreciation_date:
                        line_i += 1
                table_i_start = table_i
                line_i_start = line_i

                # check if residual value corresponds with table
                # and adjust table when needed
                cr.execute(
                    "SELECT COALESCE(SUM(amount), 0.0) "
                    "FROM account_asset_depreciation_line_fiscal "
                    "WHERE id IN %s",
                    (tuple(posted_depreciation_line_ids),))
                res = cr.fetchone()
                depreciated_value = res[0]
                residual_amount = asset.asset_value - depreciated_value
                amount_diff = round(
                    residual_amount_table - residual_amount, digits)
                if amount_diff:
                    entry = table[table_i_start]
                    if entry['fy_id']:
                        cr.execute(
                            "SELECT COALESCE(SUM(amount), 0.0) "
                            "FROM account_asset_depreciation_line_fiscal "
                            "WHERE id in %s "
                            "      AND line_date >= %s and line_date <= %s",
                            (tuple(posted_depreciation_line_ids),
                             entry['date_start'],
                             entry['date_stop']))
                        res = cr.fetchone()
                        fy_amount_check = res[0]
                    else:
                        fy_amount_check = 0.0
                    lines = entry['lines']
                    for line in lines[line_i_start:-1]:
                        line['depreciated_value'] = depreciated_value
                        depreciated_value += line['amount']
                        fy_amount_check += line['amount']
                        residual_amount -= line['amount']
                        line['remaining_value'] = residual_amount
                    lines[-1]['depreciated_value'] = depreciated_value
                    lines[-1]['amount'] = entry['fy_amount'] - fy_amount_check

            else:
                table_i_start = 0
                line_i_start = 0
            if context.get('fiscal_methods'):
                amount_to_depr = asset.fiscal_amount_to_depreciate
            else:
                amount_to_depr = asset.asset_value
            seq = len(posted_depreciation_line_ids)
            depr_line_id = last_depreciation_line and last_depreciation_line.id
            last_date = table[-1]['lines'][-1]['date']
            for entry in table[table_i_start:]:
                for line in entry['lines'][line_i_start:]:
                    seq += 1
                    name = self._get_depreciation_entry_name(
                        cr, uid, asset, seq, context=context)
                    if line['date'] == last_date:
                        # ensure that the last entry of the table always
                        # depreciates the remaining value
                        cr.execute(
                            "SELECT COALESCE(SUM(amount), 0.0), "
                            "    COALESCE(SUM(amount_variation), 0.0) "
                            "FROM account_asset_depreciation_line_fiscal "
                            "WHERE type = 'depreciate' AND line_date < %s "
                            "AND asset_id = %s ",
                            (last_date, asset.id))
                        res = cr.fetchone()
                        amount = (amount_to_depr + res[1]) - res[0]
                    else:
                        amount = line['amount']
                    vals = {
                        'asset_historical_value': \
                            entry['asset_historical_value'],
                        'previous_id': depr_line_id,
                        'amount': amount,
                        'amount_variation': line['amount_variation'],
                        'asset_id': asset.id,
                        'name': name,
                        'line_date': line['date'].strftime('%Y-%m-%d'),
                        'init_entry': entry['init'],
                    }
                    depr_line_id = depreciation_lin_obj.create(
                        cr, uid, vals, context=context)
                line_i_start = 0

        return True
    
    
class account_asset_depreciation_line(models.Model):
    _inherit = "account.asset.depreciation.line"
    
    amount = fields.Float('Amount', digits=dp.get_precision('Account'), 
                          required=True)
    amount_variation = fields.Float('Amount Variation', 
                                    digits=dp.get_precision('Account'))
    remaining_value = fields.Float('Next Period Depreciation', 
                                   compute='_compute', readonly=True,
                                   digits=dp.get_precision('Account'))
    depreciated_value = fields.Float('Amount Already Depreciated', 
                                   compute='_compute', readonly=True,
                                   digits=dp.get_precision('Account'))
    asset_historical_value = fields.Float(string='Asset Historical Value', 
                               digits=dp.get_precision('Account'), 
                               readonly=True)
    accumulated_depreciation = fields.Float('Accumulated Depreciation', 
                                     compute='_compute', store=True)
    sale_remove_move_ids = fields.One2many('account.move', 
                                           'asset_remove_move_id', 
                                           string='Sale remove move')
    fiscal_line_ids = fields.One2many('account.asset.depreciation.line.fiscal',
                                      'normal_line_id',
                                      string='Fiscal lines')
    amount_remove_move = fields.Float('Amount remove move', readonly=True,
        help="Contains amount of sale invoice line for remove asset")
    
    @api.one
    @api.depends('amount')
    def _compute(self):
        digits = self.env['decimal.precision'].precision_get('Account')
        asset_value = self[0].asset_id.asset_value
        domain = [('asset_id', '=', self.asset_id.id),
                  ('type', '=', 'depreciate')]
        dlines = self.search(domain, order='line_date')
        for i, dl in enumerate(dlines):
            if i == 0:
                depreciated_value = dl.previous_id and \
                    (asset_value - dl.previous_id.remaining_value) or 0.0
                remaining_value = dl.asset_historical_value - depreciated_value\
                     - dl.amount
                accumulated_depreciation = depreciated_value + dl.amount
            else:
                remaining_value -= dl.amount
                remaining_value += dl.amount_variation
                round(remaining_value, digits)
                depreciated_value += dl.previous_id.amount
                accumulated_depreciation = depreciated_value + dl.amount
            
            dl.depreciated_value = depreciated_value
            dl.remaining_value = remaining_value > 0 and remaining_value or 0
            dl.accumulated_depreciation = accumulated_depreciation
            
    @api.onchange('amount')
    def onchange_amount(self):
        if self.type == 'depreciate':
            self.remaining_value = self.asset_id.asset_value \
                - self.depreciated_value - self.amount
    
    @api.v7
    def create_move(self, cr, uid, ids, context=None):
        '''
        recompute depreciation lines to align fiscal values
        '''
        asset_obj = self.pool.get('account.asset.asset')
        period_obj = self.pool.get('account.period')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        created_move_ids = []
        asset_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            asset = line.asset_id
            if asset.method_time in ['year', 'percentage']:
                depreciation_date = context.get('depreciation_date') or \
                    line.line_date
            else:
                depreciation_date = context.get('depreciation_date') or \
                    time.strftime('%Y-%m-%d')
            ctx = dict(context, account_period_prefer_normal=True)
            period_ids = period_obj.find(
                cr, uid, depreciation_date, context=ctx)
            period_id = period_ids and period_ids[0] or False
            move_id = move_obj.create(cr, uid, self._setup_move_data(
                line, depreciation_date, period_id, context),
                context=context)
            depr_acc_id = asset.category_id.account_depreciation_id.id
            exp_acc_id = asset.category_id.account_expense_depreciation_id.id
            ctx = dict(context, allow_asset=True)
            move_line_obj.create(cr, uid, self._setup_move_line_data(
                line, depreciation_date, period_id, depr_acc_id,
                'depreciation', move_id, context), ctx)
            move_line_obj.create(cr, uid, self._setup_move_line_data(
                line, depreciation_date, period_id, exp_acc_id, 'expense',
                move_id, context), ctx)
            self.write(
                cr, uid, line.id, {'move_id': move_id},
                context={'allow_asset_line_update': True})
            created_move_ids.append(move_id)
            asset_ids.append(asset.id)
        # we re-evaluate the assets to determine whether we can close them
        for asset in asset_obj.browse(
                cr, uid, list(set(asset_ids)), context=context):
            if currency_obj.is_zero(cr, uid, asset.company_id.currency_id,
                                    asset.value_residual):
                asset.write({'state': 'close'})
        asset_to_recompute = []
        # assets from move lines
        '''
        domain = [('move_id', 'in', created_move_ids),
                  ('asset_id', '!=', False)]
        ml_ids = self.pool['account.move.line'].search(cr, uid, domain)
        for ml in self.pool['account.move.line'].browse(cr, uid, ml_ids):
            asset_to_recompute.append(ml.asset_id.id)
        if asset_to_recompute:
            self.pool['account.asset.asset'].\
                compute_depreciation_board(cr, uid, asset_to_recompute, context)
        '''
        return created_move_ids
    
    @api.v7
    def unlink_move(self, cr, uid, ids, context=None):
        '''
        recompute depreciation lines to align fiscal values
        '''
        asset_to_recompute = []
        move_ids = []
        for dpl in self.browse(cr, uid, ids):
            move_ids.append(dpl.move_id.id)
        # before unlink search assets from move lines
        domain = [('move_id', 'in', move_ids),
                  ('asset_id', '!=', False)]
        ml_ids = self.pool['account.move.line'].search(cr, uid, domain)
        for ml in self.pool['account.move.line'].browse(cr, uid, ml_ids):
            asset_to_recompute.append(ml.asset_id.id)
        res = super(account_asset_depreciation_line, self).\
            unlink_move(cr, uid, ids, context)
        if asset_to_recompute:
            self.pool['account.asset.asset'].\
                compute_depreciation_board(cr, uid, asset_to_recompute, context)
        return res
    

class account_asset_depreciation_line_fiscal(models.Model):
    _name = "account.asset.depreciation.line.fiscal"
    
    name = fields.Char(string='Depreciation Name', size=64, readonly=True)
    asset_id = fields.Many2one('account.asset.asset', string='Asset',
                               required=True, ondelete='cascade')
    previous_id = fields.Many2one('account.asset.depreciation.line.fiscal', 
                                  string='Previous Depreciation Line',
                                  readonly=True)
    asset_historical_value = fields.Float(string='Asset Historical Value', 
                               digits=dp.get_precision('Account'), 
                               readonly=True)
    amount = fields.Float('Amount', required=True ,
                          digits=dp.get_precision('Account'))
    remaining_value = fields.Float('Next Period Depreciation', 
                                   compute='_compute', store=True)
    amount_variation = fields.Float('Amount Variation', 
                                    digits=dp.get_precision('Account'))
    depreciated_value = fields.Float('Amount Already Depreciated', 
                                     compute='_compute', store=True)
    accumulated_depreciation = fields.Float('Accumulated Depreciation', 
                                     compute='_compute', store=True) 
    line_date = fields.Date('Date', required=True)
    type = fields.Selection([('create', 'Asset Value'), 
                             ('depreciate', 'Depreciation'), 
                             ('remove', 'Asset Removal'),], 
                            string="Type", readonly=True, default='depreciate')
    init_entry = fields.Boolean(string='Initial Balance Entry', 
                                help="Set this flag for entries of previous \
                                fiscal years for which OpenERP has not \
                                generated accounting entries.")
    move_check = fields.Boolean(string='Posted', compute='_move_check', 
                                store=True)
    normal_line_id = fields.Many2one('account.asset.depreciation.line', 
                                  string='Depreciation Line Normal chained',
                                  readonly=True, ondelete="cascade")
    
    @api.one
    @api.depends('asset_id.depreciation_line_ids')
    def _move_check(self):
        '''
        Is posted if exists normal line with account moves 
        '''
        domain = [('asset_id', '=', self.asset_id.id),
                  ('type', '=', 'depreciate'),
                  ('line_date', '>=', self.line_date)]
        last_line = self.env['account.asset.depreciation.line'].search(
            domain, order='line_date', limit=1)
        if last_line and last_line.move_check:
            self.move_check = True
        else:
            self.move_check = False
        
    @api.one
    @api.depends('amount')
    def _compute(self):
        digits = self.env['decimal.precision'].precision_get('Account')
        asset_value = self[0].asset_id.asset_value
        domain = [('asset_id', '=', self.asset_id.id),
                  ('type', '=', 'depreciate')]
        dlines = self.search(domain, order='line_date')
        for i, dl in enumerate(dlines):
            if i == 0:
                depreciated_value = dl.previous_id and \
                    (asset_value - dl.previous_id.remaining_value) or 0.0
                remaining_value = dl.asset_historical_value - depreciated_value\
                     - dl.amount
                accumulated_depreciation = depreciated_value + dl.amount
            else:
                remaining_value -= dl.amount
                remaining_value += dl.amount_variation
                round(remaining_value, digits)
                depreciated_value += dl.previous_id.amount
                accumulated_depreciation = depreciated_value + dl.amount
            dl.depreciated_value = depreciated_value
            dl.remaining_value = round(remaining_value > 0 and remaining_value \
                                       or 0, digits)
            dl.accumulated_depreciation = accumulated_depreciation
            
    @api.onchange('amount')
    def onchange_amount(self):
        if self.type == 'depreciate':
            self.remaining_value = self.asset_id.asset_value \
                - self.depreciated_value - self.amount


class account_asset_property(models.Model):
     
    _name = "account.asset.property"
    _description = "Asset - Property"
    
    name = fields.Char(string='Name', required=True)
    line_ids = fields.One2many('account.asset.property.line', 'property_id',
                               string='Roles')
    fiscal_depreciation = fields.Boolean(string='Apply to Fiscal Depreciation',
                                         default=True)
    normal_depreciation = fields.Boolean(string='Apply to Normal Depreciation',
                                         default=True)
    fiscal_coeff_asset_depreciable = fields.Float(
        string='Coeff for asset Fiscal value depreciable', default=1)
    normal_coeff_asset_depreciable = fields.Float(
        string='Coeff for asset Normal value depreciable', default=1)

    def _compute_role(self, amount, nr_line, nr_last_line):
        dp_obj = self.env['decimal.precision']
        role = {
            'amount' : amount,
            'coeff' : 0,
        }
        p_line = False
        # Search for nr line
        domain = [('property_id', '=', self.id),
                  ('line_number', '=', nr_line)] 
        p_line = self.env['account.asset.property.line'].search(domain)
        if p_line:
            role['amount'] = round(amount * p_line.coeff, 
                                   dp_obj.precision_get('Account'))
            role['coeff'] = p_line.coeff
            role['fiscal_depreciation'] = p_line.property_id.fiscal_depreciation
            role['normal_depreciation'] = p_line.property_id.normal_depreciation
            return role
        
        # Search for last line
        if nr_line == nr_last_line:
            domain = [('property_id', '=', self.id),
                      ('line_number', '=', -1)]
            p_line = self.env['account.asset.property.line'].search(domain)
            if p_line:
                role['amount'] = round(amount * p_line.coeff, 
                                   dp_obj.precision_get('Account'))
                role['coeff'] = p_line.coeff
                role['fiscal_depreciation'] = \
                    p_line.property_id.fiscal_depreciation
                role['normal_depreciation'] = \
                    p_line.property_id.normal_depreciation
                return role
        
        return role


class account_asset_property_line(models.Model):
     
    _name = "account.asset.property.line"
    _description = "Asset - Property line"
    
    property_id = fields.Many2one('account.asset.property', readonly=True)
    sequence = fields.Integer(string='Sequence', readonly=True)
    name = fields.Char(string='Name')
    line_number = fields.Integer(string='Line number', help="Line number to \
        apply the coeff. Set -1 for the last line.")
    coeff = fields.Float('Coeff')

