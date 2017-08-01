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


class project_issue(models.Model):
    _inherit = 'project.issue'

    extra_type_id = fields.Many2one('project.extra.type',
                                           string='Extra Type')

    @api.v7
    def on_change_project(self, cr, uid, ids, project_id, context=None):
        res = super(project_issue, self).on_change_project(cr, uid, ids,
                                                           project_id,
                                                           context=None)
        if project_id:
            project = self.pool.get('project.project').browse(cr, uid,
                                                              project_id,
                                                              context=context)
            if project and project.extra_type_id:
                res['value']['extra_type_id'] = \
                    project.extra_type_id.id
            else:
                res['value']['extra_type_id'] = False
        return res
