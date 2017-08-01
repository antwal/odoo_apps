# -*- coding: utf-8 -*-
##############################################################################
#    
#    Author: Alessandro Camilli (a.camilli@openforce.it)
#    Copyright (C) 2015
#    Openforce di Camilli Alessandro - www.openforce.it
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

from openerp.tests.common import TransactionCase

class test_intrastat(TransactionCase):
    
    def create_invoice(self, partner, lines):
        # Partner data
        res = self.inv_obj.onchange_partner_id(
            'out_invoice', partner.id, date_invoice=False, payment_term=False, 
            partner_bank_id=False, company_id=False)
        partner_vals = {
            'fiscal_position' : res['value']['fiscal_position'],
            'account_id' : res['value']['account_id'],
            'payment_term' : res['value']['payment_term'],
            }
        # Invoice
        vals = {
            'partner_id': partner.id,
            'intrastat': True,
            'invoice_line': lines,
            'account_id': partner_vals['account_id'],
            'fiscal_position': partner_vals['fiscal_position'],
            'payment_term': partner_vals['payment_term']
            }
        return self.inv_obj.create(vals)
    

    def setUp(self):
        super(test_intrastat, self).setUp()
        
        self.inv_obj = self.env['account.invoice']
        self.inv_line_obj = self.env['account.invoice.line']
        self.partner01 = self.env.ref('base.res_partner_1')
        self.product01 = self.env.ref('product.product_product_10')
        
    def test_invoice_totals(self):
        '''
        Total of invoice must be equal to total amount intrastat lines
        '''
        
        # Create invoice
        lines = []
        
        res = self.inv_line_obj.product_id_change(
            self.product01.id, self.product01.uom_id.id, qty=1, name='', 
            type='out_invoice', partner_id=self.partner01.id, 
            fposition_id=False, price_unit=False, currency_id=False,
            company_id=None)
        vals = res['value']
        vals['product_id'] = self.product01.id
        vals['quantity'] = 1
        
        lines.append( (0, 0, vals))
        invoice = self.create_invoice(self.partner01, lines)
        
        # Compute intrastat lines
        invoice.compute_intrastat_lines()
        self.assertEqual(invoice.intrastat, True)
        # Amount Control 
        total_intrastat_amount = sum(
            l.amount_currency for l in invoice.intrastat_line_ids)
        self.assertEqual(total_intrastat_amount, invoice.amount_untaxed)
        
        
        
        
        