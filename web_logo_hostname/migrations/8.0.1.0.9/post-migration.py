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

    cr.execute("""
        SELECT c.id, c.hostname
        FROM res_company c
    """)
    hostnames = cr.fetchall()

    for hostname in hostnames:
        if not hostname[1]:
            continue

        cr.execute("""
            SELECT h.id, h.hostname
            FROM res_company h
            WHERE h.id = %d
        """ % hostname[0])
        host = cr.fetchone()

        if host:
            # Insert old value to new table
            cr.execute("""
                INSERT INTO res_company_hostname(hostname, company_id)
                VALUES ('%s', %d)
            """ % (hostname[1], host[0]))

    # Drop old column
    cr.execute("""
        ALTER TABLE res_company
        DROP COLUMN hostname
    """)
