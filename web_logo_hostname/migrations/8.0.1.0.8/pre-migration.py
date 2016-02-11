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

def migrate(cr, version):
    if not version:
        return

    # Check table (8.0.1.0.6)
    cr.execute("""
        SELECT c.id, c.hostname
        FROM res_company c
    """)
    hostnames = cr.fetchall()

    if isinstance(hostnames, list):
        # Migrate to 8.0.1.0.8
        cr.execute("""
            ALTER TABLE res_company
            RENAME COLUMN hostname TO hostname_to_update
        """)
    else:
        return
