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


class project_task(models.Model):
    _inherit = 'project.task'

    issue_id = fields.Many2one('project.issue', string='Issue')
    sync_stage_issue = fields.Boolean(string='Sync Stage Issue', default=True)
    worksheet_attachment_ids = fields.Many2many('ir.attachment',
                                                string="Worksheet")
    issue_ticket_ref = fields.Char(string='Issue Ticket Ref', store=True,
                                   related='issue_id.ticket_ref')
    @api.multi
    def write(self, vals):
        '''
        Sync with issue if required
        '''
        for task in self:
            if 'stage_id' in vals:
                if task.sync_stage_issue and task.issue_id:
                    task.issue_id.write({'stage_id' : vals['stage_id']})

        return super(project_task,self).write(vals)
