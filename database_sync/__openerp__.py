# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Walter Antolini (info@antwal.name)
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
    'name': 'Database sync',
    'version': '1.0',
    'category': 'Base',
    'description': """
    Handle sync between more databases
""",
    'author': 'Antolini Walter',
    'website': 'https://www.antwal.name',
    'license': 'AGPL-3',
    "depends" : ['base',],
    "data" : [
              'security/security.xml',
              'security/ir.model.access.csv',
              'view/db_sync_view.xml',
              'wizard/wizard_sync_view.xml',
              ],
    "demo" : [],
    "active": False,
    "installable": True
}
