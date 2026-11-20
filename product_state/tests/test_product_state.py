# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase

from .. import post_init_hook

_logger = logging.getLogger(__name__)


class TestProductState(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProductState = cls.env["product.state"]
        cls.state_test = cls.ProductState.create({"name": "State Test", "code": "Test"})
        cls.state_sellable = cls.env.ref("product_state.product_state_sellable")
        cls.product_obj = cls.env["product.template"]

    @classmethod
    def _create_product(cls, state=None):
        vals = {"name": "Product Test for State"}
        if state:
            vals.update({"product_state_id": state.id})
        cls.created_product = cls.product_obj.create(vals)

    def test_01_product_state(self):
        """
        Check if new state has no products
        Create a product, check if it has the default state
        Create a product with state
        Check if new state has 1 product
        """
        self.assertEqual(self.state_test.products_count, 0)
        self._create_product()
        self.assertEqual(self.created_product.product_state_id, self.state_sellable)
        self.assertEqual(self.state_test.products_count, 0)
        self._create_product(self.state_test)
        self.assertEqual(self.created_product.product_state_id, self.state_test)
        self.assertEqual(self.state_test.products_count, 1)

    def test_02_set_product_state(self):
        """
        Create product, it has default state
        Then, update the state
        It should have the existing one (Test)
        """
        self._create_product()
        self.assertEqual(self.created_product.product_state_id, self.state_sellable)
        self.created_product.state = "Test"
        self.assertEqual(self.created_product.product_state_id, self.state_test)

    def test_03_set_constrains_product_state(self):
        """
        Create another default state,
        It should have the existing only one default state at time
        """
        with self.assertRaisesRegex(
            ValidationError, "There should be only one default state"
        ):
            self.env["product.state"].create(
                {"name": "Default State 2", "code": "df2", "default": True}
            )

    def test_04_invalid_state(self):
        self._create_product()
        with self.assertRaisesRegex(
            UserError, "The product state code new_code could not be found."
        ):
            self.created_product.state = "new_code"

    def test_05_copy(self):
        """
        Create product with non-default state.
        Copy product.
        The copy should have the default state.
        """
        self._create_product()
        self.created_product.state = "Test"
        copied_product = self.created_product.copy()
        self.assertEqual(copied_product.product_state_id, self.state_sellable)

    def test_06_post_init_hook(self):
        """
        Create a product without state.
        Run the post init hook.
        It should get the default state.
        """
        product = self.product_obj.create(
            {"name": "Product without state", "product_state_id": False}
        )
        self.assertFalse(product.product_state_id)
        self.assertFalse(product.state)
        post_init_hook(self.env)
        product.invalidate_recordset()
        self.assertEqual(product.product_state_id, self.state_sellable)
        self.assertEqual(product.state, "sellable")

    def test_07_post_init_hook_uses_default_state(self):
        """
        Change the default state.
        Create a product without state and run the post init hook.
        It should get the new default state, not the sellable one.
        """
        self.state_sellable.default = False
        default_state = self.ProductState.create(
            {"name": "Custom Default", "code": "custom_default", "default": True}
        )
        product = self.product_obj.create(
            {"name": "Product without state", "product_state_id": False}
        )
        post_init_hook(self.env)
        product.invalidate_recordset()
        self.assertEqual(product.product_state_id, default_state)
        self.assertEqual(product.state, "custom_default")
