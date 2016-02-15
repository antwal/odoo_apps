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
        SELECT hostname, company_id
        FROM res_company_hostname
        WHERE company_id is not null
    """)

    if not cr.rowcount:
        # Insert / Migrate content table
        cr.execute("""
            INSERT INTO res_company_hostname (hostname, company_id, write_date, create_uid, write_uid)
            SELECT hostname_to_update, id, write_date, create_uid, write_uid
            FROM res_company
        """)
    else:
        # Update / Migrate content table
        cr.execute("""
            UPDATE res_company_hostname
            SET hostname = res_company.hostname_to_update,
                company_id = res_company.id,
                write_date = res_company.write_date,
                create_uid = res_company.create_uid,
                write_uid = res_company.write_uid
            FROM res_company
        """)

    # Not delete old column but rename only
    cr.execute("""
        ALTER TABLE res_company
        RENAME COLUMN hostname_to_update TO hostname_to_delete
    """)
