# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from . import models
from odoo.orm.domains import Domain


def post_init_hook(env):
    """Add a state on existing products"""
    tmpl_obj = env["product.template"].with_context(active_test=False)
    tmpl_without_state_id = tmpl_obj.search(Domain("product_state_id", "=", False))
    tmpl_without_state_id.filtered("state")._inverse_product_state()
    tmpl_without_state_id = tmpl_obj.search(Domain("product_state_id", "=", False))
    default_state = tmpl_obj._get_default_product_state()
    if default_state:
        tmpl_without_state_id.write({"product_state_id": default_state.id})
