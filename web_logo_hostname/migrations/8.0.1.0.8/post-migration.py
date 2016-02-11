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
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import SUPERUSER_ID
from openerp.modules.registry import RegistryManager

def _write_update(cr, model, table, values):
    cr.execute("""
        SELECT %s, %s
        FROM %(table)s
        WHERE %(field)s is not null % {
          'table': table,
          'field': values[1]
        }
    """, (values[0], values[1],))

    if not cr.rowcount:
        # Insert / Write
        pass
    else:
        # Update
        pass

def migrate(cr, version):
    if not version:
        return

    import pdb;pdb.set_trace()

    registry = RegistryManager.get(cr.dbname)

    # Check table (8.0.1.0.6)
    cr.execute("""
        SELECT c.id, c.hostname_to_update
        FROM res_company c
    """)
    if cr.rowcount:
        hostnames = cr.fetchall()

        for hostname in hostnames:
            if not hostname[1]:
                continue

            cr.execute("""
                SELECT h.id, h.hostname_to_update
                FROM res_company h
                WHERE h.id = %d
            """ % (hostname[0],))
            host = cr.fetchone()

            if host:
                _write_update(cr, registry['res.company.hostname'], 'res_company_hostname', host, ['hostname', 'company_id'])

        # Drop old column
        cr.execute("""
            ALTER TABLE res_company
            DROP COLUMN hostname_to_update
        """)
