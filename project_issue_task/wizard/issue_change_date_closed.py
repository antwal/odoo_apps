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
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import models, fields, api, _


class wizard_issue_change_date_closed(models.TransientModel):
    _name = "wizard.issue.change.date.closed"
    _description = "Wizard for issue to change date closed"

    date_closed = fields.Datetime(string='Date Closed')

    @api.multi
    def change_date_closed(self):
        for wiz_obj in self:
            issue_ids = self.env.context.get('active_ids')
            for issue in self.env['project.issue'].browse(issue_ids):
                issue.date_closed  = wiz_obj.date_closed

        return {'type': 'ir.actions.act_window_close'}
