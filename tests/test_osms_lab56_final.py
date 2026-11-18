import unittest
from unittest.mock import Mock, patch
import app as osms


class FakeCursor:
    def __init__(self, one=None, many=None):
        self.one_results = list(one or [])
        self.many_results = list(many or [])
        self.executed = []
        self.lastrowid = 101

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return self.one_results.pop(0) if self.one_results else None

    def fetchall(self):
        return self.many_results.pop(0) if self.many_results else []

class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor
        self.committed = False
        self.closed = False

    def cursor(self, dictionary=False):
        return self.fake_cursor

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


class OSMSUnitTests(unittest.TestCase):
    def setUp(self):
        self.render = patch.object(osms, 'render_template', return_value='TEST_PAGE')
        self.render.start()
        self.audit = patch.object(osms, 'write_audit_log')
        self.audit.start()
        self.addCleanup(patch.stopall)

    def call_route(self, route, url, method='POST', data=None, session_data=None, route_args=None):
        with osms.app.test_request_context(url, method=method, data=data or {}):
            osms.session.clear()
            for key, value in (session_data or {}).items():
                osms.session[key] = value
            return route(**(route_args or {}))

    def test_01_supplier_registration_requires_code_and_name(self):
        cursor = FakeCursor()
        conn = FakeConnection(cursor)
        with patch.object(osms, 'get_connection', return_value=conn):
            result = self.call_route(osms.add_supplier, '/suppliers/add', data={
                'supplier_code': '', 'supplier_name': ''
            })
        self.assertEqual(result, 'TEST_PAGE')
        self.assertFalse(conn.committed)
        osms.render_template.assert_called_with('add_supplier.html', error='Supplier Code and Supplier Name are required.')

    def test_02_supply_registration_rejects_invalid_numbers(self):
        cursor = FakeCursor(many=[[], []])
        conn = FakeConnection(cursor)
        with patch.object(osms, 'get_connection', return_value=conn):
            result = self.call_route(osms.add_supply, '/supplies/add', data={
                'supply_code': 'PEN-001', 'supply_name': 'Ballpen',
                'category_id': '1', 'unit_id': '1',
                'reorder_level': 'abc', 'maximum_stock': '100', 'unit_cost': '5'
            })
        self.assertEqual(result, 'TEST_PAGE')
        self.assertFalse(conn.committed)
        osms.render_template.assert_called_with(
            'add_supply.html', categories=[], units=[],
            error='Reorder Level and Maximum Stock must be whole numbers, and Unit Cost must be a valid number.'
        )

    def test_03_inventory_receipt_rejects_zero_quantity(self):
        cursor = FakeCursor(one=[{'receipt_id': 7, 'supplier_id': 2}], many=[[], []])
        conn = FakeConnection(cursor)
        with patch.object(osms, 'get_connection', return_value=conn):
            result = self.call_route(osms.receipt_items, '/receipts/items/7', data={
                'supply_id': '3', 'quantity': '0', 'unit_cost': '12'
            }, session_data={'user_id': 1}, route_args={'receipt_id': 7})
        self.assertEqual(result, 'TEST_PAGE')
        self.assertFalse(conn.committed)
        osms.render_template.assert_called_with(
            'receipt_items.html', receipt={'receipt_id': 7, 'supplier_id': 2},
            supplies=[], items=[], error='Received quantity must be greater than zero.'
        )

    def test_04_request_creation_rejects_invalid_date(self):
        cursor = FakeCursor(many=[[]])
        conn = FakeConnection(cursor)
        with patch.object(osms, 'get_connection', return_value=conn):
            result = self.call_route(osms.add_request, '/requests/add', data={
                'employee_id': '4', 'request_number': 'REQ-001',
                'request_date': 'not-a-date', 'priority': 'Normal',
                'required_date': '', 'purpose': 'Office use'
            })
        self.assertEqual(result, 'TEST_PAGE')
        self.assertFalse(conn.committed)
        osms.render_template.assert_called_with(
            'add_request.html', employees=[],
            error='Please enter a valid request date and required date.'
        )

    def test_05_approval_rejects_unknown_decision(self):
        cursor = FakeCursor(
            one=[{'status': 'For Approval'}, {'last_id': 0}],
            many=[[{'approval_level': 1}], [{'level_number': 1}]]
        )
        conn = FakeConnection(cursor)
        with patch.object(osms, 'get_connection', return_value=conn):
            result = self.call_route(osms.decide_request, '/requests/decide/9', data={
                'decision': 'Maybe', 'remarks': ''
            }, session_data={'username': 'tester'}, route_args={'request_id': 9})
        self.assertEqual(result.location, '/requests/review/9?msg=invalid_decision')
        self.assertFalse(conn.committed)

    def test_06_issuance_rejects_request_not_approved(self):
        cursor = FakeCursor(one=[{'status': 'For Approval'}])
        conn = FakeConnection(cursor)
        with patch.object(osms, 'get_connection', return_value=conn):
            result = self.call_route(osms.issue_request, '/issuance/issue/9', route_args={'request_id': 9})
        self.assertEqual(result[1], 400)
        self.assertFalse(conn.committed)

    def test_07_stock_deduction_rejects_quantity_above_available_stock(self):
        cursor = FakeCursor(
            one=[
                {'request_id': 9, 'request_number': 'REQ-009', 'status': 'Approved'},
                {'today': '2026-11-03'}
            ],
            many=[[
                {'request_item_id': 5, 'supply_id': 3, 'approved_qty': 10,
                 'issued_qty': 0, 'stock': 4, 'supply_name': 'Bond Paper',
                 'unit_id': 1}
            ]]
        )
        conn = FakeConnection(cursor)
        with patch.object(osms, 'get_connection', return_value=conn):
            result = self.call_route(osms.issue_request, '/issuance/issue/9', data={
                'issued_by': 'Supply Officer', 'issuance_date': '2026-11-01',
                'issue_5': '5'
            }, route_args={'request_id': 9})
        self.assertEqual(result, 'TEST_PAGE')
        self.assertFalse(conn.committed)
        osms.render_template.assert_called_with(
            'issue_request.html',
            req={'request_id': 9, 'request_number': 'REQ-009', 'status': 'Approved'},
            items=[{
                'request_item_id': 5, 'supply_id': 3, 'approved_qty': 10,
                'issued_qty': 0, 'stock': 4, 'supply_name': 'Bond Paper',
                'unit_id': 1, 'remaining': 10, 'max_issue': 4, 'issue_qty': 5
            }],
            error='Cannot issue 5 of Bond Paper. Only 4 in stock.',
            today='2026-11-03'
        )

    def test_08_stock_adjustment_prevents_negative_inventory(self):
        cursor = FakeCursor(
            one=[{'supply_id': 3}, {'current_stock': 2}],
            many=[[], []]
        )
        conn = FakeConnection(cursor)
        with patch.object(osms, 'get_connection', return_value=conn):
            result = self.call_route(osms.stock_adjustments, '/inventory/adjustments', data={
                'supply_id': '3', 'direction': 'Decrease', 'quantity': '3',
                'reason': 'Correction', 'adjusted_by': 'Inventory Clerk',
                'remarks': 'Physical count correction'
            })
        self.assertEqual(result, 'TEST_PAGE')
        self.assertFalse(conn.committed)
        osms.render_template.assert_called_with(
            'stock_adjustments.html', supplies=[], adjustments=[],
            error='This adjustment would make stock negative. Current stock is 2.'
        )

    def test_09_inventory_report_calculates_totals(self):
        cursor = FakeCursor(many=[[
            {'supply_code': 'PEN-001', 'supply_name': 'Ballpen',
             'reorder_level': 10, 'unit_cost': 5, 'status': 'Active',
             'category_name': 'Writing', 'unit_name': 'Piece',
             'stock': 8, 'stock_value': 40},
            {'supply_code': 'PPR-001', 'supply_name': 'Bond Paper',
             'reorder_level': 5, 'unit_cost': 2, 'status': 'Active',
             'category_name': 'Paper', 'unit_name': 'Ream',
             'stock': 0, 'stock_value': 0}
        ]])
        conn = FakeConnection(cursor)
        with patch.object(osms, 'get_connection', return_value=conn):
            result = self.call_route(osms.inventory_report, '/reports/inventory', method='GET')
        self.assertEqual(result, 'TEST_PAGE')
        kwargs = osms.render_template.call_args.kwargs
        self.assertEqual(kwargs['total_units'], 8)
        self.assertEqual(kwargs['total_value'], 40)
        self.assertEqual(len(kwargs['low_stock']), 1)
        self.assertEqual(len(kwargs['out_of_stock']), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
