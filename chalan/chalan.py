import itertools
import math
from lxml import etree
import time
import openerp
import openerp.service.report
import uuid
import collections
import babel.dates
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class sale_order_chalan(models.Model):
    _name='sale.order'
    _inherit='sale.order',

    @api.model
    def create(self, vals):
        order_serch = self.env['sale.order']
        if vals.get('chalan') == 'chalan':
            print "vals......",self.env['ir.sequence'].get('sale.order.challan'), vals
            vals['chalan_number'] = self.env['ir.sequence'].get('sale.order.challan')
        return super(sale_order_chalan, self).create(vals)

   
    chalan_sequence = fields.Integer(string='Chalan Sequence')
    chalan = fields.Selection([('none','None'),('chalan','Chalan')],'Chalan', help="To describe Chalan", domain=[('chalan', '=', 'chalan')],)
    chalan_desc  = fields.Char('Chalan Discription', size=128)
    chalan_number = fields.Char(string='Chalan Number', domain=[('chalan','==','Chalan')],)
    
    _defaults = {
        'chalan': 'none',
        }