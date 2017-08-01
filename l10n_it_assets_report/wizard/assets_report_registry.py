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

from openerp import models, fields, api, exceptions, _
from openerp.exceptions import Warning as UserError

# v8
class assets_report_registry(models.TransientModel):
    _name = 'assets.report.registry'

    date_start = fields.Date(string='Asset Start Date')
    date_end = fields.Date(string='Asset End Date')

    category_id = fields.Many2many('account.asset.category', string='Asset Category')
    asset_id = fields.Many2many('account.asset.asset', string='Asset Name')

    # v7
    def report_registry_print(self, cr, uid, ids, context=None):
        """
        Avvio la stampa verso il report in base alla scelta dell'utente nel Wizard

        :param cr:
        :param uid:
        :param ids:
        :param context:
        :return:
        """

        # Recupera le informazioni del wizard
        wizard = self.browse(cr, uid, ids[0], context=context)

        # Recupero i recordset
        search_obj = self.pool['account.asset.depreciation.line.fiscal']

        search_domain = []
        # Pre ricerca condizionale
        if wizard.category_id:
            search_domain += [('asset_id.category_id', 'in', [category.id for category in wizard.category_id])]
        if wizard.asset_id:
            search_domain += [('asset_id', 'in', [asset.id for asset in wizard.asset_id])]
        if wizard.date_start and wizard.date_end:
            search_domain += [('line_date', '>=', wizard.date_start), ('line_date', '<=', wizard.date_end)]
        elif wizard.date_start:
            search_domain += [('line_date', '>=', wizard.date_start)]
        elif wizard.date_end:
            search_domain += [('line_date', '<=', wizard.date_end)]

        # Effettuo una ricerca in base alla selezione dell'utente
        search_ids = search_obj.search(cr, uid, search_domain)

        if not search_ids:
            raise UserError(_('No documents found in the current selection'))
        # else

        unique_asset_id = []
        # Genero una lista degli ID univoci degli asset presenti nella ricerca
        for single_id in search_obj.browse(cr, uid, search_ids, context=context):
            if not single_id['asset_id'].id in unique_asset_id:
                unique_asset_id.append(single_id['asset_id'].id)

        datas_form = {}
        datas_form['asset_ids'] = unique_asset_id
        datas_form['date_start'] = wizard.date_start
        datas_form['date_end'] = wizard.date_end

        report_name = 'l10n_it_assets_report.report_assets_report_registry'

        datas = {}
        datas = {
            'ids': search_ids,
            'model': 'account.asset.depreciation.line.fiscal',
            'form': datas_form,
        }

        # Richiamo le azioni sul Report (Parser)
        return self.pool['report'].get_action(
            cr, uid, [], report_name, data=datas, context=context)
