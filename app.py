import os
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_connection

app = Flask(__name__)
app.secret_key = os.environ.get('OSMS_SECRET_KEY', 'dev-only-key-change-before-deployment')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

def get_number(cursor, query):
    # Runs a query that returns one number called n
    cursor.execute(query)
    return int(cursor.fetchone()['n'])


def get_chart_data(cursor, query):
    # Runs a query that returns chart_label and chart_value, and splits them into two lists
    cursor.execute(query)
    rows = cursor.fetchall()
    return [str(row['chart_label']) for row in rows], [int(row['chart_value']) for row in rows]


@app.route('/')
def home():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    total_supplies = get_number(cursor, 'SELECT COUNT(*) AS n FROM supplies')
    active_suppliers = get_number(cursor, 'SELECT COUNT(*) AS n FROM suppliers WHERE status = "Active"')
    pending_requests = get_number(cursor, 'SELECT COUNT(*) AS n FROM supply_requests WHERE status IN ("Submitted", "Under Review", "For Approval")')
    for_approval = get_number(cursor, 'SELECT COUNT(*) AS n FROM supply_requests WHERE status = "For Approval"')
    issued_this_month = get_number(cursor, 'SELECT COALESCE(SUM(issuance_items.issued_qty), 0) AS n FROM issuance_items JOIN issuances ON issuance_items.issuance_id = issuances.issuance_id WHERE YEAR(issuances.issuance_date) = YEAR(CURDATE()) AND MONTH(issuances.issuance_date) = MONTH(CURDATE())')
    low_stock = get_number(cursor, 'SELECT COUNT(*) AS n FROM supplies LEFT JOIN inventory ON supplies.supply_id = inventory.supply_id WHERE supplies.status = "Active" AND COALESCE(inventory.current_stock, 0) > 0 AND COALESCE(inventory.current_stock, 0) <= supplies.reorder_level')
    out_of_stock = get_number(cursor, 'SELECT COUNT(*) AS n FROM supplies LEFT JOIN inventory ON supplies.supply_id = inventory.supply_id WHERE supplies.status = "Active" AND COALESCE(inventory.current_stock, 0) = 0')
    category_labels, category_values = get_chart_data(cursor, 'SELECT COALESCE(supply_categories.category_name, "Uncategorized") AS chart_label, COUNT(*) AS chart_value FROM supplies LEFT JOIN supply_categories ON supplies.category_id = supply_categories.category_id GROUP BY supply_categories.category_name ORDER BY chart_value DESC')
    department_labels, department_values = get_chart_data(cursor, 'SELECT COALESCE(departments.department_name, "No department") AS chart_label, COUNT(*) AS chart_value FROM supply_requests LEFT JOIN departments ON supply_requests.department_id = departments.department_id GROUP BY departments.department_name ORDER BY chart_value DESC')
    monthly_labels, monthly_values = get_chart_data(cursor, 'SELECT CONCAT(YEAR(issuances.issuance_date), "-", LPAD(MONTH(issuances.issuance_date), 2, "0")) AS chart_label, SUM(issuance_items.issued_qty) AS chart_value FROM issuance_items JOIN issuances ON issuance_items.issuance_id = issuances.issuance_id WHERE issuances.issuance_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) GROUP BY chart_label ORDER BY chart_label')
    requested_labels, requested_values = get_chart_data(cursor, 'SELECT supplies.supply_name AS chart_label, SUM(request_items.requested_qty) AS chart_value FROM request_items JOIN supply_requests ON request_items.request_id = supply_requests.request_id JOIN supplies ON request_items.supply_id = supplies.supply_id WHERE supply_requests.status <> "Draft" GROUP BY supplies.supply_id ORDER BY chart_value DESC LIMIT 5')
    issued_labels, issued_values = get_chart_data(cursor, 'SELECT supplies.supply_name AS chart_label, SUM(issuance_items.issued_qty) AS chart_value FROM issuance_items JOIN supplies ON issuance_items.supply_id = supplies.supply_id GROUP BY supplies.supply_id ORDER BY chart_value DESC LIMIT 5')
    cursor.execute('SELECT CONCAT(YEAR(created_at), "-", LPAD(MONTH(created_at), 2, "0")) AS chart_label, SUM(CASE WHEN transaction_type = "Stock In" THEN quantity ELSE 0 END) AS stock_in, SUM(CASE WHEN transaction_type = "Issued" THEN ABS(quantity) ELSE 0 END) AS stock_out FROM inventory_transactions WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH) GROUP BY chart_label ORDER BY chart_label')
    movement_rows = cursor.fetchall()
    movement_labels = [row['chart_label'] for row in movement_rows]
    movement_in = [int(row['stock_in']) for row in movement_rows]
    movement_out = [int(row['stock_out']) for row in movement_rows]
    cursor.execute('SELECT supplies.supply_name, supplies.reorder_level, COALESCE(inventory.current_stock, 0) AS stock FROM supplies LEFT JOIN inventory ON supplies.supply_id = inventory.supply_id WHERE supplies.status = "Active" AND COALESCE(inventory.current_stock, 0) <= supplies.reorder_level ORDER BY COALESCE(inventory.current_stock, 0), supplies.supply_name LIMIT 8')
    low_rows = cursor.fetchall()
    low_labels = [row['supply_name'] for row in low_rows]
    low_stock_values = [int(row['stock']) for row in low_rows]
    low_reorder_values = [int(row['reorder_level']) for row in low_rows]
    conn.close()
    return render_template('index.html', total_supplies=total_supplies, active_suppliers=active_suppliers, pending_requests=pending_requests, for_approval=for_approval, issued_this_month=issued_this_month, low_stock=low_stock, out_of_stock=out_of_stock, category_labels=category_labels, category_values=category_values, department_labels=department_labels, department_values=department_values, monthly_labels=monthly_labels, monthly_values=monthly_values, requested_labels=requested_labels, requested_values=requested_values, issued_labels=issued_labels, issued_values=issued_values, movement_labels=movement_labels, movement_in=movement_in, movement_out=movement_out, low_labels=low_labels, low_stock_values=low_stock_values, low_reorder_values=low_reorder_values)


