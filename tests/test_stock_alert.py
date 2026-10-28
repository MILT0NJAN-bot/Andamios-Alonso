import unittest
from unittest.mock import patch
from tests import test_service
from app.desktop import Application


class StockAlertTests(unittest.TestCase):
    setUp = test_service.RentalTests.setUp
    tearDown = test_service.RentalTests.tearDown

    def test_warn_only_when_rented_item_reaches_zero(self):
        key = self.service.create_rental(self.client,'Obra','2026-10-14','2026-10-17',{self.item:4})
        with patch('app.desktop.messagebox.showwarning') as warning:
            Application.notify_exhausted_stock(self,key)
            warning.assert_not_called()
            key = self.service.create_rental(self.client,'Obra','2026-10-14','2026-10-17',{self.item:1})
            Application.notify_exhausted_stock(self,key)
            warning.assert_called_once()
            self.assertIn('Equipo',warning.call_args.args[1])
            self.assertIn('Disponibles: 0',warning.call_args.args[1])
            self.service.return_rental(key)
            warning.reset_mock()
            Application.notify_exhausted_stock(self,key)
            warning.assert_not_called()
