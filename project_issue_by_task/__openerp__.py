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


{
    'name': 'Project Issue Task',
    'summary': 'Handle Issue with tasks',
    'description': """
Manange the issue by task. For each Issue, it's possibile to chain more tasks.
==============================================================================
    """,
    'version': '8.0.2.0.4',
    'category': 'Project',
    'author': "Antolini Walter",
    'website': 'http://www.antwal.name',
    'license': 'AGPL-3',
    "depends" : [
        'project_issue',
        'project_issue_ticket_sequence_id',
        'project_task_extra_type',
        'project_issue_extra_type',
        'project_stage_update'
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/issue_change_date_closed_view.xml',
        'views/project_issue.xml',
        'views/project.xml',
    ],
    'installable': True,
    'auto_install': False,
}
