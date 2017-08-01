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

from openerp.tools.translate import _
from openerp.osv import orm, fields
import decimal_precision as dp

class wizard_year_statement(orm.TransientModel):

    _name = 'wizard.year.statement'

    _columns = {
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscalyear',
                                         required=True),
        'amount_generic': fields.float('Generic Credit or Debit', 
                                       readonly=True),
        'amount_interest': fields.float('Amount Interest'),
        'amount_paid': fields.float('Amount Paid'),
        'print_page_from': fields.integer('Page number from'),
        'print_page_year': fields.char('Page number year', size=10),
        }
    
    _defaults = {
        'print_page_from' : 1,
        'amount_paid' : 0
        }
    
    def on_change_fiscalyear_id(self, cr, uid, ids, fiscalyear_id, context=None):
        res={}
        
        end_statment_vat_obj = self.pool['account.vat.period.end.statement']
        period_obj = self.pool['account.period']
        dp_obj = self.pool['decimal.precision']
        
        if not fiscalyear_id:
            return res
        # Periods competence
        domain = [('fiscalyear_id', '=', fiscalyear_id)]
        period_ids = period_obj.search(cr, uid, domain)
        
        wiz_val = {}
        # Statements of competence
        statements = []
        domain = [('id', '>', 0)]
        statement_ids = end_statment_vat_obj.search(cr, uid, domain)
        for statement in end_statment_vat_obj.browse(cr, uid, statement_ids):
            statement_valid = True
            for ps in statement.period_ids:
                if ps.id not in period_ids:
                    statement_valid = False
            if statement_valid:
                statements.append(statement.id)
        
        # Statement Generic lines
        amount_generic = 0
        for statement in end_statment_vat_obj.browse(cr, uid, statements):
            for line in statement.generic_vat_account_line_ids:
                print "xx"
                # credits are positive and debits are negative
                amount_generic += line.amount * -1
        wiz_val.update({'amount_generic':amount_generic})
        
        # Statement Paid
        amount_paid = 0
        domain = [('state', '=', 'paid')]
        statement_ids = end_statment_vat_obj.search(cr, uid, domain)
        for statement in end_statment_vat_obj.browse(cr, uid, statement_ids):
            if statement.id not in statements:
                continue
            if statement.authority_vat_amount > 0:
                amount_paid += (statement.authority_vat_amount \
                                - statement.residual)
        wiz_val.update({'amount_paid':amount_paid}) 
        
        res={'value': wiz_val}
        
        return res
    
    def print_report(self, cr, uid, ids, context={}):
        wizard = self.browse(cr, uid, ids, context)[0]
        res = {
            'type': 'ir.actions.report.xml',
            'datas': {'ids': ids,
                      #'model': 'account.move',
                      'model': self._name,
                      'fiscalyear_id': wizard.fiscalyear_id.id,
                      'amount_generic': wizard.amount_generic,
                      'amount_interest': wizard.amount_interest,
                      'amount_paid': wizard.amount_paid,
                      'year': wizard.fiscalyear_id.name,
                      'print_page_from': wizard.print_page_from,
                      'print_page_year': wizard.print_page_year,
                      },
            'report_name': 'vat.year.end.statement',
        }
        return res