# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Abstract (http://www.abstract.it)
#                       Openforce di Camilli Alessandro - www.openforce.it
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Italian Assets Management',
    'version': '8.0.2.5',
    'category': 'Localization/Italy',
    'description': """
        - Parallel Depreciation Board for fiscal values
        - Amount Variations from other moves in the year
        - Property of asset to compute lines throught coefficients 
        
        Require account_asset_management with Pull Request 
        https://github.com/alessandrocamilli/account-financial-tools/commit/27a6b65521370c68ed381d3a41f0305735c7dee6
    """,
    'summary': 'Italian Assets Management',
    'author': 'Openforce di Alessandro Camilli, Abstract, \
        Odoo Community Association (OCA)',
    'website': 'http://www.openforce.it/',
    'license': 'AGPL-3',
    'depends': [
        'account', 'account_asset_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/asset_view.xml',
        'views/account_view.xml',
        'wizard/account_asset_remove_select_view.xml',
        ],
    'test': [],
    'installable': True,
}
