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
    search = request.args.get('search','')
    base_query = 'SELECT supplies.*, supply_categories.category_name, units.unit_name FROM supplies LEFT JOIN supply_categories ON supplies.category_id = supply_categories.category_id LEFT JOIN units ON supplies.unit_id = units.unit_id' 
    if search: 
        base_query += ' WHERE supplies.supply_code LIKE %s OR supplies.supply_name LIKE %s OR supply_categories.category_name LIKE %s OR supplies.brand LIKE %s' 
        search_term = '%' + search + '%' 
        cursor.execute(base_query, (search_term, search_term, search_term, search_term)) 
    else: 
        cursor.execute(base_query)
    all_supplies = cursor.fetchall()
    conn.close()
    return render_template('supplies.html', supplies=all_supplies)

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
    conn.close() 
    return render_template('supply_profile.html', supply=supply)

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
    conn.close() 
    return render_template('supplier_profile.html', supplier=supplier, assigned_supplies=assigned_supplies)

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
        conn.commit() 
        conn.close() 
        return redirect('/receipts') 
    cursor.execute('SELECT * FROM suppliers WHERE status="Active"') 
    supplier_list = cursor.fetchall() 
    conn.close() 
    return render_template('add_receipt.html', suppliers=supplier_list)

 
if __name__ == '__main__':  
    app.run(debug=True)
