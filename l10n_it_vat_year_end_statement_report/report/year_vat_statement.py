# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Apulia Sofware s.r.l (<info@apuliasoftware.it>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm, fields
import time
from report import report_sxw
from tools.translate import _
from operator import itemgetter

class Parser(report_sxw.rml_parse):

    def _build_codes_dict(self, tax_code, res=None, context=None):
        '''
        Openforce changed logic: base o sum with amount to print
        '''
        if res is None:
            res = {}
        if context is None:
            context = {}
        tax_pool = self.pool['account.tax']
        if res.get(tax_code.name, False):
            raise orm.except_orm(
                _('Error'),
                _('Too many occurences of tax code %s') % tax_code.name)
        # search for taxes linked to that code
        tax_ids = tax_pool.search(
            self.cr, self.uid, [
                ('tax_code_id', '=', tax_code.id)], context=context)
        if tax_ids:
            tax = tax_pool.browse(
                self.cr, self.uid, tax_ids[0], context=context)
            # search for the related base code
            base_code = (
                tax.base_code_id or tax.parent_id
                and tax.parent_id.base_code_id or False)
            if not base_code:
                raise orm.except_orm(
                    _('Error'),
                    _('No base code found for tax code %s')
                    % tax_code.name)
            # check if every tax is linked to the same tax code and base
            # code
            for tax in tax_pool.browse(
                    self.cr, self.uid, tax_ids, context=context):
                test_base_code = (
                    tax.base_code_id or tax.parent_id
                    and tax.parent_id.base_code_id or False)
                if test_base_code.id != base_code.id:
                    raise orm.except_orm(
                        _('Error'),
                        _('Not every tax linked to tax code %s is linked '
                          'the same base code') % tax_code.name)
            # Openforce: base o sum with amount to print
            if tax_code.sum or base_code.sum:
                res[tax_code.name] = {
                    'vat': tax_code.sum,
                    'base': base_code.sum,
                }
        for child_code in tax_code.child_ids:
            res = self._build_codes_dict(
                child_code, res=res, context=context)
        return res

    def _get_tax_codes_amounts(self, type='credit',
                               tax_code_ids=None, context={}):
        tax_code_pool = self.pool['account.tax.code']
        if tax_code_ids is None:
            tax_code_ids = tax_code_pool.search(self.cr, self.uid, [
                ('vat_statement_account_id', '!=', False),
                ('vat_statement_type', '=', type),
                ], context=context)
        res = {}
        code_pool = self.pool['account.tax.code']
        context['fiscalyear_id'] = self.localcontext['data']['fiscalyear_id']
        context['year'] = self.localcontext['data']['year']
        for tax_code in code_pool.browse(
                self.cr, self.uid, tax_code_ids, context=context):
            res = self._build_codes_dict(tax_code, res=res, context=context)
        return res
    
    def _get_period(self, statement, context={}):
        res = ""
        for p in statement.period_ids:
            if res:
                res += ', '
            res += p.name
        return res
    def _get_lines_generic_amounts(self, context={}):
        end_statment_vat_obj = self.pool['account.vat.period.end.statement']
        period_obj = self.pool['account.period']
        dp_obj = self.pool['decimal.precision']
        res = []
        fiscalyear_id = self.localcontext['data']['fiscalyear_id']
        if not fiscalyear_id:
            return res
        # Periods competence
        domain = [('fiscalyear_id', '=', fiscalyear_id)]
        period_ids = period_obj.search(self.cr, self.uid, domain)
        
        # Statements of competence
        statements = []
        domain = [('id', '>', 0)]
        statement_ids = end_statment_vat_obj.search(self.cr, self.uid, domain)
        for statement in end_statment_vat_obj.browse(self.cr, self.uid, 
                                                     statement_ids):
            statement_valid = True
            for ps in statement.period_ids:
                if ps.id not in period_ids:
                    statement_valid = False
            if statement_valid:
                statements.append(statement.id)
        
        # Statement Generic lines
        amount_generic = 0
        for statement in end_statment_vat_obj.browse(self.cr, self.uid, 
                                                     statements):
            for line in statement.generic_vat_account_line_ids:
                
                data = {
                    'period' : self._get_period(statement),
                    'account_code' : line.account_id.code,
                    'account_name' : line.account_id.name or '',
                    'description' : 'description' in line and line.description\
                        or '',
                    'amount' : line.amount * -1,
                }
                res.append(data)
                # credits are positive and debits are negative
                #amount_generic += line.amount * -1
        res = sorted(res, key=itemgetter('period'))
        return res
    

    def get_year(self, context={}):
        return self.pool['account.fiscalyear'].browse(
            self.cr, self.uid,
            self.localcontext['data']['fiscalyear_id']).name
    
    def get_amount_interest(self, context={}):
        return self.localcontext['data']['amount_interest']
    def get_amount_generic(self, context={}):
        return self.localcontext['data']['amount_generic']
    def get_amount_paid(self, context={}):
        amount = self.localcontext['data']['amount_paid'] 
        return amount
            
    def get_page_year(self, context={}):
        page_year = ''
        if 'print_page_year' in self.localcontext['data']\
                and self.localcontext['data']['print_page_year']:
            page_year = self.localcontext['data']['print_page_year']
        return page_year
    
    def get_page_number_from(self, context={}):
        page_number_from = 0
        if 'print_page_number_from' in self.localcontext['data']\
                and self.localcontext['data']['print_page_number_from']:
            page_number_from = self.localcontext['data']['print_page_number_from']
        return page_number_from

    def __init__(self, cr, uid, name, context=None):
        if context is None:
            context = {}
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'tax_codes_amounts': self._get_tax_codes_amounts,
            'lines_generic_amounts': self._get_lines_generic_amounts,
            'year': self.get_year,
            'amount_generic': self.get_amount_generic,
            'amount_interest': self.get_amount_interest,
            'amount_paid': self.get_amount_paid,
            'print_page_year': self.get_page_year,
            'print_page_from': self.get_page_number_from,
            })
        self.context = context
 
report_sxw.report_sxw(
    'report.vat.year.end.statement',
    'wizard.year.statement',
    'addons/year_vat_period_and_statement/report/'
    'year_vat_statement.mako',
    parser=Parser)