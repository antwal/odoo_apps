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
    _inherit = 'project.task.type'

    update_date_end = fields.Boolean(string='Update Date End')


class project_task(models.Model):
    _inherit = 'project.task'

    @api.multi
    def write(self, vals):
        '''
        Sync with issue if required
        '''
        for task in self:
            if 'stage_id' in vals:
                stage = self.env['project.task.type'].browse(vals['stage_id'])
                if stage.update_date_end:
                    vals['date_end'] = fields.Datetime.now()
                    if not 'date_start' in vals:
                        vals['date_start'] = task.date_start
                    if vals['date_start'] > vals['date_end']:
                        vals['date_start'] = vals['date_end']

        return super(project_task,self).write(vals)
