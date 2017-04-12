import json
from lxml import etree
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp import api, fields, models, _
from openerp.tools import float_is_zero, float_compare
from openerp.tools.misc import formatLang
from openerp.exceptions import UserError, RedirectWarning, ValidationError
import openerp.addons.decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)
import datetime


class account_invoice_cashs(models.Model):
    _name = "account.invoice"
    _inherit = "account.invoice"

    # @api.one
    # @api.depends(
    # 'state', 'currency_id', 'invoice_line_ids.price_subtotal',
    # 'move_id.line_ids.amount_residual',
    # 'move_id.line_ids.currency_id')
    # def _compute_residual(self):
    #     residual = 0.0
    #     residual_company_signed = 0.0
    #     sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
    #     for line in self.sudo().move_id.line_ids:
    #         if line.account_id.internal_type in ('receivable', 'payable'):
    #             residual_company_signed += line.amount_residual
    #             if line.currency_id == self.currency_id:
    #                 residual += line.amount_residual_currency if line.currency_id else line.amount_residual
    #             else:
    #                 from_currency = (line.currency_id and line.currency_id.with_context(
    #                     date=line.date)) or line.company_id.currency_id.with_context(date=line.date)
    #                 residual += from_currency.compute(line.amount_residual, self.currency_id)
    #     self.residual_company_signed = abs(residual_company_signed) * sign
    #
    #     #residual += self.cartage + self.labour
    #     self.residual_signed = abs(residual) * sign
    #     self.residual = abs(residual)
    #     digits_rounding_precision = self.currency_id.rounding
    #     if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
    #         self.reconciled = True
    #     else:
    #         self.reconciled = False

    @api.model
    def create(self, vals):
        #	vals = {}
        order_serch = self.env['account.invoice']
        if vals.get('cash_credit') == 'cash_invoice':
            vals['serial_number'] = self.env['ir.sequence'].get('account.invoice.cashs') or '/'
            print"======vals['serial_number']=======", vals['serial_number']

        elif vals.get('cash_credit') == 'credit_invoice':
            vals['serial_number'] = self.env['ir.sequence'].get('account.invoice.credits') or '/'
            print"======vals['serial_number']=======", vals['serial_number']

        return super(account_invoice_cashs, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('cash_credit') == 'cash_invoice':
            vals['serial_number'] = self.env['ir.sequence'].get('account.invoice.cashs') or '/'
            print"======vals['serial_number']=======", vals['serial_number']

        elif vals.get('cash_credit') == 'credit_invoice':
            vals['serial_number'] = self.env['ir.sequence'].get('account.invoice.credits') or '/'
            print"======vals['serial_number']=======", vals['serial_number']

        return super(account_invoice_cashs, self).write(vals)


    def _compute_amount(self):
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(line.amount for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax + self.cartage + self.labour
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.currency_id != self.company_id.currency_id:
            amount_total_company_signed = self.currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = self.currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign

    cartage = fields.Float(string='Cartage', digits=dp.get_precision('Product Price'))
    labour = fields.Float(string='Labour', digits=dp.get_precision('Product Price'))
    cash_credit = fields.Selection([('cash_invoice', 'Cash'), ('credit_invoice', 'Credit')], string='Mode Of Payment',
                                   required=False, copy=False)
    serial_number = fields.Char(string='Serial Number', copy=False)
    debit_sequence = fields.Integer(string='Debit Sequence')
    penalty_date = fields.Date(string='Penalty Date')

    # reconciled = fields.Boolean(string='Paid/Reconciled', store=True, readonly=True, compute='_compute_residual')
    # residual = fields.Monetary(string='Amount Due', compute='_compute_residual', store=True)
    # residual_signed = fields.Monetary(string='Amount Due', currency_field='currency_id', compute='_compute_residual',
    #                                   store=True)
    # residual_company_signed = fields.Monetary(string='Amount Due', currency_field='company_currency_id',
    #                                           compute='_compute_residual', store=True)

    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(_('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids:
                raise UserError(_('Please create some invoice lines.'))
            if inv.move_id:
                continue

            ctx = dict(self._context, lang=inv.partner_id.lang)

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            date_invoice = inv.date_invoice
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()



            diff_currency = inv.currency_id != company_currency

            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)

            # here creating an additional journal entry if cartage and Labour Exist
            if inv.cartage or inv.labour:
                 iml.append({
                    'type': 'src',
                    'name': 'Cartage And Labour',
                    'price': -(inv.cartage+inv.labour),
                    'price_unit' : inv.cartage+inv.labour,
                    'account_id': self.env['account.account'].search([('name','=','Local Services')], limit=1).id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and company_currency.with_context(ctx).compute(inv.cartage+inv.labour, inv.currency_id),
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id,
                    'quantity': 1.0,
                })

            name = inv.name or '/'
            if inv.payment_term_id:
                totlines = inv.with_context(ctx).payment_term_id.with_context(currency_id=inv.currency_id.id).compute(total, date_invoice)[0]
                res_amount_currency = total_currency
                ctx['date'] = date_invoice
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1]+inv.cartage+inv.labour, inv.currency_id)
                    else:
                        amount_currency = False

                    # last line: add the diff
                    res_amount_currency -= amount_currency or 0
                    if i + 1 == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1] + company_currency.with_context(ctx).compute(inv.cartage+inv.labour, inv.currency_id),
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total + inv.cartage+inv.labour,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency + company_currency.with_context(ctx).compute(inv.cartage+inv.labour, inv.currency_id),
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id
                })


            print "IML....",iml

            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            line = inv.group_lines(iml, line)




            journal = inv.journal_id.with_context(ctx)
            line = inv.finalize_invoice_move_lines(line)

            date = inv.date or date_invoice
            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': journal.id,
                'date': date,
                'narration': inv.comment,
            }
            ctx['company_id'] = inv.company_id.id
            ctx['dont_create_taxes'] = True
            ctx['invoice'] = inv
            ctx_nolang = ctx.copy()
            ctx_nolang.pop('lang', None)
            move = account_move.with_context(ctx_nolang).create(move_vals)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move.post()
            # make the invoice point to that move
            vals = {
                'move_id': move.id,
                'date': date,
                'move_name': move.name,
            }
            inv.with_context(ctx).write(vals)
        return True

    @api.multi
    def invoice_print_custom(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        return self.env['report'].get_action(self, 'invoice_cartage.report_invoice_list')

















# class product_exchange(osv.osv_memory):
#     _name = "product.exchange"
#     _columns ={
#                'name': fields.char('Name', size=256),
#                'claim_return_id':fields.float('Claim retrun Id', readonly=False),

#                }
