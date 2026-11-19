import json
import unittest
from tests import test_service
from app.address_fields import formatted,normalized


class AddressTests(unittest.TestCase):
    setUp=test_service.RentalTests.setUp
    tearDown=test_service.RentalTests.tearDown

    def parts(self):
        return dict(street='Av. Reforma 123',colony='Centro',postal_code='01234',municipality='Colima',state='Colima',references='Portón azul')

    def test_rental_saves_parts_without_changing_old_address(self):
        parts=self.parts();address=formatted(parts)
        key=self.service.create_rental(self.client,address,'2026-11-05','2026-11-07',{self.item:1},address_data=parts)
        self.assertEqual(self.db.rows('SELECT work_address FROM rentals WHERE id=?',(key,))[0][0],address)
        saved=json.loads(self.db.rows('SELECT data_json FROM address_details WHERE client_id=?',(self.client,))[0][0])
        self.assertEqual(saved,parts)
        self.assertTrue(self.db.rows("SELECT 1 FROM addresses WHERE client_id=? AND address='Obra 1'",(self.client,)))

    def test_client_address_and_optional_references(self):
        parts=self.parts();parts['references']=''
        address=formatted(parts)
        self.service.save_client(self.client,'Ana Pérez','5551234567',None,'',address,address_data=parts)
        self.assertNotIn('Referencias:',address)
        self.assertEqual(normalized(parts)['postal_code'],'01234')
        self.assertTrue(self.db.rows('SELECT 1 FROM address_details WHERE address=?',(address,)))

    def test_invalid_postcode_rolls_back_rental(self):
        parts=self.parts();parts['postal_code']='1234'
        with self.assertRaises(ValueError):
            self.service.create_rental(self.client,formatted(parts),'2026-11-05','2026-11-07',{self.item:1},address_data=parts)
        self.assertFalse(self.db.rows('SELECT * FROM rentals'))
        self.assertEqual(self.db.rows('SELECT available FROM items WHERE id=?',(self.item,))[0][0],5)

    def test_mismatched_parts_are_rejected(self):
        with self.assertRaises(ValueError):
            self.service.create_rental(self.client,'Otra dirección','2026-11-05','2026-11-07',{self.item:1},address_data=self.parts())

    def test_legacy_string_still_supported(self):
        key=self.service.create_rental(self.client,'Obra anterior sin desglose','2026-11-05','2026-11-07',{self.item:1})
        self.assertIn('Obra anterior sin desglose',self.service.note(key))
