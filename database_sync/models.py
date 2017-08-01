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

from openerp.osv import fields, orm
from openerp.tools.translate import _
from datetime import datetime, date
from operator import itemgetter

import psycopg2

class db_sync_connection(orm.Model):

    _name = "db.sync.connection"
    _description = "DB sync - Connection"

    _columns = {
        'name': fields.char('Name', required=True),
        'active': fields.boolean('Active'),
        'type': fields.selection((
                                   ('import','Import'),
                                   ('export','Export')),
                                'Type'),
        'host': fields.char('Host', required=True),
        'host_user_id': fields.integer('User ID', required=True),
        'database_name': fields.char('Database name', size=64, required=True),
        'database_user': fields.char('Database user', size=64, required=True),
        'database_password': fields.char('Database password', size=64, required=True),

        'model_ids': fields.one2many('db.sync.model', 'connection_id','Models to sync'),
        'log_ids': fields.one2many('db.sync.log', 'connection_id','Log of sync'),
        'counter_ids': fields.one2many('db.sync.model.counter', 'connection_id','Counters'),
        'element_ids': fields.one2many('db.sync.model.element', 'connection_id','Elements'),
    }

    _defaults = {
        'active' : True
        }

    def execute_sync(self, cr, uid, ids, context=None):
        res = {}
        if not context:
            context = {}

        for connection in self.browse(cr, uid, ids):
            # connect to db
            conn_string = "dbname='%s' user='%s' host='%s' password='%s'" \
                % (connection.database_name, connection.database_user, \
                   connection.host, connection.database_password)
            try:
                conn = psycopg2.connect(conn_string)
            except:
                raise "I am unable to connect to the database"
            cr_host = conn.cursor()
            # user host

            context.update({'connection': connection})
            context.update({'cr_host': cr_host})
            context.update({'uid_host': connection.host_user_id})

            # Move sync - create
            val = {
                'date': datetime.now(),
                'connection_id': connection.id,
                }
            log_id = self.pool['db.sync.log'].create(cr, uid, val)
            context.update({'log_id': log_id})

            # Models from sysyem to import
            for model in connection.model_ids:
                if not model.active:
                    continue
                if model.model_id.model[:3]=='ir.'\
                        and not model.model_id.model == 'ir.sequence':
                    continue

                for rel in model.model_relation_ids:
                    if not rel.active:
                        continue
                    if rel.after_model:
                        continue
                    if rel.model_id.model[:3]=='ir.'\
                        and not rel.model_id.model == 'ir.sequence':
                        continue
                    self.pool['db.sync.model'].sync(cr, uid, [model.id],
                                                    rel.model_id.id,
                                                    rel.fields_sync,
                                                    rel.sql_where,
                                                    rel.sql_constraints,
                                                    context)
                #### test
                #cr.commit()
                ###

                # Then the model required
                model_name = False
                self.pool['db.sync.model'].sync(cr, uid, [model.id],
                                                    model.model_id.id,
                                                    model.fields_sync,
                                                    model.sql_where,
                                                    model.sql_constraints,
                                                    context)
                #### test
                #cr.commit()
                ###
                # Relation after model
                for rel in model.model_relation_ids:
                    if not rel.active:
                        continue
                    if not rel.after_model:
                        continue
                    if rel.model_id.model[:3]=='ir.'\
                            and not rel.model_id.model == 'ir.sequence':
                        continue

                    self.pool['db.sync.model'].sync(cr, uid, [model.id],
                                                    rel.model_id.id,
                                                    rel.fields_sync,
                                                    rel.sql_where,
                                                    rel.sql_constraints,
                                                    context)
        return res

class db_sync_model_relation(orm.Model):
    '''
    All model linked
    '''
    _name = "db.sync.model.relation"
    _description = "DB sync - Model - Relations"

    _columns = {
        'model_ref_id': fields.many2one('db.sync.model', 'Model Ref',
                                required=True, readonly=True, ondelete="cascade"),
        'model_id': fields.many2one('ir.model', 'Model', required=True),
        'sequence': fields.integer('Sequence'),
        'after_model': fields.boolean('Sync after model of ref'),
        'fields_sync': fields.text('Field unique for sync',
                help='Use comma for more fields'),
        'sql_where': fields.text('Sql where',
                help='Sql condition WITHOUT command where'),
        'sql_constraints': fields.text('Sql constraints',
                help='Sql constraints'),
        'active': fields.boolean('Active'),
    }
    _defaults = {
        'active': True
    }

    _order = "sequence"

