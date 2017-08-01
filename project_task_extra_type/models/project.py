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


class project_project(models.Model):
    _inherit = 'project.project'

    extra_type_id = fields.Many2one('project.extra.type',
                                    string='Default Extra Type')

class project_task(models.Model):
    _inherit = 'project.task'

    extra_type_id = fields.Many2one('project.extra.type',
                                           string='Extra Type')


class project_extra_type(models.Model):
    _name = 'project.extra.type'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code', size=10, required=True)
    default = fields.Boolean(string='Default')
