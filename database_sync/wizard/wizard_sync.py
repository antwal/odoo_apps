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

from osv import fields,orm, osv
from tools.translate import _
import time

class wizard_sync(osv.osv_memory):

    _name = "db.sync.wizard.sync"
    _columns = {
    }

    def execute_sync(self, cr, uid, ids, context=None):
        wizard = self.read(cr, uid, ids)[0]
        db_sync_connection_obj = self.pool['db.sync.connection']

        domain = [('active', '=', True)]
        conn_ids = db_sync_connection_obj.search(cr, uid, domain)

        db_sync_connection_obj.execute_sync(cr, uid, conn_ids, context=None)

        return {
            'type': 'ir.actions.act_window_close',
        }
