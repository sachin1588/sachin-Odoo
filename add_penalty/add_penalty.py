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
 
class add_penalty(models.Model):
    _name = 'add.penalty'


    @api.multi
    def test_amount(self):
        print"=======test_amount====="
        res = {}
        date_diff = 0
        now = datetime.now()
        print"=======now=====",now
        now = now.strftime('%Y-%m-%d')
        date_now = datetime.strptime(now,'%Y-%m-%d')
        dt = date_now
        name = 'CD Break'
        # comment = 'Write-Off'
        # cd_flag = True
        # tname = 'None'
        # qty = 1
        # rate = 1.00
        # amount = 0.0
        # amt = 0.0
        # pay_option = 'without_writeoff'
        # mline_state = 'valid'
        # move_state = 'draft'
        # ptype = 'dr'
        # v_state = 'draft'
        # v_type = 'sale'  
        # cartageflag = 'true'       
        # seq_id = self.env['ir.sequence'].search([('name','=','Sales Journal')])[0]
        # vnumber = self.env['ir.sequence'].next_by_id(seq_id)
        # ref = vnumber.replace('/','')
        account_invoice = self.env['account.invoice'].search([])
        print"======account_invoice=======",account_invoice
        
        for case in account_invoice:
            self.env.cr.execute('select * from account_invoice where partner_id ='+str(case.partner_id.id))
            account_invoices = account_invoice.browse(ids = map(lambda x: x[0], self.env.cr.fetchall()))
            print"=======account_invoicesaccount_invoices=====",account_invoices
            for inv in account_invoices:
                if (inv.penalty_date):
                    dt = datetime.strptime(inv.penalty_date,'%Y-%m-%d')
                    print"=======dt=====",dt


        return res
    
    # @api.model
    # def button_compute(self):
    #     for line in self.browse(self):
    #         if set_total:
    #             self.env['add.penalty'].write(cr, uid, [line.id], {'name': line.name})
    #     return True

    partner_id = fields.Many2one('res.partner', string = 'Partner Name')
    invoice_id = fields.Many2one('account.invoice', string ='Partner Invoice', domain=[('state', '=', 'open')],)
    test = fields.Integer(string ='Grand Total', store = True)
            
    
    
 
 
    