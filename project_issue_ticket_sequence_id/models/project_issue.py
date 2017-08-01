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
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import models, fields, api, _


class project_issue(models.Model):
    _inherit = 'project.issue'

    @api.one
    def _task_ref(self):
        number = self.env['ir.sequence'].get('project.issue.ticket')
        ref = ''
        if self.user_id.partner_id.ticket_prefix:
            ref += '%s' % self.user_id.partner_id.ticket_prefix
        if self.partner_id.ticket_ref:
            if ref :
                ref += '_%s' % self.partner_id.ticket_ref
            else:
                ref += '%s' % self.partner_id.ticket_ref
        if number:
            if ref :
                ref += '_%s' % number
            else:
                ref += '%s' % number
        self.ticket_ref = ref

    ticket_ref = fields.Char(string='Ticket ID', readonly=True)

    @api.model
    def create(self, vals):
        res = super(project_issue, self).create(vals)
        res._task_ref()
        return res


    def message_post(self, cr, uid, thread_id, body='', subject=None, type='notification',
                     subtype=None, parent_id=False, attachments=None, context=None,
                     content_subtype='html', **kwargs):
        if context.get('params', False):
            params = context.get('params')
            issue_id = params.get('id', False)
            if issue_id:
                issue = self.pool['project.issue'].browse(cr, uid, issue_id)
                ticket_ref = issue.ticket_ref or ''
                if ticket_ref:
                    subject = '%s: %s' % (_('Ticket ref'), ticket_ref)

        return super(project_issue, self).message_post(
            cr, uid, thread_id, body, subject, type, subtype, parent_id,
            attachments, context, content_subtype, **kwargs)
