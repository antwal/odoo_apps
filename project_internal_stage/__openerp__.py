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
    'name': 'Project Internal Stage',
    'summary': 'Stage for internal use',
    'description': """
Add Internal Use field for Tasks and Issues
===========================================
    """,
    'version': '8.0.1.0.1',
    'category': 'Project',
    'author': "Antolini Walter",
    'website': 'http://www.antwal.name',
    'license': 'AGPL-3',
    "depends" : [
        'project',
        'project_issue'
    ],
    'data': [
        'views/project.xml',
    ],
    'installable': True,
    'auto_install': False,
}
