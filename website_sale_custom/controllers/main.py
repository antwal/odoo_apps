# -*- coding: utf-8 -*-
import werkzeug

from openerp import SUPERUSER_ID
from openerp import http
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug
from openerp.addons.web.controllers.main import login_redirect

from openerp.addons import website_sale

class website_sale_custom(website_sale.controllers.main.website_sale):

    @http.route('/shop/payment/get_status/<int:sale_order_id>', type='json', auth="public", website=True)
    def payment_get_status(self, sale_order_id, **post):
        cr, uid, context = request.cr, request.uid, request.context

        order = request.registry['sale.order'].browse(cr, SUPERUSER_ID, sale_order_id, context=context)
        assert order.id == request.session.get('sale_last_order_id')

        if not order:
            return {
                'state': 'error',
                'message': '<p>%s</p>' % _('There seems to be an error with your request.'),
            }

        # TODO: Fix

    def checkout_form_validate(self, data):
        res = super(website_sale_custom, self).checkout_form_validate(data)
        if not data.get('vat'):
            res['vat'] = 'missing'
        return res

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True)
    def payment_confirmation(self, **post):
        res = super(website_sale_custom, self).payment_confirmation(**post)

        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.registry['sale.order'].browse(cr, SUPERUSER_ID, sale_order_id, context=context)

            email_template_obj = pool.get('email.template')
            template = pool.get('ir.model.data').get_object(cr, uid, 'sale', 'email_template_edi_sale')

            subject = "subject mail"
            vals = email_template_obj.generate_email(cr, uid, template.id, order.id, context=context)
            vals['subject'] = subject
            vals['email_to'] = order.user_id.email

            email_id = pool.get('mail.mail').create(cr, uid, vals, context)
            pool.get('mail.mail').send(cr, uid, email_id, context)

        return res