class db_sync_model(orm.Model):

    _name = "db.sync.model"
    _description = "DB sync - Model"

    _columns = {
        'connection_id': fields.many2one('db.sync.connection', 'Connection',
                    readonly=True, ondelete="cascade"),
        'model_id': fields.many2one('ir.model', 'Model', required=True),
        'name': fields.char('Model Name'),
        'fields_sync': fields.text('Field unique for sync',
                help='Use comma for more fields'),
        'sql_where': fields.text('Sql where',
                help='Sql condition WITHOUT command where'),
        'sql_constraints': fields.text('Sql constraints',
                help='Sql constraints'),
        'active': fields.boolean('Active'),
        'model_relation_ids': fields.one2many('db.sync.model.relation', 'model_ref_id', 'Model'),
    }
    _defaults = {
        'active': True
    }

    def on_change_model_id(self, cr, uid, ids, model_id, context=None):
        rels = []
        if model_id:

            relations = self.get_relations(cr, uid, model_id, context)

            seq = 0
            for rel in relations:
                seq+=1
                val = {
                    'sequence' : seq,
                    #'model_ref_id' : model_id,
                    'model_id' : rel['model_id'],
                    'after_model' : rel['after_model'],
                    'fields_sync' : rel['fields_sync'],
                    'active' : True,
                }
                rels.append((0,0,val))
        val = {'model_relation_ids' : rels}
        res ={}
        res = {'value': val}

        return res

    def _get_sub_relations(self, cr, uid, model_to_scan, model_already_scan,
                           sequence, context=None):
        ir_model_obj = self.pool['ir.model']
        res = {
            'model_to_scan' : [],
            'model_rel' : {},
            'sequence' : sequence
            }
        model_rel = {}
        new_model_to_scan = []
        for ir_model in ir_model_obj.browse(cr, uid, model_to_scan):
            # Model ok
            model_already_scan.append(ir_model.id)
            for field in ir_model.field_id:
                if field.ttype in ['many2one', 'many2many']:
                    # Search ids to append for more relations
                    domain = [('model', '=', field.relation)]
                    ir_model_ids = ir_model_obj.search(cr, uid, domain)
                    # Save data
                    sequence += 1
                    val = {
                        'model_id' : ir_model_ids and ir_model_ids[0] or False,
                        'model' : field.relation,
                        'sequence' : sequence,
                        'after_model' : False,
                        'fields_sync' : False
                    }

                    model_rel[field.relation] = val
                    # Next level
                    for ir_model_id in ir_model_ids:
                        if not ir_model_id in  model_already_scan \
                            and not ir_model_id in  new_model_to_scan:
                            new_model_to_scan.append(ir_model_id)
        res = {
            'model_already_scan' : model_already_scan,
            'new_model_to_scan' : new_model_to_scan,
            'model_rel' : model_rel,
            'sequence' : sequence,
        }
        return res


    def get_relations(self, cr, uid, model_id, context=None):
        '''
        Return a structure with all models to sync ordered by parent
        '''
        if not model_id:
            return False
        ir_model_obj = self.pool['ir.model']
        ir_model = ir_model_obj.browse(cr, uid, model_id)

        res = {}
        # Fields linked to another model
        model_rel = {}
        model_to_scan = []
        model_already_scan = []
        sequence = 0
        model_to_scan.append(model_id)# first is model in the connection
        continue_scan = True

        while continue_scan:
            res = self._get_sub_relations(cr, uid,
                                          model_to_scan,
                                          model_already_scan,
                                          sequence,
                                          context)
            if not res['new_model_to_scan']:
                continue_scan = False
            else:
                model_to_scan = res['new_model_to_scan']
                model_already_scan = res['model_already_scan']
                sequence = res['sequence']
                model_rel.update(res['model_rel'])

        # Reorder relation by priority
        # remove key
        model_rel_with_key = model_rel
        model_rel_list = []
        for key, value in model_rel_with_key.iteritems():
            model_rel_list.append(value)
        # Order by priority
        model_rel = []
        res = sorted(model_rel_list, key=itemgetter('sequence'), reverse=True)

        # Low priority to models linked to main model
        model_rel = []
        for md in res:
            ir_model = ir_model_obj.browse(cr, uid, md['model_id'])
            after_model = False
            field_key_sync = ""
            for field in ir_model.field_id:
                if field.ttype in ['many2one', 'many2many']:
                    # Search ids to append for more relations
                    domain = [('model', '=', field.relation)]
                    ir_model_ids = ir_model_obj.search(cr, uid, domain)
                    if ir_model_ids[0] == model_id:
                        after_model = True
                if field.name in ["name"]:
                    if field_key_sync:
                        field_key_sync += ', '
                    field_key_sync += field.name

            md.update({'after_model': after_model})
            md.update({'fields_sync': field_key_sync})
            model_rel.append(md)
        res = model_rel
        return res

    def _get_last_ref(self, cr, uid, ir_model, type='import',context=None):
        connection = context.get('connection')
        last_ref = False
        domain = [('connection_id', '=', connection.id),
                  ('model_id', '=', ir_model.id)]
        model_log_ids = self.pool['db.sync.model.counter'].search(cr, uid,
                                    domain)
        if model_log_ids:
            model_log = self.pool['db.sync.model.counter'].browse(cr, uid,
                                                    model_log_ids[0])
            if model_log:
                if type == 'import':
                    last_ref = model_log.last_ref_imported
                else:
                    last_ref = model_log.last_ref_exported
        return last_ref

    def _get_elements_to_sync(self, cr, uid, ir_model, type='import',
                                            sql_where=None,
                                            sql_constraints=None,
                                            context=None):
        if not sql_where:
            sql_where = ''
        sql_filters = False

        connection = context.get('connection')
        cr_host = context.get('cr_host')
        uid_host = context.get('uid_host')
        # Sql constrains
        # NB: id field is required in the statement!!!!
        if sql_constraints:
            sql_filters = {}
            elements_constraint = []
            elements_constraint_ids = []
            cr_host.execute(sql_constraints)

            columns = [i[0] for i in cr_host.description]
            for element in cr_host.fetchall():
                elements_constraint.append(dict(zip(columns, element)))
                elements_constraint_ids.append(elements_constraint[-1]['id'])
            if elements_constraint_ids:
                if sql_where :
                    sql_where += ' AND '
                sql_where += " id IN %(constraint_ids)s "
                sql_filters.update({'constraint_ids': tuple(elements_constraint_ids)})

        # Last Ref imported
        last_ref = self._get_last_ref(cr, uid, ir_model, type, context)
        if last_ref:
            if sql_where :
                sql_where += ' AND '
            sql_where += " write_date > '%s' " % last_ref
        sql_table_name = ir_model.model
        sql_table_name = sql_table_name.replace(".", "_")

        sql = """ SELECT * FROM %s  """ % (sql_table_name,)
        if sql_where:
            sql += " WHERE %s " % sql_where
        if connection.type == type:
            elements = []
            cr_host.execute(sql, sql_filters)
            # cursor to dict
            columns = [i[0] for i in cr_host.description]
            for element in cr_host.fetchall():
                elements.append(dict(zip(columns, element)))
        else:
            #cr.execute(sql)
            cr.execute(sql, sql_filters)
            elements = cr.dictfetchall()

        # ADD fields with relations
        if elements:
            elements = self._prepare_relation_field(cr, uid, ir_model,
                                                    elements, context)

        return elements

    def _prepare_relation_field(self, cr, uid, ir_model, elements,
                                            context=None):
        '''
        Add Field of relations
        '''
        ## TODO: There is a bug with many2many
        ##


    def _prepare_destination_id(self, cr, uid, ids, ir_model, element_origin,
                                            fields_sync, context=None):
        ###
        # FIXED
        ###
        if ir_model.model == "res.company":
            return element_origin['id']
        if ir_model.model[:3] == "ir." \
                and not ir_model.model == 'ir.sequence':
            return element_origin['id']
        '''
        To extend for another policy to assign destination id
        '''
        connection = context.get('connection')
        cr_host = context.get('cr_host')
        uid_host = context.get('uid_host')

        destination_id = False
        #
        # Search relation on register
        #
        rel = False
        rel = self.pool['db.sync.model.element'].get_rel(cr, uid,
                                    ir_model.id,
                                    False,
                                    element_origin['id'],
                                    context)
        if rel and rel.local_id:
            destination_id = rel.local_id

        #
        # Search relation with key fields sync
        #
        if not destination_id and fields_sync:

            where = ""
            where_params = []
            field_key_list = fields_sync.split(',')
            for field_key in field_key_list:
                field_key = field_key.strip()
                # features of field
                # Compose where
                if where:
                    where += ' AND '
                where +=  field_key + " = %s "

                where_params.append(element_origin[field_key]) # automatic escape char
            where_params = tuple(where_params)

            where = ' WHERE ' + where
            sql_table_name = ir_model.model
            sql_table_name = sql_table_name.replace(".", "_")

            sql = """ SELECT * FROM %s
                    %s
                    LIMIT 1
                """ \
                % (sql_table_name, where)
            if connection.type == 'export':
                elements = []
                cr_host.execute(sql, where_params)
                # cursor to dict
                columns = [i[0] for i in cr_host.description]
                for element in cr_host.fetchall():
                    elements.append(dict(zip(columns, element)))
            else:
                cr.execute(sql, where_params)
                elements = cr.dictfetchall()
            destination_id = False
            for el in elements:
                destination_id = el['id']
                # Register relations between local and host element
                rel_id = self.pool['db.sync.model.element'].register(cr, uid,
                                                ir_model.id,
                                                el['id'],
                                                element_origin['id'],
                                                context)
        return destination_id

    def _change_ref(self, cr, uid, ids, ir_model, element, ref_field, context=None):
        '''
        Change Ids ref to other models second the elements already in the destination db
        '''
        connection = context.get('connection')
        cr_host = context.get('cr_host')
        uid_host = context.get('uid_host')

        domain = [('model_id', '=', ir_model.id),
                  ('name', '=', ref_field)]
        m_field_ids = self.pool['ir.model.fields'].search(cr, uid, domain)
        for m_field in self.pool['ir.model.fields'].browse(cr, uid, m_field_ids):
            if not element[ref_field]:
                continue
            if m_field.relation[:3]=='ir.' \
                and not m_field.relation == 'ir.sequence':
                    continue
            domain = [('model', '=', m_field.relation)]
            model_rel_ids = self.pool['ir.model'].search(cr, uid, domain)
            if model_rel_ids:

                ## Search id relations with function base for retrive destination
                destination_el_id = False
                ir_model_rel = self.pool['ir.model'].browse(cr, uid,
                                                            model_rel_ids[0])
                sql_table_name = ir_model_rel.model
                sql_table_name = sql_table_name.replace(".", "_")

                sql = """ SELECT * FROM %s WHERE id = %s LIMIT 1 """ \
                        % (sql_table_name, element[ref_field])
                if connection.type == 'import':
                    rel_elements = []
                    cr_host.execute(sql)
                    # cursor to dict
                    columns = [i[0] for i in cr_host.description]
                    for rel_element in cr_host.fetchall():
                        rel_elements.append(dict(zip(columns, rel_element)))
                else:
                    cr.execute(sql)
                    rel_elements = cr.dictfetchall()
                rel_elements = self._prepare_relation_field(cr, uid, ir_model_rel,
                                                            rel_elements, context)

                if rel_elements:
                    rel_element = rel_elements[0]
                    sql = """ SELECT mr.id AS rel_id, mr.fields_sync AS rel_fields_sync
                        FROM db_sync_model_relation mr
                        left join db_sync_model m ON (m.id = mr.model_ref_id )
                        WHERE m.connection_id = %s AND mr.model_id = %s
                        """ \
                        % (connection.id, ir_model_rel.id)
                    cr.execute(sql)
                    mr_ids = cr.dictfetchall()
                    fields_for_sync  =False
                    if mr_ids:
                        mr = self.pool['db.sync.model.relation'].browse(cr, uid, mr_ids[0]['rel_id'])
                        fields_for_sync = mr.fields_sync
                    destination_el_id = self._prepare_destination_id(cr, uid, ids,
                                                ir_model_rel, rel_element, fields_for_sync,
                                                context)

                if destination_el_id:
                    element[ref_field] = destination_el_id
                else:
                    # To create:
                    print "To create"
                    print rel_element
                    # This creation doesn't guarantees that this is the last element
                    context.update({'no_update_counter' : True})
                    el_id = self._add_element(cr, uid, ids, ir_model_rel,
                                              rel_element, context)
                    element[ref_field] = el_id


        return element

    def _add_element(self, cr, uid, ids, ir_model, element, context=None):
        el_id = False

        # Model
        model_obj = self.pool[ir_model.model]

        connection = context.get('connection')
        cr_host = context.get('cr_host')
        uid_host = context.get('uid_host')
        log_id = context.get('log_id')

        if not ir_model:
            return False


        create_date = element.get('create_date')
        write_date = element.get('write_date')
        source_id = element.get('id')

        element.pop("create_uid", None)
        element.pop("create_date", None)
        element.pop("write_date", None)
        element.pop("write_uid", None)
        element.pop("image", None)
        element.pop("image_small", None)
        element.pop("image_medium", None)
        element.pop("id", None)

        #
        if 'parent_left' in element:
            element.pop("parent_left", None)
        if 'parent_right' in element:
            element.pop("parent_right", None)

        # Add property fields before change refs
        sql = """ SELECT * FROM ir_property irp
                        WHERE irp.res_id = '%s'
                        """ \
                        % (ir_model.model + ',' + str(source_id))
        cr_host.execute(sql)
        properties = []
        # cursor to dict
        columns = [i[0] for i in cr_host.description]
        for property in cr_host.fetchall():
            properties.append(dict(zip(columns, property)))
        for property in properties:
            if property['value_reference'] and property['name']:
                p_vals = property['value_reference'].split(',')
                element.update({property['name'] : int(p_vals[1])})
        # Change refs
        #  change all ids of the model senconds rels
        for key in element.keys():
            element = self._change_ref(cr, uid, ids,
                                       ir_model,
                                       element,
                                       key,
                                       context)

        if connection.type == 'import':
            try:
                print element
                el_id = model_obj.create(cr, uid, element, context)
            except Exception, e:
                import pdb
                pdb.set_trace()
                val = {
                    'log_id' : log_id,
                    'model_id' : ir_model.id,
                    'descriptioin' : 'Element id: %s - %s' % (source_id, e[0]),
                }
                self.pool['db.sync.log.line'].create(cr, uid, val)

        # Register relations between local and host element
        rel_id = self.pool['db.sync.model.element'].register(cr, uid,
                                        ir_model.id,
                                        el_id,
                                        source_id,
                                        context)

        # Trace last ref imported
        if not context.get('no_update_counter'):
            domain = [('connection_id', '=', connection.id),
                      ('model_id', '=', ir_model.id)]
            model_counter_ids = self.pool['db.sync.model.counter'].search(
                                                            cr, uid, domain)
            if not model_counter_ids:
                val = {
                    'connection_id': connection.id,
                    'model_id': ir_model.id,
                }
                model_counter_id = self.pool['db.sync.model.counter'].create(
                                                                cr, uid, val)
            else:
                model_counter_id = model_counter_ids[0]

            model_counter = self.pool['db.sync.model.counter'].browse(cr,
                                            uid, model_counter_id)
            last_ref_import = False
            if write_date \
                    and write_date > model_counter.last_ref_imported:
                last_ref_import = write_date
            elif create_date \
                    and create_date > model_counter.last_ref_imported:
                last_ref_import = create_date

            if last_ref_import:
                val = {
                    'last_ref_imported' : last_ref_import
                }
                self.pool['db.sync.model.counter'].write(cr, uid,
                                                    [model_counter_id], val)


        return el_id


    def sync(self, cr, uid, ids, ir_model_id, fields_sync, sql_where,
                                            sql_constraints, context=None):
        '''
        Visto che riceve ir_models sarebbe da estendere ir_model.
        Per ora lascio qui
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'

        ir_model_obj = self.pool['ir.model']

        connection = context.get('connection')
        cr_host = context.get('cr_host')
        uid_host = context.get('uid_host')
        log_id = context.get('log_id')

        #if not model_id and not model_name:
        if not ir_model_id:
            return False

        ir_model = ir_model_obj.browse(cr, uid, ir_model_id)

        el_to_import = self._get_elements_to_sync(cr, uid,
                                                    ir_model,
                                                    'import',
                                                    sql_where,
                                                    sql_constraints,
                                                    context)
        el_to_export = self._get_elements_to_sync(cr, uid,
                                                    ir_model,
                                                    'export',
                                                    sql_where,
                                                    sql_constraints,
                                                    context)
        # Reorder elements
        if el_to_import and 'parent_id' in el_to_import[0]:
            el_to_import = sorted(el_to_import, key=itemgetter('parent_id'))
        # Model
        model_obj = self.pool[ir_model.model]

        # Import
        last_create_date = 0
        last_write_date = 0
        last_host_id = 0
        for element in el_to_import:

            destination_el_id = self._prepare_destination_id(cr, uid, ids,
                                                ir_model, element, fields_sync,
                                                context)

            if ir_model.model == 'res.bank':
                print element

            if destination_el_id:
                continue

            context.update({'no_update_counter' : False})
            el_id = self._add_element(cr, uid, ids, ir_model, element, context)


        return True


class db_sync_log(orm.Model):

    _name = "db.sync.log"
    _description = "DB sync - Log"

    _columns = {
        'connection_id': fields.many2one('db.sync.connection', 'Connection',
                    readonly=True),
        'date': fields.datetime('Date'),
        'line_ids': fields.one2many('db.sync.log.line', 'log_id', 'Log'),
    }
class db_sync_log_line(orm.Model):

    _name = "db.sync.log.line"
    _description = "DB sync - Log line"

    _columns = {
        'log_id': fields.many2one('db.sync.log', 'log',
                    readonly=True),
        'model_id': fields.many2one('ir.model', 'Model Standard',
                    readonly=True),
        'description': fields.text('Description',
                    readonly=True),
    }

class db_sync_model_counter(orm.Model):

    _name = "db.sync.model.counter"
    _description = "DB sync - Model Counter "

    _columns = {
        'connection_id': fields.many2one('db.sync.connection', 'Connection',
                    readonly=True, ondelete="cascade"),
        'model_id': fields.many2one('ir.model', 'Model Standard',
                    readonly=True),
        'last_ref_imported': fields.datetime('Ref Last element imported',
                    ),
        'last_ref_exported': fields.datetime('Ref Last element exported',
                    ),
    }
class db_sync_model_element(orm.Model):

    _name = "db.sync.model.element"
    _description = "DB sync - Model Element"

    _columns = {
        'connection_id': fields.many2one('db.sync.connection', 'Connection',
                    readonly=True, ondelete="cascade"),
        'model_id': fields.many2one('ir.model', 'Model Standard',
                    readonly=True),
        'local_id': fields.integer('Local ID',
                    readonly=True),
        'host_id': fields.integer('Host ID',
                    readonly=True),
        'description': fields.char('Description',
                    readonly=True),
    }

    def get_rel(self, cr, uid, model_id=None, local_id=None, host_id=None,
                                                                context=None):
        connection = context.get('connection')
        if not connection :
            return False
        if not model_id :
            return False
        if not local_id and not host_id:
            return False

        domain = [('connection_id', '=', connection.id),
                  ('model_id', '=', model_id)]
        if local_id:
            domain.append( ('local_id', '=', local_id) )
        if host_id:
            domain.append( ('host_id', '=', host_id) )

        rel_ids = self.search(cr, uid, domain)
        rel =False
        if rel_ids:
            rel = self.browse(cr, uid, rel_ids[0])

        return rel

    def register(self, cr, uid, model_id=None, local_id=None, host_id=None,
                                                                context=None):
        if not model_id or not local_id or not host_id:
            return False

        connection = context.get('connection')
        #Try description
        description = False
        ir_model = self.pool['ir.model'].browse(cr, uid, model_id)
        model = self.pool[ir_model.model].browse(cr, uid, local_id)
        if 'name' in model and model.name:
            description = model.name
        elif 'code' in model and model.code:
            description = model.code
        elif 'name_template' in model and model.name_template:
            description = model.name_template
        elif 'default_code' in model and model.default_code:
            description = model.default_code
        elif 'ref' in model and model.ref:
            description = model.ref
        else:
            description = 'id: %s' % str(local_id)

        val = {
            'connection_id' : connection.id,
            'model_id' : model_id,
            'local_id' : local_id,
            'host_id' : host_id,
            'description' : description or False,
        }
        domain = [('connection_id', '=', connection.id),
                  ('model_id', '=', model_id),
                  ('local_id', '=', local_id)]
        el_ids = self.search(cr, uid, domain)

        if not el_ids:
            el_id = self.create(cr, uid, val)
        else:
            el_id = el_ids[0]
            self.write(cr, uid, [el_id], val)

        return el_id
