# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Alessandro Camilli (alessndrocamilli@openforce.it)
#            Walter Antolini (walterantolini@openforce.it)
#    Copyright (C) 2015 Abstract (http://www.abstract.it)
#                       Openforce di Camilli Alessandro (www.openforce.it)
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
    'name': 'Italian Assets Management Report',
    'version': '1.1.7',
    'category': 'Localization/Italy',
    'summary': 'Italian Assets Management',
    'author': 'Openforce di Alessandro Camilli, \
        Odoo Community Association (OCA)',
    'website': 'http://www.openforce.it/',
    'license': 'AGPL-3',
    'depends': [
        'account', 'account_asset_management', 'l10n_it_assets'
    ],
    'data': [
        'wizard/assets_report_registry.xml',
        'report/report.xml',
        'report/report_assets_report_registry.xml'
    ],
    'test': [],
    'installable': True,
}
