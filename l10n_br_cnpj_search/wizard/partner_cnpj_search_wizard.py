from erpbrasil.base.fiscal import cnpj_cpf
from erpbrasil.base.misc import punctuation_rm
from requests import get

from odoo import api, fields, models


class PartnerCnpjSearchWizard(models.TransientModel):
    _name = "partner.search.wizard"

    partner_id = fields.Char()
    provider_name = fields.Char()
    cnpj_cpf = fields.Char()
    legal_name = fields.Char()
    name = fields.Char()
    inscr_est = fields.Char()
    zip = fields.Char()
    street_name = fields.Char()
    street_number = fields.Char()
    street2 = fields.Char()
    district = fields.Char()
    state_id = fields.Many2one(comodel_name="res.country.state")
    city_id = fields.Many2one(
        comodel_name="res.city",
        domain="[('state_id', '=', state_id)]",
    )
    country_id = fields.Many2one(comodel_name="res.country")
    phone = fields.Char()
    mobile = fields.Char()
    email = fields.Char()
    legal_nature = fields.Char()
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.ref("base.BRL"),
    )
    equity_capital = fields.Monetary(currency_field="currency_id")
    cnae_main_id = fields.Many2one(comodel_name="l10n_br_fiscal.cnae")
    cnae_secondary_ids = fields.Many2many(
        comodel_name="l10n_br_fiscal.cnae",
        relation="wizard_fiscal_cnae_rel",
        column1="company_id",
        column2="cnae_id",
    )

    @api.onchange("cnpj_cpf")
    def _onchange_cnpj_cpf(self):
        self.cnpj_cpf = cnpj_cpf.formata(str(self.cnpj_cpf))

    def _get_partner_values(self, cnpj_cpf):
        webservice = self.env["l10n_br_cnpj_search.webservice.abstract"]
        webservice.get_provider()
        response = get(
            webservice.get_api_url(cnpj_cpf), headers=webservice.get_headers()
        )

        data = webservice.validate(response)
        values = webservice.import_data(data)
        return values

    def default_get(self, fields):
        res = super(PartnerCnpjSearchWizard, self).default_get(fields)
        partner_id = self._context.get("default_partner_id")

        partner_model = self.env["res.company"]
        if not partner_model.browse(partner_id).exists():
            partner_model = self.env["res.partner"]

        partner = partner_model.browse(partner_id)

        cnpj_cpf = punctuation_rm(partner.cnpj_cpf)
        webservice_instance = self.env["l10n_br_cnpj_search.webservice.abstract"]

        provider_name = webservice_instance.get_provider()
        values = self._get_partner_values(cnpj_cpf)
        cnae_secondary_ids = [(6, 0, values.get("cnae_secondary_ids", []))]

        res.update(
            {
                "legal_name": values.get("legal_name", ""),
                "name": values.get("name", ""),
                "cnpj_cpf": cnpj_cpf,
                "inscr_est": values.get("inscr_est", ""),
                "zip": values.get("zip", ""),
                "street_name": values.get("street_name", ""),
                "street_number": values.get("street_number", ""),
                "street2": values.get("street2", ""),
                "district": values.get("district", ""),
                "state_id": values.get("state_id", ""),
                "city_id": values.get("city_id", ""),
                "country_id": values.get("country_id", ""),
                "phone": values.get("phone", ""),
                "mobile": values.get("mobile", ""),
                "email": values.get("email", ""),
                "legal_nature": values.get("legal_nature", ""),
                "equity_capital": values.get("equity_capital", 0.0),
                "cnae_main_id": values.get("cnae_main_id", ""),
                "cnae_secondary_ids": cnae_secondary_ids,
                "provider_name": provider_name,
            }
        )
        return res

    def action_update_partner(self):
        partner_id = self._context.get("default_partner_id")

        partner_model = self.env["res.company"]
        if not partner_model.browse(partner_id).exists():
            partner_model = self.env["res.partner"]

        partner = partner_model.browse(partner_id)

        values_to_update = {
            "legal_name": self.legal_name,
            "name": self.name,
            "inscr_est": self.inscr_est,
            "zip": self.zip,
            "street_name": self.street_name,
            "street_number": self.street_number,
            "street2": self.street2,
            "district": self.district,
            "state_id": self.state_id.id,
            "city_id": self.city_id.id,
            "country_id": self.country_id.id,
            "phone": self.phone,
            "mobile": self.mobile,
            "email": self.email,
            "legal_nature": self.legal_nature,
            "equity_capital": self.equity_capital,
            "cnae_main_id": self.cnae_main_id,
            "cnae_secondary_ids": self.cnae_secondary_ids,
        }
        non_empty_values = {
            key: value for key, value in values_to_update.items() if value
        }
        if non_empty_values:
            # Update partner only if there are non-empty values
            partner.write(non_empty_values)
        return {"type": "ir.actions.act_window_close"}