@app.before_request
def require_login():
    # Every page except the login page and static files needs a logged-in user
    if request.endpoint in ('login', 'static'):
        return None
    if 'user_id' not in session:
        return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT users.*, roles.role_name, (users.locked_until IS NOT NULL AND users.locked_until > NOW()) AS is_locked FROM users JOIN roles ON users.role_id = roles.role_id WHERE users.username=%s', (username,))
        user = cursor.fetchone()
        if user and user['is_locked']:
            error = 'Too many failed attempts. This account is locked for 15 minutes.'
        elif user and user['status'] == 'Active' and check_password_hash(user['password_hash'], password):
            cursor.execute('UPDATE users SET failed_attempts=0, locked_until=NULL WHERE user_id=%s', (user['user_id'],))
            conn.commit()
            conn.close()
            session.clear()
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role_name']
            return redirect('/')
        else:
            error = 'Invalid username or password.'
            if user:
                attempts = (user['failed_attempts'] or 0) + 1
                if attempts >= 5:
                    cursor.execute('UPDATE users SET failed_attempts=0, locked_until=DATE_ADD(NOW(), INTERVAL 15 MINUTE) WHERE user_id=%s', (user['user_id'],))
                else:
                    cursor.execute('UPDATE users SET failed_attempts=%s WHERE user_id=%s', (attempts, user['user_id']))
                conn.commit()
        conn.close()
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


@app.route('/account/password', methods=['GET', 'POST'])
def change_password():
    error = None
    message = None
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT password_hash FROM users WHERE user_id=%s', (session['user_id'],))
        user = cursor.fetchone()
        if not check_password_hash(user['password_hash'], current_password):
            error = 'Your current password is incorrect.'
        elif len(new_password) < 8:
            error = 'The new password must be at least 8 characters long.'
        elif new_password != confirm_password:
            error = 'The new passwords do not match.'
        else:
            cursor.execute('UPDATE users SET password_hash=%s WHERE user_id=%s', (generate_password_hash(new_password), session['user_id']))
            conn.commit()
            message = 'Your password has been changed.'
        conn.close()
    return render_template('change_password.html', error=error, message=message)


if __name__ == '__main__':  
    app.run(host="0.0.0.0", port=5500) 
