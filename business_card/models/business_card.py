# -*- coding: utf-8 -*-

from odoo import models, fields, api ,_


class BusinessCard(models.Model):
    _name = 'business.card'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'rating.mixin']

    name = fields.Char(string='Req.No', copy=False, readonly=True, index=True, default=lambda self: _('New'),
                       required=True, track_visibility='always')
    employee_name = fields.Many2one('hr.employee', string="Employee", track_visibility='always', readonly=True,
                                    default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1))
    employee_full_name = fields.Char(string="Employee Full Name", related='employee_name.employee_full_name')
    employee_email = fields.Char(string="Email", related='employee_name.work_email')
    job_name = fields.Many2one('hr.job', related='employee_name.job_id')
    department_name = fields.Many2one('hr.department', related='employee_name.department_id')
    employee_phone = fields.Char(string="Mobile Phone", related='employee_name.mobile_phone')
    create_date = fields.Date(string='Created On', default=fields.Date.today(), readonly=True)
    reject_reason = fields.Text(string='Reject Reason')

    state = fields.Selection([
        ('wfa', "Waiting For Approve"),
        ('hr', "HR Department"),
        ('rejected', "Rejected"),
        ('done', "Done")
    ], default='wfa', string="Stage", track_visibility='onchange')

    def hr_department(self):
        self.state = 'hr'

    def reject(self, **additional_values):
        template = self.env.ref('business_card.mail_template_reject_business_card')
        self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True, raise_exception=True)

        return self.write({'state': 'rejected',
                           'reject_reason': additional_values.get('reject_reason')})

    def done(self):
        template = self.env.ref('business_card.mail_template_done_business_card')
        self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True, raise_exception=True)
        self.state = 'done'

    @api.model
    def get_email_to(self):
        user_group = self.env.ref("business_card.business_card_hr_group")
        email_list = [
            usr.partner_id.email for usr in user_group.users if usr.partner_id.email]
        return ",".join(email_list)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq = self.env['ir.sequence'].next_by_code('business.card') or '/'
            vals['name'] = seq
        res = super(BusinessCard, self).create(vals)
        template = self.env.ref('business_card.mail_template_business_card')
        self.env['mail.template'].browse(template.id).send_mail(res.id, force_send=True, raise_exception=True)
        return res


class RejectMessagebusinessCard(models.TransientModel):
    _name = 'reject.message.business.card'

    reject_reason = fields.Text('Reject Reason')

    def action_reject_reason(self):
        business_card = self.env['business.card'].browse(self.env.context.get('active_ids'))
        return business_card.reject(reject_reason=self.reject_reason)

