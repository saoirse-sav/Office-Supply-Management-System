from flask import Flask, render_template, request, redirect
from db import get_connection

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/categories')
def categories():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    search = request.args.get('search', '') 
    if search: 
        cursor.execute('SELECT * FROM supply_categories WHERE category_name LIKE %s', ('%' + search + '%',)) 
    else: 
        cursor.execute('SELECT * FROM supply_categories')
    all_categories = cursor.fetchall()
    conn.close()
    return render_template('categories.html', categories=all_categories)

@app.route('/categories/add', methods=['GET', 'POST'])
def add_category(): 
    if request.method == 'POST': 
        name = request.form['category_name'] 
        description = request.form['description'] 
        conn = get_connection() 
        cursor = conn.cursor() 
        cursor.execute('INSERT INTO supply_categories (category_name, description) VALUES (%s, %s)', (name, description)) 
        conn.commit() 
        conn.close() 
        return redirect('/categories') 
    return render_template('add_category.html')

@app.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    if request.method == 'POST': 
        name = request.form['category_name'] 
        description = request.form['description'] 
        cursor.execute('UPDATE supply_categories SET category_name=%s, description=%s WHERE category_id=%s', (name, description, category_id)) 
        conn.commit() 
        conn.close() 
        return redirect('/categories') 
    cursor.execute('SELECT * FROM supply_categories WHERE category_id=%s', (category_id,)) 
    category = cursor.fetchone() 
    conn.close() 
    return render_template('edit_category.html', category=category)

@app.route('/categories/delete/<int:category_id>') 
def delete_category(category_id): 
    conn = get_connection() 
    cursor = conn.cursor() 
    cursor.execute('DELETE FROM supply_categories WHERE category_id=%s', (category_id,)) 
    conn.commit() 
    conn.close() 
    return redirect('/categories')

@app.route('/categories/toggle/<int:category_id>') 
def toggle_category(category_id): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    cursor.execute('SELECT status FROM supply_categories WHERE category_id=%s', (category_id,)) 
    current = cursor.fetchone() 
    new_status = 'Inactive' if current['status'] == 'Active' else 'Active' 
    cursor.execute('UPDATE supply_categories SET status=%s WHERE category_id=%s', (new_status, category_id)) 
    conn.commit() 
    conn.close() 
    return redirect('/categories')

@app.route('/units') 
def units(): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    search = request.args.get('search', '') 
    if search: 
        cursor.execute('SELECT * FROM units WHERE unit_name LIKE %s', ('%' + search + '%',)) 
    else: cursor.execute('SELECT * FROM units') 
    all_units = cursor.fetchall() 
    conn.close() 
    return render_template('units.html', units=all_units) 

@app.route('/units/add', methods=['GET', 'POST']) 
def add_unit(): 
    if request.method == 'POST': 
        name = request.form['unit_name'] 
        conn = get_connection() 
        cursor = conn.cursor() 
        cursor.execute('INSERT INTO units (unit_name) VALUES (%s)', (name,)) 
        conn.commit() 
        conn.close() 
        return redirect('/units')   
    return render_template('add_unit.html') 

@app.route('/units/edit/<int:unit_id>', methods=['GET', 'POST']) 
def edit_unit(unit_id): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    if request.method == 'POST': 
        name = request.form['unit_name'] 
        cursor.execute('UPDATE units SET unit_name=%s WHERE unit_id=%s', (name, unit_id)) 
        conn.commit() 
        conn.close() 
        return redirect('/units') 
    cursor.execute('SELECT * FROM units WHERE unit_id=%s', (unit_id,)) 
    unit = cursor.fetchone() 
    conn.close() 
    return render_template('edit_unit.html', unit=unit) 

@app.route('/units/delete/<int:unit_id>') 
def delete_unit(unit_id): 
    conn = get_connection() 
    cursor = conn.cursor() 
    cursor.execute('DELETE FROM units WHERE unit_id=%s', (unit_id,)) 
    conn.commit() 
    conn.close() 
    return redirect('/units') 

@app.route('/units/toggle/<int:unit_id>') 
def toggle_unit(unit_id): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    cursor.execute('SELECT status FROM units WHERE unit_id=%s', (unit_id,)) 
    current = cursor.fetchone() 
    new_status = 'Inactive' if current['status'] == 'Active' else 'Active' 
    cursor.execute('UPDATE units SET status=%s WHERE unit_id=%s', (new_status, unit_id)) 
    conn.commit() 
    conn.close() 
    return redirect('/units')

@app.route('/supplies')
def supplies():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    search = request.args.get('search', '')
    unit_filter = request.args.get('unit_id', '')
    status_filter = request.args.get('status', '')
    stock_filter = request.args.get('stock_level', '')
    query = 'SELECT supplies.*, supply_categories.category_name, units.unit_name, COALESCE(inventory.current_stock, 0) AS stock FROM supplies LEFT JOIN supply_categories ON supplies.category_id = supply_categories.category_id LEFT JOIN units ON supplies.unit_id = units.unit_id LEFT JOIN inventory ON supplies.supply_id = inventory.supply_id'
    conditions = []
    params = []
    if search:
        conditions.append('(supplies.supply_code LIKE %s OR supplies.supply_name LIKE %s OR supply_categories.category_name LIKE %s OR supplies.brand LIKE %s)')
        search_term = '%' + search + '%'
        params.extend([search_term, search_term, search_term, search_term])
    if unit_filter:
        conditions.append('supplies.unit_id = %s')
        params.append(unit_filter)
    if status_filter:
        conditions.append('supplies.status = %s')
        params.append(status_filter)
    if stock_filter == 'out':
        conditions.append('COALESCE(inventory.current_stock, 0) = 0')
    elif stock_filter == 'low':
        conditions.append('(COALESCE(inventory.current_stock, 0) > 0 AND COALESCE(inventory.current_stock, 0) <= supplies.reorder_level)')
    elif stock_filter == 'available':
        conditions.append('(COALESCE(inventory.current_stock, 0) > 0 AND COALESCE(inventory.current_stock, 0) > supplies.reorder_level)')
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    cursor.execute(query, tuple(params))
    all_supplies = cursor.fetchall()
    cursor.execute('SELECT * FROM units ORDER BY unit_name')
    unit_list = cursor.fetchall()
    conn.close()
    return render_template('supplies.html', supplies=all_supplies, units=unit_list, selected_unit=unit_filter, selected_status=status_filter, selected_stock=stock_filter)

@app.route('/supplies/add', methods=['GET', 'POST'])
def add_supply():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    error = None
    if request.method == 'POST':
        code = request.form['supply_code']
        name = request.form['supply_name']
        category_id = request.form['category_id']
        description = request.form['description']
        unit_id = request.form['unit_id']
        brand = request.form['brand']
        reorder_level = request.form['reorder_level']
        maximum_stock = request.form['maximum_stock']
        unit_cost = request.form['unit_cost']
        if int(reorder_level) < 0 or int(maximum_stock) < 0 or float(unit_cost) < 0: 
            error = 'Reorder Level, Maximum Stock, and Unit Cost cannot be negative.' 
        else: 
            cursor.execute('INSERT INTO supplies (supply_code, supply_name, category_id, description, unit_id, brand, reorder_level, maximum_stock, unit_cost) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', (code, name, category_id, description, unit_id, brand, reorder_level, maximum_stock, unit_cost)) 
            conn.commit() 
            conn.close() 
            return redirect('/supplies')
    cursor.execute('SELECT * FROM supply_categories')
    category_list = cursor.fetchall()
    cursor.execute('SELECT * FROM units')
    unit_list = cursor.fetchall()
    conn.close()
    return render_template('add_supply.html',categories=category_list, units=unit_list, error=error)


