# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Antolini Walter (http://www.antwal.name)
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


from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class res_company_hostname(models.Model):
    _name = 'res.company.hostname'

    # Limited to RFC 1035 - http://www.ietf.org/rfc/rfc1035.txt
    hostname = fields.Char(string='Hostname', size=64)
    company_id = fields.Many2one('res.company', string='Company')

    @api.model
    def get_company_id_by_hostname(self, host=None):
        res = False

        if host:
            domain = [('hostname', '=', str(host))]
            company_ids = self.search(domain)

            if company_ids.company_id:
                # INFO: Return always one company_id.id
                res = company_ids.company_id.id

        return res

    @api.one
    @api.constrains('hostname')
    def _check_unique_constraint(self):
        if len(self.search([( 'hostname', '=', str(self.hostname) )])) > 1:
            raise ValidationError("Domain name already exists, it must be unique")


class res_company(models.Model):
    _inherit = 'res.company'

    hostname_id = fields.One2many('res.company.hostname', 'company_id')
