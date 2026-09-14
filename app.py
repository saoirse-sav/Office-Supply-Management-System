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
    cursor.execute('SELECT supplies.*, supply_categories.category_name, units.unit_name FROM supplies LEFT JOIN supply_categories ON supplies.category_id = supply_categories.category_id LEFT JOIN units ON supplies.unit_id = units.unit_id')
    all_supplies = cursor.fetchall()
    conn.close()
    return render_template('supplies.html', supplies=all_supplies)

@app.route('/supplies/add', methods=['GET', 'POST'])
def add_supply():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
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
        cursor.execute('INSERT INTO supplies (supply_code, supply_name, category_id, description, unit_id, brand, reorder_level, maximum_stock, unit_cost) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', (code, name, category_id, description, unit_id, brand, reorder_level, maximum_stock, unit_cost))
        conn.commit()
        conn.close()
        return redirect('/supplies')
    cursor.execute('SELECT * FROM supply_categories')
    category_list = cursor.fetchall()
    cursor.execute('SELECT * FROM units')
    unit_list = cursor.fetchall()
    conn.close()
    return render_template('add_supply.html',categories=category_list, units=unit_list)


      
if __name__ == '__main__':  
    app.run(debug=True)