@app.route('/supplies/edit/<int:supply_id>', methods=['GET','POST'])
def edit_supply(supply_id): 
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    error = None
    if request.method == 'POST':
        code = request.form['supply_code']
        name = request.form['supply_name']
        category_id = request.form['category_id']
        description = request.form['description']
        unit_id = request.form['unit_id']
        brand = request.form['brand']
        reorder_level = request.form['reorder_level']
        maximum_stock = request.form['maximum_stock']
        unit_cost = request.form['unit_cost']
        if int(reorder_level) < 0 or int(maximum_stock) < 0 or float(unit_cost) < 0: 
            error = 'Reorder Level, Maximum Stock, and Unit Cost cannot be negative.' 
        else: 
            cursor.execute('UPDATE supplies SET supply_code=%s, supply_name=%s, category_id=%s, description=%s, unit_id=%s, brand=%s, reorder_level=%s, maximum_stock=%s, unit_cost=%s WHERE supply_id=%s', (code,name,category_id,description,unit_id,brand,reorder_level,maximum_stock,unit_cost,supply_id)) 
            conn.commit() 
            conn.close() 
            return redirect('/supplies')
    cursor.execute('SELECT * FROM supplies WHERE supply_id=%s', (supply_id,))
    supply = cursor.fetchone()
    cursor.execute('SELECT * FROM supply_categories')
    category_list = cursor.fetchall() 
    cursor.execute('SELECT * FROM units')
    unit_list = cursor.fetchall()
    conn.close()
    return render_template('edit_supply.html', supply=supply,categories=category_list, units=unit_list, error=error)

