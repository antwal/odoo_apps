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
from datetime import datetime, time, timedelta
from openerp import netsvc
from openerp import tools

class product_template(orm.Model):
    _inherit="product.template"

    _columns = {
        'sale_brand_id': fields.many2one('sale.brand', 'Brand',
            help="""Sale Brand"""
        ),
    }

class sale_brand(orm.Model):

    _name = "sale.brand"
    _description = "Sale Brand"

    def _get_image(self, cr, uid, ids, name, args, context=None):
        result = dict.fromkeys(ids, False)
        for obj in self.browse(cr, uid, ids, context=context):
            result[obj.id] = tools.image_get_resized_images(obj.image, avoid_resize_medium=True)
        return result

    def _set_image(self, cr, uid, id, name, value, args, context=None):
        return self.write(cr, uid, [id], {'image': tools.image_resize_image_big(value)}, context=context)

    _columns = {
        'active': fields.boolean('Active', readonly=True),
        'name': fields.char('Name'),
        'description': fields.text('Description'),
        'image': fields.binary("Image",
            help="This field holds the image used as image for the product, limited to 1024x1024px."),
        'image_medium': fields.function(_get_image, fnct_inv=_set_image,
            string="Medium-sized image", type="binary", multi="_get_image",
            store={
                'sale.brand': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Medium-sized image of the product. It is automatically "\
                 "resized as a 128x128px image, with aspect ratio preserved, "\
                 "only when the image exceeds one of those sizes. Use this field in form views or some kanban views."),
        'image_small': fields.function(_get_image, fnct_inv=_set_image,
            string="Small-sized image", type="binary", multi="_get_image",
            store={
                'sale.brand': (lambda self, cr, uid, ids, c={}: ids, ['image'], 10),
            },
            help="Small-sized image of the product. It is automatically "\
                 "resized as a 64x64px image, with aspect ratio preserved. "\
                 "Use this field anywhere a small image is required."),

    }

    _defaults = {
        'active': True
    }
