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

from openerp.report import report_sxw
from openerp.osv import osv
from openerp import _

# v7
class Parser(report_sxw.rml_parse):
    """
    Template Parser
    """

    def __init__(self, cr, uid, name, context):
        """
        Definisco le mie funzioni nel Parser da richiamare nel template

        :param cr:
        :param uid:
        :param name:
        :param context:
        :return:
        """

        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_assets': self._get_assets,
            'get_lines': self._get_lines,
            'purchaseValue': self._format_purchase_value,
        })

    def set_context(self, objects, data, ids, report_type = None):
        """
        Recupero il data passato dal wizard e lo assegno a delle variabili per il template

        :param objects:
        :param data:
        :param ids:
        :param report_type:
        :return:
        """

        self.localcontext.update({
            'asset_ids': data['form'].get('asset_ids'),
        })
        return super(Parser, self).set_context(
            objects, data, ids, report_type=report_type)

    def _get_lines(self, data, asset):
        """
        Asset valid lines
        :param data:
        :param asset:
        :return:
        """
        depreciation_obj = self.pool['account.asset.depreciation.line.fiscal']
        domain =[('asset_id', '=', asset.id),
                 ('type', 'in', ['depreciate'])]
        if data['form']['date_start']:
            domain.append(('line_date', '>=', data['form']['date_start']))
        if data['form']['date_end']:
            domain.append(('line_date', '<=', data['form']['date_end']))
        
        line_ids = depreciation_obj.search(self.cr, self.uid, domain)
        if line_ids:
            return depreciation_obj.browse(self.cr, self.uid, line_ids)
        else:
            return False

    def _get_assets(self, asset_ids):
        """
        Ritorna la lista degli assets n base agli id passati

        :param asset_ids:
        :return:
        """

        asset_obj = self.pool.get('account.asset.asset')
        # Recupero i record dell'asset_id richiesto
        asset_items = asset_obj.browse(self.cr, self.uid, asset_ids)

        return asset_items

    def _format_purchase_value(self, value):
        """
        Il dato passato è un float

        :param value:
        :return:
        """

        # TODO: Rivedere questa funzione
        return abs(value)


# v7
class ReportAssetRegistry(osv.AbstractModel):
    """
    Wrapper Template Abstract Model
    """

    _name = 'report.l10n_it_assets_report.report_assets_report_registry'
    _inherit = 'report.abstract_report'
    _template = 'l10n_it_assets_report.report_assets_report_registry'
    _wrapped_report_class = Parser