@app.route('/supplies/delete/<int:supply_id>')
def delete_supply(supply_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM supplies WHERE supply_id=%s',(supply_id,))
    conn.commit()
    conn.close()
    return redirect('/supplies')

@app.route('/supplies/profile/<int:supply_id>')
def supply_profile(supply_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT supplies.*, supply_categories.category_name, units.unit_name FROM supplies LEFT JOIN supply_categories ON supplies.category_id = supply_categories.category_id LEFT JOIN units ON supplies.unit_id = units.unit_id WHERE supplies.supply_id=%s', (supply_id,))
    supply = cursor.fetchone()
    cursor.execute('SELECT suppliers.supplier_id, suppliers.supplier_code, suppliers.supplier_name, suppliers.contact_person, suppliers.contact_number, suppliers.status FROM suppliers JOIN supplier_supplies ON suppliers.supplier_id = supplier_supplies.supplier_id WHERE supplier_supplies.supply_id=%s', (supply_id,))
    offered_by = cursor.fetchall()
    cursor.execute('SELECT * FROM inventory WHERE supply_id=%s', (supply_id,))
    current_inventory = cursor.fetchone()
    cursor.execute('SELECT * FROM inventory_transactions WHERE supply_id=%s AND transaction_type="Stock In" ORDER BY transaction_id DESC', (supply_id,))
    stock_in_history = cursor.fetchall()
    cursor.execute('SELECT inventory_transactions.*, issuances.issuance_number FROM inventory_transactions LEFT JOIN issuances ON inventory_transactions.reference_id = issuances.issuance_id WHERE inventory_transactions.supply_id=%s AND inventory_transactions.transaction_type="Issued" ORDER BY inventory_transactions.transaction_id DESC', (supply_id,))
    stock_out_history = cursor.fetchall()
    cursor.execute('SELECT supply_requests.request_number, supply_requests.request_date, supply_requests.status, employees.first_name, employees.last_name, request_items.requested_qty, request_items.approved_qty, request_items.issued_qty FROM request_items JOIN supply_requests ON request_items.request_id = supply_requests.request_id LEFT JOIN employees ON supply_requests.employee_id = employees.employee_id WHERE request_items.supply_id=%s ORDER BY supply_requests.request_id DESC', (supply_id,))
    request_history = cursor.fetchall()
    cursor.execute('SELECT issuances.issuance_id, issuances.issuance_number, issuances.issuance_date, issuances.issued_by, supply_requests.request_number, issuance_items.issued_qty FROM issuance_items JOIN issuances ON issuance_items.issuance_id = issuances.issuance_id JOIN supply_requests ON issuances.request_id = supply_requests.request_id WHERE issuance_items.supply_id=%s ORDER BY issuances.issuance_id DESC', (supply_id,))
    issuance_history = cursor.fetchall()
    conn.close()
    return render_template('supply_profile.html', supply=supply, offered_by=offered_by, current_inventory=current_inventory, stock_in_history=stock_in_history, stock_out_history=stock_out_history, request_history=request_history, issuance_history=issuance_history)

@app.route('/suppliers') 
def suppliers():    
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    search = request.args.get('search', '') 
    if search: 
        cursor.execute('SELECT * FROM suppliers WHERE supplier_name LIKE %s OR supplier_code LIKE %s OR contact_person LIKE %s', ('%' + search + '%', '%' + search + '%', '%' + search + '%')) 
    else: 
        cursor.execute('SELECT * FROM suppliers')
    all_suppliers = cursor.fetchall() 
    conn.close() 
    return render_template('suppliers.html', suppliers=all_suppliers) 

@app.route('/suppliers/add', methods=['GET', 'POST']) 
def add_supplier(): 
    if request.method == 'POST': 
        code = request.form['supplier_code'] 
        name = request.form['supplier_name'] 
        contact_person = request.form['contact_person'] 
        address = request.form['address'] 
        email = request.form['email'] 
        contact_number = request.form['contact_number'] 
        tax_info = request.form['tax_info'] 
        conn = get_connection() 
        cursor = conn.cursor() 
        cursor.execute('INSERT INTO suppliers (supplier_code, supplier_name, contact_person, address, email, contact_number, tax_info) VALUES (%s, %s, %s, %s, %s, %s, %s)', (code, name, contact_person, address, email, contact_number, tax_info)) 
        conn.commit() 
        conn.close() 
        return redirect('/suppliers') 
    return render_template('add_supplier.html')

@app.route('/suppliers/edit/<int:supplier_id>', methods=['GET', 'POST']) 
def edit_supplier(supplier_id): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    if request.method == 'POST': 
        code = request.form['supplier_code'] 
        name = request.form['supplier_name'] 
        contact_person = request.form['contact_person'] 
        address = request.form['address'] 
        email = request.form['email'] 
        contact_number = request.form['contact_number'] 
        tax_info = request.form['tax_info'] 
        cursor.execute('UPDATE suppliers SET supplier_code=%s, supplier_name=%s, contact_person=%s, address=%s, email=%s, contact_number=%s, tax_info=%s WHERE supplier_id=%s', (code, name, contact_person, address, email, contact_number, tax_info, supplier_id)) 
        conn.commit() 
        conn.close() 
        return redirect('/suppliers') 
    cursor.execute('SELECT * FROM suppliers WHERE supplier_id=%s', (supplier_id,)) 
    supplier = cursor.fetchone() 
    conn.close() 
    return render_template('edit_supplier.html', supplier=supplier) 

@app.route('/suppliers/toggle/<int:supplier_id>') 
def toggle_supplier(supplier_id): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    cursor.execute('SELECT status FROM suppliers WHERE supplier_id=%s', (supplier_id,)) 
    current = cursor.fetchone() 
    new_status = 'Inactive' if current['status'] == 'Active' else 'Active' 
    cursor.execute('UPDATE suppliers SET status=%s WHERE supplier_id=%s', (new_status, supplier_id)) 
    conn.commit() 
    conn.close() 
    return redirect('/suppliers') 

@app.route('/suppliers/profile/<int:supplier_id>')
def supplier_profile(supplier_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM suppliers WHERE supplier_id=%s', (supplier_id,))
    supplier = cursor.fetchone()
    cursor.execute('SELECT supplies.* FROM supplies JOIN supplier_supplies ON supplies.supply_id = supplier_supplies.supply_id WHERE supplier_supplies.supplier_id=%s', (supplier_id,))
    assigned_supplies = cursor.fetchall()
    cursor.execute('SELECT supply_receipts.receipt_number, supply_receipts.delivery_date, supplies.supply_name, receipt_items.quantity, receipt_items.unit_cost, receipt_items.total_cost FROM receipt_items JOIN supply_receipts ON receipt_items.receipt_id = supply_receipts.receipt_id JOIN supplies ON receipt_items.supply_id = supplies.supply_id WHERE supply_receipts.supplier_id=%s ORDER BY supply_receipts.delivery_date DESC, supply_receipts.receipt_id DESC', (supplier_id,))
    purchases = cursor.fetchall()
    grand_total = sum(row['total_cost'] for row in purchases)
    conn.close()
    return render_template('supplier_profile.html', supplier=supplier, assigned_supplies=assigned_supplies, purchases=purchases, grand_total=grand_total)

@app.route('/suppliers/assign/<int:supplier_id>', methods=['GET', 'POST'])
def assign_supplies(supplier_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        selected_ids = request.form.getlist('supply_ids')
        cursor.execute('DELETE FROM supplier_supplies WHERE supplier_id=%s', (supplier_id,))
        for supply_id in selected_ids:
            cursor.execute('INSERT INTO supplier_supplies (supplier_id, supply_id) VALUES (%s, %s)', (supplier_id, supply_id))
        conn.commit()
        conn.close()
        return redirect('/suppliers/profile/' + str(supplier_id))
    cursor.execute('SELECT * FROM suppliers WHERE supplier_id=%s', (supplier_id,))
    supplier = cursor.fetchone()
    cursor.execute('SELECT * FROM supplies')
    all_supplies = cursor.fetchall()
    cursor.execute('SELECT supply_id FROM supplier_supplies WHERE supplier_id=%s', (supplier_id,))
    assigned_rows = cursor.fetchall()
    assigned_ids = [row['supply_id'] for row in assigned_rows]
    conn.close()
    return render_template('assign_supplies.html', supplier=supplier, supplies=all_supplies, assigned_ids=assigned_ids)

@app.route('/receipts') 
def receipts(): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    cursor.execute('SELECT supply_receipts.*, suppliers.supplier_name FROM supply_receipts LEFT JOIN suppliers ON supply_receipts.supplier_id = suppliers.supplier_id ORDER BY supply_receipts.receipt_id DESC') 
    all_receipts = cursor.fetchall() 
    conn.close() 
    return render_template('receipts.html', receipts=all_receipts)

@app.route('/receipts/items/<int:receipt_id>', methods=['GET', 'POST'])
def receipt_items(receipt_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        supply_id = request.form['supply_id']
        quantity = int(request.form['quantity'])
        unit_cost = float(request.form['unit_cost'])
        total_cost = quantity * unit_cost
        batch_reference = request.form['batch_reference']
        cursor.execute('INSERT INTO receipt_items (receipt_id, supply_id, quantity, unit_cost, total_cost, batch_reference) VALUES (%s, %s, %s, %s, %s, %s)', (receipt_id, supply_id, quantity, unit_cost, total_cost, batch_reference))
        cursor.execute('SELECT * FROM inventory WHERE supply_id=%s', (supply_id,))
        existing_inventory = cursor.fetchone()
        if existing_inventory:
            new_stock = existing_inventory['current_stock'] + quantity
            cursor.execute('UPDATE inventory SET current_stock=%s WHERE supply_id=%s', (new_stock, supply_id))
        else:
            new_stock = quantity
            cursor.execute('INSERT INTO inventory (supply_id, current_stock) VALUES (%s, %s)', (supply_id, new_stock))
        cursor.execute('INSERT INTO inventory_transactions (supply_id, transaction_type, quantity, balance_after, reference_type, reference_id) VALUES (%s, %s, %s, %s, %s, %s)', (supply_id, 'Stock In', quantity, new_stock, 'Receipt', receipt_id))
        conn.commit()
    cursor.execute('SELECT * FROM supply_receipts WHERE receipt_id=%s', (receipt_id,))
    receipt = cursor.fetchone()
    cursor.execute('SELECT supplies.* FROM supplies JOIN supplier_supplies ON supplies.supply_id = supplier_supplies.supply_id WHERE supplier_supplies.supplier_id=%s AND supplies.status="Active"', (receipt['supplier_id'],))
    supply_list = cursor.fetchall()
    cursor.execute('SELECT receipt_items.*, supplies.supply_name FROM receipt_items JOIN supplies ON receipt_items.supply_id = supplies.supply_id WHERE receipt_items.receipt_id=%s', (receipt_id,))
    items = cursor.fetchall()
    conn.close()
    return render_template('receipt_items.html', receipt=receipt, supplies=supply_list, items=items)

@app.route('/inventory/transactions') 
def inventory_transactions(): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    cursor.execute('SELECT inventory_transactions.*, supplies.supply_name FROM inventory_transactions JOIN supplies ON inventory_transactions.supply_id = supplies.supply_id ORDER BY inventory_transactions.created_at DESC') 
    all_transactions = cursor.fetchall() 
    conn.close() 
    return render_template('inventory_transactions.html', transactions=all_transactions)

@app.route('/departments') 
def departments(): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    cursor.execute('SELECT * FROM departments') 
    all_departments = cursor.fetchall() 
    conn.close() 
    return render_template('departments.html', departments=all_departments) 

@app.route('/departments/add', methods=['GET', 'POST']) 
def add_department(): 
    if request.method == 'POST': 
        name = request.form['department_name'] 
        conn = get_connection() 
        cursor = conn.cursor() 
        cursor.execute('INSERT INTO departments (department_name) VALUES (%s)', (name,)) 
        conn.commit() 
        conn.close() 
        return redirect('/departments') 
    return render_template('add_department.html')

@app.route('/employees') 
def employees(): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    cursor.execute('SELECT employees.*, departments.department_name FROM employees LEFT JOIN departments ON employees.department_id = departments.department_id') 
    all_employees = cursor.fetchall() 
    conn.close() 
    return render_template('employees.html', employees=all_employees) 

@app.route('/employees/add', methods=['GET', 'POST']) 
def add_employee(): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    if request.method == 'POST': 
        first_name = request.form['first_name'] 
        last_name = request.form['last_name'] 
        position = request.form['position'] 
        department_id = request.form['department_id'] 
        email = request.form['email'] 
        contact_number = request.form['contact_number'] 
        cursor.execute('INSERT INTO employees (first_name, last_name, position, department_id, email, contact_number) VALUES (%s, %s, %s, %s, %s, %s)', (first_name, last_name, position, department_id, email, contact_number)) 
        conn.commit() 
        conn.close() 
        return redirect('/employees') 
    cursor.execute('SELECT * FROM departments WHERE status="Active"') 
    department_list = cursor.fetchall() 
    conn.close()
    return render_template('add_employee.html', departments=department_list)

@app.route('/requests') 
def requests_list(): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    cursor.execute('SELECT supply_requests.*, employees.first_name, employees.last_name, departments.department_name, (SELECT COUNT(*) FROM request_items WHERE request_items.request_id = supply_requests.request_id) AS item_count FROM supply_requests LEFT JOIN employees ON supply_requests.employee_id = employees.employee_id LEFT JOIN departments ON supply_requests.department_id = departments.department_id ORDER BY supply_requests.request_id DESC') 
    all_requests = cursor.fetchall() 
    conn.close() 
    return render_template('requests.html', requests=all_requests)


@app.route('/requests/add', methods=['GET', 'POST']) 
def add_request(): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    if request.method == 'POST': 
        request_number = request.form['request_number'] 
        employee_id = request.form['employee_id'] 
        request_date = request.form['request_date'] 
        purpose = request.form['purpose'] 
        priority = request.form['priority'] 
        required_date = request.form['required_date'] 
        remarks = request.form['remarks'] 
        cursor.execute('SELECT department_id FROM employees WHERE employee_id=%s', (employee_id,)) 
        employee_row = cursor.fetchone() 
        department_id = employee_row['department_id'] 
        cursor.execute('INSERT INTO supply_requests (request_number, employee_id, department_id, request_date, purpose, priority, required_date, remarks) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)', (request_number, employee_id, department_id, request_date, purpose, priority, required_date, remarks)) 
        conn.commit() 
        new_request_id = cursor.lastrowid 
        conn.close() 
        return redirect('/requests/items/' + str(new_request_id)) 
    cursor.execute('SELECT * FROM employees WHERE status="Active"') 
    employee_list = cursor.fetchall() 
    conn.close() 
    return render_template('add_request.html', employees=employee_list)

@app.route('/receipts/add', methods=['GET', 'POST']) 
def add_receipt(): 
    conn = get_connection() 
    cursor = conn.cursor(dictionary=True) 
    if request.method == 'POST': 
        receipt_number = request.form['receipt_number'] 
        supplier_id = request.form['supplier_id'] 
        delivery_date = request.form['delivery_date'] 
        po_reference = request.form['po_reference'] 
        received_by = request.form['received_by'] 
        remarks = request.form['remarks'] 
        cursor.execute('INSERT INTO supply_receipts (receipt_number, supplier_id, delivery_date, po_reference, received_by, remarks) VALUES (%s, %s, %s, %s, %s, %s)', (receipt_number, supplier_id, delivery_date, po_reference, received_by, remarks))
        new_receipt_id = cursor.lastrowid
        conn.commit() 
        conn.close() 
        return redirect('/receipts/items/' + str(new_receipt_id)) 
    cursor.execute('SELECT * FROM suppliers WHERE status="Active"') 
    supplier_list = cursor.fetchall() 
    conn.close() 
    return render_template('add_receipt.html', suppliers=supplier_list)

@app.route('/requests/items/<int:request_id>', methods=['GET', 'POST'])
def request_items(request_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    error = None
    if request.args.get('msg') == 'no_items':
        error = 'A request cannot be submitted without items. Please add at least one item first.'
    cursor.execute('SELECT * FROM supply_requests WHERE request_id=%s', (request_id,))
    req = cursor.fetchone()
    editable = req['status'] in ('Draft', 'Returned')
    if request.method == 'POST' and not editable:
        error = 'This request has already been submitted and can no longer be modified.'
    elif request.method == 'POST':
        supply_id = request.form['supply_id']
        requested_qty = int(request.form['requested_qty'])
        cursor.execute('SELECT * FROM request_items WHERE request_id=%s AND supply_id=%s', (request_id, supply_id))
        duplicate_check = cursor.fetchone()
        cursor.execute('SELECT current_stock FROM inventory WHERE supply_id=%s', (supply_id,))
        stock_row = cursor.fetchone()
        available = stock_row['current_stock'] if stock_row else 0
        if duplicate_check:
            error = 'This supply has already been added to this request.'
        elif requested_qty > available:
            error = 'Requested quantity (' + str(requested_qty) + ') exceeds available stock (' + str(available) + ').'
        else:
            cursor.execute('INSERT INTO request_items (request_id, supply_id, requested_qty) VALUES (%s, %s, %s)', (request_id, supply_id, requested_qty))
            conn.commit()
    cursor.execute('SELECT supplies.*, inventory.current_stock FROM supplies LEFT JOIN inventory ON supplies.supply_id = inventory.supply_id WHERE supplies.status="Active"')
    supply_list = cursor.fetchall()
    cursor.execute('SELECT request_items.*, supplies.supply_name, inventory.current_stock FROM request_items JOIN supplies ON request_items.supply_id = supplies.supply_id LEFT JOIN inventory ON supplies.supply_id = inventory.supply_id WHERE request_items.request_id=%s', (request_id,))
    items = cursor.fetchall()
    conn.close()
    return render_template('request_items.html', req=req, supplies=supply_list, items=items, error=error, editable=editable)

@app.route('/requests/submit/<int:request_id>')
def submit_request(request_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT status FROM supply_requests WHERE request_id=%s', (request_id,))
    req = cursor.fetchone()
    cursor.execute('SELECT COUNT(*) AS item_count FROM request_items WHERE request_id=%s', (request_id,))
    count_row = cursor.fetchone()
    if req['status'] not in ('Draft', 'Returned'):
        conn.close()
        return redirect('/requests/items/' + str(request_id))
    if count_row['item_count'] == 0:
        conn.close()
        return redirect('/requests/items/' + str(request_id) + '?msg=no_items')
    cursor.execute('UPDATE supply_requests SET status="Submitted" WHERE request_id=%s', (request_id,))
    conn.commit()
    conn.close()
    return redirect('/requests')

@app.route('/approval-levels', methods=['GET', 'POST'])
def approval_levels():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    error = None
    if request.method == 'POST':
        level_number = int(request.form['level_number'])
        level_name = request.form['level_name']
        cursor.execute('SELECT * FROM approval_levels WHERE level_number=%s', (level_number,))
        if cursor.fetchone():
            error = 'Level ' + str(level_number) + ' already exists.'
        else:
            cursor.execute('INSERT INTO approval_levels (level_number, level_name) VALUES (%s, %s)', (level_number, level_name))
            conn.commit()
    cursor.execute('SELECT * FROM approval_levels ORDER BY level_number')
    levels = cursor.fetchall()
    conn.close()
    return render_template('approval_levels.html', levels=levels, error=error)


@app.route('/approval-levels/edit/<int:level_id>', methods=['GET', 'POST'])
def edit_approval_level(level_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    error = None
    if request.method == 'POST':
        level_number = int(request.form['level_number'])
        level_name = request.form['level_name']
        cursor.execute('SELECT * FROM approval_levels WHERE level_number=%s AND level_id<>%s', (level_number, level_id))
        if cursor.fetchone():
            error = 'Level ' + str(level_number) + ' already exists.'
        else:
            cursor.execute('UPDATE approval_levels SET level_number=%s, level_name=%s WHERE level_id=%s', (level_number, level_name, level_id))
            conn.commit()
            conn.close()
            return redirect('/approval-levels')
    cursor.execute('SELECT * FROM approval_levels WHERE level_id=%s', (level_id,))
    level = cursor.fetchone()
    conn.close()
    return render_template('edit_approval_level.html', level=level, error=error)


@app.route('/approval-levels/toggle/<int:level_id>')
def toggle_approval_level(level_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT status FROM approval_levels WHERE level_id=%s', (level_id,))
    current = cursor.fetchone()
    new_status = 'Inactive' if current['status'] == 'Active' else 'Active'
    cursor.execute('UPDATE approval_levels SET status=%s WHERE level_id=%s', (new_status, level_id))
    conn.commit()
    conn.close()
    return redirect('/approval-levels')

@app.route('/requests/review/<int:request_id>', methods=['GET', 'POST'])
def review_request(request_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    error = None
    if request.args.get('msg') == 'remarks_required':
        error = 'Remarks are required when rejecting or returning a request.'
    cursor.execute('SELECT supply_requests.*, employees.first_name, employees.last_name, departments.department_name FROM supply_requests LEFT JOIN employees ON supply_requests.employee_id = employees.employee_id LEFT JOIN departments ON supply_requests.department_id = departments.department_id WHERE supply_requests.request_id=%s', (request_id,))
    req = cursor.fetchone()
    cursor.execute('SELECT request_items.*, supplies.supply_name, inventory.current_stock FROM request_items JOIN supplies ON request_items.supply_id = supplies.supply_id LEFT JOIN inventory ON supplies.supply_id = inventory.supply_id WHERE request_items.request_id=%s', (request_id,))
    items = cursor.fetchall()
    if request.method == 'POST':
        action = request.form['action']
        if action == 'start' and req['status'] == 'Submitted':
            cursor.execute('UPDATE supply_requests SET status="Under Review" WHERE request_id=%s', (request_id,))
            conn.commit()
            conn.close()
            return redirect('/requests/review/' + str(request_id))
        elif action == 'save' and req['status'] == 'Under Review':
            for item in items:
                value = int(request.form['approved_' + str(item['request_item_id'])])
                item['approved_qty'] = value
                available = item['current_stock'] or 0
                if value < 0 or value > item['requested_qty']:
                    error = 'Approved quantity for ' + item['supply_name'] + ' must be between 0 and the requested quantity (' + str(item['requested_qty']) + ').'
                elif value > available:
                    error = 'Approved quantity for ' + item['supply_name'] + ' (' + str(value) + ') exceeds available stock (' + str(available) + ').'
            if error is None:
                for item in items:
                    cursor.execute('UPDATE request_items SET approved_qty=%s WHERE request_item_id=%s', (item['approved_qty'], item['request_item_id']))
                cursor.execute('UPDATE supply_requests SET review_remarks=%s, status="For Approval" WHERE request_id=%s', (request.form['review_remarks'], request_id))
                conn.commit()
                conn.close()
                return redirect('/requests/review/' + str(request_id))
    next_level = None
    if req['status'] == 'For Approval':
        next_level = get_next_level(cursor, request_id)
    cursor.execute('SELECT approvals.*, approval_levels.level_name FROM approvals LEFT JOIN approval_levels ON approvals.approval_level = approval_levels.level_number WHERE approvals.request_id=%s ORDER BY approvals.approval_id', (request_id,))
    history = cursor.fetchall()
    conn.close()
    return render_template('review_request.html', req=req, items=items, error=error, next_level=next_level, history=history)

def get_next_level(cursor, request_id):
    cursor.execute('SELECT MAX(approval_id) AS last_id FROM approvals WHERE request_id=%s AND decision="Returned"', (request_id,))
    last_returned_id = cursor.fetchone()['last_id'] or 0
    cursor.execute('SELECT approval_level FROM approvals WHERE request_id=%s AND decision="Approved" AND approval_id>%s', (request_id, last_returned_id))
    approved_levels = [row['approval_level'] for row in cursor.fetchall()]
    cursor.execute('SELECT * FROM approval_levels WHERE status="Active" ORDER BY level_number')
    for level in cursor.fetchall():
        if level['level_number'] not in approved_levels:
            return level
    return None


@app.route('/requests/decide/<int:request_id>', methods=['POST'])
def decide_request(request_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT status FROM supply_requests WHERE request_id=%s', (request_id,))
    req = cursor.fetchone()
    approver_name = request.form['approver_name']
    decision = request.form['decision']
    remarks = request.form['remarks'].strip()
    level = get_next_level(cursor, request_id)
    if req['status'] != 'For Approval' or level is None or decision not in ('Approved', 'Rejected', 'Returned'):
        conn.close()
        return redirect('/requests/review/' + str(request_id))
    if decision in ('Rejected', 'Returned') and remarks == '':
        conn.close()
        return redirect('/requests/review/' + str(request_id) + '?msg=remarks_required')
    cursor.execute('INSERT INTO approvals (request_id, approver_name, approval_level, decision, remarks) VALUES (%s, %s, %s, %s, %s)', (request_id, approver_name, level['level_number'], decision, remarks))
    if decision == 'Approved':
        if get_next_level(cursor, request_id) is None:
            cursor.execute('UPDATE supply_requests SET status="Approved" WHERE request_id=%s', (request_id,))
    else:
        cursor.execute('UPDATE supply_requests SET status=%s WHERE request_id=%s', (decision, request_id))
    conn.commit()
    conn.close()
    return redirect('/requests/review/' + str(request_id))

@app.route('/inventory')
def inventory_list():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT supplies.supply_id, supplies.supply_code, supplies.supply_name, supplies.reorder_level, units.unit_name, COALESCE(inventory.current_stock, 0) AS stock, CASE WHEN COALESCE(inventory.current_stock, 0) = 0 THEN "Out of Stock" WHEN COALESCE(inventory.current_stock, 0) <= supplies.reorder_level THEN "Low Stock" ELSE "Available" END AS stock_status FROM supplies LEFT JOIN units ON supplies.unit_id = units.unit_id LEFT JOIN inventory ON supplies.supply_id = inventory.supply_id ORDER BY supplies.supply_name')
    rows = cursor.fetchall()
    conn.close()
    return render_template('inventory.html', rows=rows)

@app.route('/inventory/adjustments', methods=['GET', 'POST'])
def stock_adjustments():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    error = None
    if request.method == 'POST':
        supply_id = request.form['supply_id']
        direction = request.form['direction']
        quantity = int(request.form['quantity'])
        reason = request.form['reason']
        adjusted_by = request.form['adjusted_by']
        remarks = request.form['remarks'].strip()
        cursor.execute('SELECT current_stock FROM inventory WHERE supply_id=%s', (supply_id,))
        stock_row = cursor.fetchone()
        current_stock = stock_row['current_stock'] if stock_row else 0
        change = quantity if direction == 'Increase' else -quantity
        new_stock = current_stock + change
        if quantity < 1:
            error = 'Quantity must be at least 1.'
        elif remarks == '':
            error = 'Remarks are required for every adjustment.'
        elif new_stock < 0:
            error = 'This adjustment would make stock negative. Current stock is ' + str(current_stock) + '.'
        else:
            if stock_row:
                cursor.execute('UPDATE inventory SET current_stock=%s WHERE supply_id=%s', (new_stock, supply_id))
            else:
                cursor.execute('INSERT INTO inventory (supply_id, current_stock) VALUES (%s, %s)', (supply_id, new_stock))
            cursor.execute('INSERT INTO stock_adjustments (supply_id, quantity, reason, adjusted_by, remarks) VALUES (%s, %s, %s, %s, %s)', (supply_id, change, reason, adjusted_by, remarks))
            adjustment_id = cursor.lastrowid
            cursor.execute('INSERT INTO inventory_transactions (supply_id, transaction_type, quantity, balance_after, reference_type, reference_id) VALUES (%s, %s, %s, %s, %s, %s)', (supply_id, 'Adjustment', change, new_stock, 'Adjustment', adjustment_id))
            conn.commit()
            conn.close()
            return redirect('/inventory/adjustments')
    cursor.execute('SELECT supplies.supply_id, supplies.supply_code, supplies.supply_name, COALESCE(inventory.current_stock, 0) AS stock FROM supplies LEFT JOIN inventory ON supplies.supply_id = inventory.supply_id WHERE supplies.status="Active" ORDER BY supplies.supply_name')
    supply_list = cursor.fetchall()
    cursor.execute('SELECT stock_adjustments.*, supplies.supply_name FROM stock_adjustments JOIN supplies ON stock_adjustments.supply_id = supplies.supply_id ORDER BY stock_adjustments.adjustment_id DESC')
    adjustments = cursor.fetchall()
    conn.close()
    return render_template('stock_adjustments.html', supplies=supply_list, adjustments=adjustments, error=error)

@app.route('/inventory/physical-count', methods=['GET', 'POST'])
def physical_count():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    error = None
    if request.method == 'POST':
        supply_id = request.form['supply_id']
        actual_qty = int(request.form['actual_qty'])
        counted_by = request.form['counted_by']
        reason = request.form['reason'].strip()
        cursor.execute('SELECT current_stock FROM inventory WHERE supply_id=%s', (supply_id,))
        stock_row = cursor.fetchone()
        system_qty = stock_row['current_stock'] if stock_row else 0
        variance = actual_qty - system_qty
        if actual_qty < 0:
            error = 'Actual quantity cannot be negative.'
        elif variance != 0 and reason == '':
            error = 'A reason is required when the actual count differs from the system quantity.'
        else:
            cursor.execute('INSERT INTO physical_counts (supply_id, system_qty, actual_qty, variance, reason, counted_by) VALUES (%s, %s, %s, %s, %s, %s)', (supply_id, system_qty, actual_qty, variance, reason, counted_by))
            count_id = cursor.lastrowid
            if variance != 0:
                if stock_row:
                    cursor.execute('UPDATE inventory SET current_stock=%s WHERE supply_id=%s', (actual_qty, supply_id))
                else:
                    cursor.execute('INSERT INTO inventory (supply_id, current_stock) VALUES (%s, %s)', (supply_id, actual_qty))
                cursor.execute('INSERT INTO stock_adjustments (supply_id, quantity, reason, adjusted_by, remarks) VALUES (%s, %s, %s, %s, %s)', (supply_id, variance, 'Physical count difference', counted_by, reason))
                cursor.execute('INSERT INTO inventory_transactions (supply_id, transaction_type, quantity, balance_after, reference_type, reference_id) VALUES (%s, %s, %s, %s, %s, %s)', (supply_id, 'Adjustment', variance, actual_qty, 'Physical Count', count_id))
            conn.commit()
            conn.close()
            return redirect('/inventory/physical-count')
    cursor.execute('SELECT supplies.supply_id, supplies.supply_code, supplies.supply_name, COALESCE(inventory.current_stock, 0) AS stock FROM supplies LEFT JOIN inventory ON supplies.supply_id = inventory.supply_id WHERE supplies.status="Active" ORDER BY supplies.supply_name')
    supply_list = cursor.fetchall()
    cursor.execute('SELECT physical_counts.*, supplies.supply_name FROM physical_counts JOIN supplies ON physical_counts.supply_id = supplies.supply_id ORDER BY physical_counts.count_id DESC')
    counts = cursor.fetchall()
    conn.close()
    return render_template('physical_count.html', supplies=supply_list, counts=counts, error=error)

@app.route('/inventory/history/<int:supply_id>')
def inventory_history(supply_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT supplies.*, units.unit_name FROM supplies LEFT JOIN units ON supplies.unit_id = units.unit_id WHERE supplies.supply_id=%s', (supply_id,))
    supply = cursor.fetchone()
    cursor.execute('SELECT current_stock FROM inventory WHERE supply_id=%s', (supply_id,))
    stock_row = cursor.fetchone()
    balance = stock_row['current_stock'] if stock_row else 0
    cursor.execute('SELECT COALESCE(SUM(CASE WHEN transaction_type="Stock In" THEN quantity ELSE 0 END), 0) AS total_in, COALESCE(SUM(CASE WHEN transaction_type="Issued" THEN ABS(quantity) ELSE 0 END), 0) AS total_out, COALESCE(SUM(CASE WHEN transaction_type="Adjustment" THEN quantity ELSE 0 END), 0) AS total_adjusted FROM inventory_transactions WHERE supply_id=%s', (supply_id,))
    totals = cursor.fetchone()
    cursor.execute('SELECT * FROM inventory_transactions WHERE supply_id=%s ORDER BY transaction_id DESC', (supply_id,))
    transactions = cursor.fetchall()
    conn.close()
    return render_template('inventory_history.html', supply=supply, balance=balance, totals=totals, transactions=transactions)

@app.route('/issuance')
def issuance_queue():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT supply_requests.request_id, supply_requests.request_number, supply_requests.status, employees.first_name, employees.last_name, departments.department_name, (SELECT MAX(decided_at) FROM approvals WHERE approvals.request_id = supply_requests.request_id AND approvals.decision="Approved") AS date_approved, (SELECT COALESCE(SUM(issued_qty), 0) FROM request_items WHERE request_items.request_id = supply_requests.request_id) AS total_issued FROM supply_requests LEFT JOIN employees ON supply_requests.employee_id = employees.employee_id LEFT JOIN departments ON supply_requests.department_id = departments.department_id WHERE supply_requests.status="Approved" ORDER BY date_approved')
    queue = cursor.fetchall()
    for row in queue:
        cursor.execute('SELECT supplies.supply_name, request_items.approved_qty, request_items.issued_qty, request_items.approved_qty - request_items.issued_qty AS remaining, units.unit_name FROM request_items JOIN supplies ON request_items.supply_id = supplies.supply_id LEFT JOIN units ON supplies.unit_id = units.unit_id WHERE request_items.request_id=%s AND request_items.approved_qty > request_items.issued_qty', (row['request_id'],))
        row['item_list'] = cursor.fetchall()
    conn.close()
    return render_template('issuance_queue.html', queue=queue)

@app.route('/issuance/issue/<int:request_id>', methods=['GET', 'POST'])
def issue_request(request_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    error = None
    cursor.execute('SELECT supply_requests.*, employees.first_name, employees.last_name, departments.department_name FROM supply_requests LEFT JOIN employees ON supply_requests.employee_id = employees.employee_id LEFT JOIN departments ON supply_requests.department_id = departments.department_id WHERE supply_requests.request_id=%s', (request_id,))
    req = cursor.fetchone()
    if req['status'] != 'Approved':
        conn.close()
        return redirect('/issuance')
    cursor.execute('SELECT request_items.*, supplies.supply_name, supplies.unit_id, units.unit_name, COALESCE(inventory.current_stock, 0) AS stock FROM request_items JOIN supplies ON request_items.supply_id = supplies.supply_id LEFT JOIN units ON supplies.unit_id = units.unit_id LEFT JOIN inventory ON supplies.supply_id = inventory.supply_id WHERE request_items.request_id=%s AND request_items.approved_qty > request_items.issued_qty', (request_id,))
    items = cursor.fetchall()
    for item in items:
        item['remaining'] = item['approved_qty'] - item['issued_qty']
        item['max_issue'] = min(item['remaining'], item['stock'])
    if request.method == 'POST':
        issued_by = request.form['issued_by']
        issuance_date = request.form['issuance_date']
        remarks = request.form['remarks']
        total = 0
        for item in items:
            qty = int(request.form['issue_' + str(item['request_item_id'])])
            item['issue_qty'] = qty
            if qty < 0 or qty > item['remaining']:
                error = 'Quantity for ' + item['supply_name'] + ' must be between 0 and the remaining approved quantity (' + str(item['remaining']) + ').'
            elif qty > item['stock']:
                error = 'Cannot issue ' + str(qty) + ' of ' + item['supply_name'] + '. Only ' + str(item['stock']) + ' in stock.'
            total += qty
        if error is None and total == 0:
            error = 'Enter a quantity to issue for at least one item.'
        if error is None:
            cursor.execute('SELECT COALESCE(MAX(issuance_id), 0) + 1 AS next_id, YEAR(CURDATE()) AS year FROM issuances')
            number_row = cursor.fetchone()
            issuance_number = 'ISS-' + str(number_row['year']) + '-' + str(number_row['next_id']).zfill(5)
            cursor.execute('INSERT INTO issuances (issuance_number, request_id, issued_by, issuance_date, remarks) VALUES (%s, %s, %s, %s, %s)', (issuance_number, request_id, issued_by, issuance_date, remarks))
            issuance_id = cursor.lastrowid
            for item in items:
                qty = item['issue_qty']
                if qty > 0:
                    new_stock = item['stock'] - qty
                    cursor.execute('INSERT INTO issuance_items (issuance_id, supply_id, approved_qty, issued_qty, unit_id) VALUES (%s, %s, %s, %s, %s)', (issuance_id, item['supply_id'], item['approved_qty'], qty, item['unit_id']))
                    cursor.execute('UPDATE inventory SET current_stock=%s WHERE supply_id=%s', (new_stock, item['supply_id']))
                    cursor.execute('INSERT INTO inventory_transactions (supply_id, transaction_type, quantity, balance_after, reference_type, reference_id) VALUES (%s, %s, %s, %s, %s, %s)', (item['supply_id'], 'Issued', qty, new_stock, 'Issuance', issuance_id))
                    cursor.execute('UPDATE request_items SET issued_qty = issued_qty + %s WHERE request_item_id=%s', (qty, item['request_item_id']))
            cursor.execute('SELECT COUNT(*) AS pending FROM request_items WHERE request_id=%s AND approved_qty > issued_qty', (request_id,))
            if cursor.fetchone()['pending'] == 0:
                cursor.execute('UPDATE supply_requests SET status="Issued" WHERE request_id=%s', (request_id,))
            conn.commit()
            conn.close()
            return redirect('/issuance/document/' + str(issuance_id))
    cursor.execute('SELECT CURDATE() AS today')
    today = cursor.fetchone()['today']
    conn.close()
    return render_template('issue_request.html', req=req, items=items, error=error, today=today)

@app.route('/issuances')
def issuance_records():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT issuances.*, supply_requests.request_number, employees.first_name, employees.last_name, departments.department_name FROM issuances JOIN supply_requests ON issuances.request_id = supply_requests.request_id LEFT JOIN employees ON supply_requests.employee_id = employees.employee_id LEFT JOIN departments ON supply_requests.department_id = departments.department_id ORDER BY issuances.issuance_id DESC')
    records = cursor.fetchall()
    conn.close()
    return render_template('issuance_records.html', records=records)


@app.route('/issuance/document/<int:issuance_id>')
def issuance_document(issuance_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT issuances.*, supply_requests.request_number, employees.first_name, employees.last_name, departments.department_name FROM issuances JOIN supply_requests ON issuances.request_id = supply_requests.request_id LEFT JOIN employees ON supply_requests.employee_id = employees.employee_id LEFT JOIN departments ON supply_requests.department_id = departments.department_id WHERE issuances.issuance_id=%s', (issuance_id,))
    issuance = cursor.fetchone()
    cursor.execute('SELECT issuance_items.*, supplies.supply_code, supplies.supply_name, units.unit_name FROM issuance_items JOIN supplies ON issuance_items.supply_id = supplies.supply_id LEFT JOIN units ON issuance_items.unit_id = units.unit_id WHERE issuance_items.issuance_id=%s', (issuance_id,))
    items = cursor.fetchall()
    conn.close()
    return render_template('issuance_document.html', issuance=issuance, items=items)

@app.route('/reports')
def reports_home():
    return render_template('reports.html')


@app.route('/reports/inventory')
def inventory_report():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT supplies.supply_code, supplies.supply_name, supplies.reorder_level, supplies.unit_cost, supplies.status, supply_categories.category_name, units.unit_name, COALESCE(inventory.current_stock, 0) AS stock, COALESCE(inventory.current_stock, 0) * supplies.unit_cost AS stock_value FROM supplies LEFT JOIN supply_categories ON supplies.category_id = supply_categories.category_id LEFT JOIN units ON supplies.unit_id = units.unit_id LEFT JOIN inventory ON supplies.supply_id = inventory.supply_id ORDER BY supply_categories.category_name, supplies.supply_name')
    all_supplies = cursor.fetchall()
    conn.close()
    low_stock = [row for row in all_supplies if row['status'] == 'Active' and row['stock'] > 0 and row['stock'] <= row['reorder_level']]
    out_of_stock = [row for row in all_supplies if row['status'] == 'Active' and row['stock'] == 0]
    categories = {}
    for row in all_supplies:
        name = row['category_name'] or 'Uncategorized'
        if name not in categories:
            categories[name] = {'category_name': name, 'supply_count': 0, 'total_stock': 0, 'total_value': 0}
        categories[name]['supply_count'] += 1
        categories[name]['total_stock'] += row['stock']
        categories[name]['total_value'] += row['stock_value']
    category_summary = sorted(categories.values(), key=lambda c: c['category_name'])
    total_units = sum(row['stock'] for row in all_supplies)
    total_value = sum(row['stock_value'] for row in all_supplies)
    return render_template('inventory_report.html', all_supplies=all_supplies, low_stock=low_stock, out_of_stock=out_of_stock, category_summary=category_summary, total_units=total_units, total_value=total_value)

@app.route('/reports/suppliers')
def supplier_report():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT suppliers.supplier_code, suppliers.supplier_name, suppliers.contact_person, suppliers.status, (SELECT GROUP_CONCAT(supplies.supply_name ORDER BY supplies.supply_name SEPARATOR ", ") FROM supplies JOIN supplier_supplies ON supplies.supply_id = supplier_supplies.supply_id WHERE supplier_supplies.supplier_id = suppliers.supplier_id) AS supply_names, (SELECT COUNT(*) FROM supply_receipts WHERE supply_receipts.supplier_id = suppliers.supplier_id) AS delivery_count, (SELECT COALESCE(SUM(receipt_items.quantity), 0) FROM receipt_items JOIN supply_receipts ON receipt_items.receipt_id = supply_receipts.receipt_id WHERE supply_receipts.supplier_id = suppliers.supplier_id) AS total_quantity, (SELECT COALESCE(SUM(receipt_items.total_cost), 0) FROM receipt_items JOIN supply_receipts ON receipt_items.receipt_id = supply_receipts.receipt_id WHERE supply_receipts.supplier_id = suppliers.supplier_id) AS total_cost FROM suppliers ORDER BY suppliers.supplier_name')
    supplier_list = cursor.fetchall()
    cursor.execute('SELECT supply_receipts.receipt_number, supply_receipts.delivery_date, suppliers.supplier_name, supplies.supply_name, receipt_items.quantity, receipt_items.unit_cost, receipt_items.total_cost FROM receipt_items JOIN supply_receipts ON receipt_items.receipt_id = supply_receipts.receipt_id JOIN suppliers ON supply_receipts.supplier_id = suppliers.supplier_id JOIN supplies ON receipt_items.supply_id = supplies.supply_id ORDER BY supply_receipts.delivery_date DESC, supply_receipts.receipt_id DESC')
    transactions = cursor.fetchall()
    conn.close()
    grand_quantity = sum(row['quantity'] for row in transactions)
    grand_cost = sum(row['total_cost'] for row in transactions)
    return render_template('supplier_report.html', supplier_list=supplier_list, transactions=transactions, grand_quantity=grand_quantity, grand_cost=grand_cost)

def status_group(status):
    # Groups the detailed statuses into the four report categories
    if status in ('Submitted', 'Under Review', 'For Approval'):
        return 'pending'
    if status in ('Approved', 'Issued'):
        return 'approved'
    if status == 'Rejected':
        return 'rejected'
    return 'other'


def add_to_summary(summary, name, group):
    # Adds one request to the count for a department or employee
    if name not in summary:
        summary[name] = {'name': name, 'total': 0, 'pending': 0, 'approved': 0, 'rejected': 0, 'other': 0}
    summary[name]['total'] += 1
    summary[name][group] += 1


@app.route('/reports/requests')
def request_report():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    department_filter = request.args.get('department_id', '')
    employee_filter = request.args.get('employee_id', '')
    status_filter = request.args.get('status_group', '')
    query = 'SELECT supply_requests.request_number, supply_requests.request_date, supply_requests.priority, supply_requests.status, employees.first_name, employees.last_name, departments.department_name, (SELECT COUNT(*) FROM request_items WHERE request_items.request_id = supply_requests.request_id) AS item_count FROM supply_requests LEFT JOIN employees ON supply_requests.employee_id = employees.employee_id LEFT JOIN departments ON supply_requests.department_id = departments.department_id'
    conditions = []
    params = []
    if date_from:
        conditions.append('supply_requests.request_date >= %s')
        params.append(date_from)
    if date_to:
        conditions.append('supply_requests.request_date <= %s')
        params.append(date_to)
    if department_filter:
        conditions.append('supply_requests.department_id = %s')
        params.append(department_filter)
    if employee_filter:
        conditions.append('supply_requests.employee_id = %s')
        params.append(employee_filter)
    if status_filter == 'pending':
        conditions.append('supply_requests.status IN ("Submitted", "Under Review", "For Approval")')
    elif status_filter == 'approved':
        conditions.append('supply_requests.status IN ("Approved", "Issued")')
    elif status_filter == 'rejected':
        conditions.append('supply_requests.status = "Rejected"')
    elif status_filter == 'returned':
        conditions.append('supply_requests.status = "Returned"')
    elif status_filter == 'draft':
        conditions.append('supply_requests.status = "Draft"')
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    query += ' ORDER BY supply_requests.request_date DESC, supply_requests.request_id DESC'
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    cursor.execute('SELECT * FROM departments ORDER BY department_name')
    department_list = cursor.fetchall()
    cursor.execute('SELECT * FROM employees ORDER BY first_name, last_name')
    employee_list = cursor.fetchall()
    conn.close()
    totals = {'total': len(rows), 'pending': 0, 'approved': 0, 'rejected': 0, 'other': 0}
    by_department = {}
    by_employee = {}
    for row in rows:
        group = status_group(row['status'])
        totals[group] += 1
        add_to_summary(by_department, row['department_name'] or 'No department', group)
        add_to_summary(by_employee, ((row['first_name'] or '') + ' ' + (row['last_name'] or '')).strip(), group)
    department_summary = sorted(by_department.values(), key=lambda d: d['name'])
    employee_summary = sorted(by_employee.values(), key=lambda d: d['name'])
    return render_template('request_report.html', rows=rows, totals=totals, department_summary=department_summary, employee_summary=employee_summary, department_list=department_list, employee_list=employee_list, date_from=date_from, date_to=date_to, selected_department=department_filter, selected_employee=employee_filter, selected_status=status_filter)
 
if __name__ == '__main__':  
    app.run(host="0.0.0.0", port=5500) 
