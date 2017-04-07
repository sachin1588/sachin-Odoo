{
"name" : "Invoice order Inherit",
"version" : "1.1",
"author" : "Evon Technologies",
"category" : "Generic Modules/Account",
"website" : "http://www.evontech.com",
"description": "Module to inherit sales order view.",
"depends" : ["account"],
"init_xml" : [],
"update_xml" : ["invoice_order_form_inherit_view.xml", 
              #  "security/ir_security.xml"
                ],
"active": False,
"installable": True
}