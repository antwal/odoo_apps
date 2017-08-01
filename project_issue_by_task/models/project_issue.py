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
from openerp.exceptions import ValidationError


class project_issue(models.Model):
    _inherit = 'project.issue'

    @api.one
    @api.depends('task_ids')
    def _task_count(self):
        self.task_count = len(self.task_ids)

    task_ids = fields.One2many('project.task', 'issue_id', string='Tasks')
    task_count = fields.Integer(string='Tasks', compute='_task_count')

    @api.multi
    def action_show_issue_tasks(self):
        context = {
            'search_default_issue_id' : self.id
        }
        return {
            'name':_("Tasks of Issue"),
            'view_mode': 'kanban,tree,form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'project.task',
            'res_id': False,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': '[]',
            'context': context
        }

    @api.multi
    def action_create_task(self):
        # Setting default for new task
        context = {
            'default_name' : self.name,
            # TODO: Bug with store modules, need fix it
            'default_store_id' : self.store_id.id or False,
            'default_issue_id' : self.id,
            'default_project_id' : self.project_id.id,
            'default_user_id' : False,
            'default_description' : self.description,
            'default_categ_ids' : [x.id for x in self.categ_ids] or False,
            'default_intervention_type_id' : self.intervention_type_id.id
                or False,
        }

        return {
            'name':_("Task from Issue"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'project.task',
            'res_id': False,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'domain': '[]',
            'context': context
        }

    @api.multi
    def action_set_stage_task_completed(self):
        '''
        Set stage of all tasks linked to the issue
        '''
        # Final Stage
        domain = [('update_date_end', '=', True)]
        stage = self.env['project.task.type'].search(domain, order='id desc',
                                                     limit=1)
        if not stage:
            raise ValidationError(_('Even stage with "update date end" is \
                required'))
        for issue in self:
            # all tasks
            for task in issue.task_ids:
                task.stage_id = stage.id

    @api.v7
    def create(self, cr, uid, vals, context=None):
        partner_id = vals.get('partner_id')

        if partner_id:
            vals.update({'message_follower_ids':[(6,0, [partner_id] )]})

        return super(project_issue, self).create(cr, uid, vals, context)
