odoo.define('nshore_customization.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var pos_models = models.PosModel.prototype.models;

    for(var i=0; i<pos_models.length; i++){
        var model=pos_models[i];
        if(model.model === 'res.company'){
             model.fields.push('street', 'street2', 'zip', 'state_id', 'city');
        }
        if(model.model === 'res.partner'){
             model.fields.push('property_payment_term_id','ref');
        }
    }

});