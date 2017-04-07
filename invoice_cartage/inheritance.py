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
	_inherit="account.invoice"


  #  @api.multi
	def _compute_residual(self):
		residual = 0.0
        residual_company_signed = 0.0
        self.sign = sign
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        for line in self.sudo().move_id.line_ids:
            if line.account_id.internal_type in ('receivable', 'payable'):
                residual_company_signed += line.amount_residual
                print"=========residual_company_signed==========",residual_company_signed

                if line.currency_id == self.currency_id:
                    residual += line.amount_residual_currency if line.currency_id else line.amount_residual
                    print"=========residual==========",residual
                else:
                    from_currency = (line.currency_id and line.currency_id.with_context(date=line.date)) or line.company_id.currency_id.with_context(date=line.date)
                    residual += from_currency.compute(line.amount_residual, self.currency_id)
        self.residual_company_signed = abs(residual_company_signed) * sign
        self.residual_signed = abs(residual) * sign
        self.residual = abs(residual)
        digits_rounding_precision = self.currency_id.rounding
        if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
            self.reconciled = True
        else:
            self.reconciled = False



	@api.model
	def create(self, vals):
	#	vals = {}
		order_serch = self.env['account.invoice']
		if vals.get('cash_credit') == 'cash_invoice':
			print "vals......",self.env['ir.sequence'].get('account.invoice.cashs'), vals
			vals['serial_number'] = self.env['ir.sequence'].get('account.invoice.cashs') or '/'
			print"======vals['serial_number']=======",vals['serial_number']
		
		elif vals.get('cash_credit') == 'credit_invoice':
			print "vals......",self.env['ir.sequence'].get('account.invoice.credits'), vals
			vals['serial_number'] = self.env['ir.sequence'].get('account.invoice.credits') or '/'
			print"======vals['serial_number']=======",vals['serial_number']

		return super(account_invoice_cashs, self).create(vals)


    


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
	cash_credit = fields.Selection([('cash_invoice', 'Cash'),('credit_invoice', 'Credit')], string='Mode Of Payment', required=False)
	serial_number = fields.Char(string='Serial Number', copy=True)
	debit_sequence = fields.Integer(string = 'Debit Sequence')
	penalty_date = fields.Date(string='Penalty Date')

	reconciled = fields.Boolean(string='Paid/Reconciled', store=True, readonly=True, compute='_compute_residual')
	residual = fields.Monetary(string='Amount Due', compute='_compute_residual', store=True)
	residual_signed = fields.Monetary(string='Amount Due', currency_field='currency_id', compute='_compute_residual', store=True)
	residual_company_signed = fields.Monetary(string='Amount Due', currency_field='company_currency_id', compute='_compute_residual', store=True)

	type = fields.Selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Vendor Bill'),
            ('out_refund','Customer Refund'),
            ('in_refund','Vendor Refund'),
        ], readonly=True, index=True, change_default=True,
        default=lambda self: self._context.get('type', 'out_invoice'),
        track_visibility='always')
#	'previous_balance':fields.boolean('Show Balance', help="Show User balance on bill"),
	
















# class product_exchange(osv.osv_memory):
#     _name = "product.exchange"
#     _columns ={
#                'name': fields.char('Name', size=256),
#                'claim_return_id':fields.float('Claim retrun Id', readonly=False),
        
#                }  
