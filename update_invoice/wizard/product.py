# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductExternalID(models.TransientModel):
    _name = 'product.external.id'

    def calculate_product_external_id(self):
        """Remove prduct name in description sale."""
        templates = self.env['product.template'].search([])
        modeldata = self.env['ir.model.data']
        for template in templates:
            print (template)
            product = self.env['product.product'].search([('product_tmpl_id', '=', template.id)])
            template_model = template.get_external_id()[template.id]
            product_model = product.get_external_id()[product.id]
            print ("template>>>>>>>>>>>>>>>", template_model, product_model)
            if template_model and not product_model:
                external_id = template_model.split('.')
                modeldata.create({'model': 'product.product',
                                  'res_id': product.id,
                                  'module': external_id[0],
                                  'name': 'p_id_' + external_id[1]})
