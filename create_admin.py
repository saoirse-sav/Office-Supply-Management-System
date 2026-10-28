import getpass
from werkzeug.security import generate_password_hash
from db import get_connection

roles = [
    ('Administrator', 'Full system access'),
    ('Supply Officer', 'Supplies, inventory, and issuance'),
    ('Requestor', 'Creates and views own requests'),
    ('Department Head', 'Approves requests'),
    ('Inventory Clerk', 'Stock management'),
    ('Management', 'Reports and dashboard'),
]

conn = get_connection()
cursor = conn.cursor(dictionary=True)

# Make sure all roles exist
for role_name, description in roles:
    cursor.execute('SELECT role_id FROM roles WHERE role_name=%s', (role_name,))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO roles (role_name, description) VALUES (%s, %s)', (role_name, description))

username = input('Username: ')
password = getpass.getpass('Password (at least 8 characters, hidden while typing): ')

if len(password) < 8:
    print('That password is too short. Nothing was changed.')
else:
    cursor.execute('SELECT user_id FROM users WHERE username=%s', (username,))
    existing = cursor.fetchone()
    new_hash = generate_password_hash(password)
    if existing:
        cursor.execute('UPDATE users SET password_hash=%s, failed_attempts=0, locked_until=NULL WHERE user_id=%s', (new_hash, existing['user_id']))
        print('Password reset for ' + username + '. Any lock on the account was cleared.')
    else:
        cursor.execute('SELECT role_id FROM roles WHERE role_name="Administrator"')
        admin_role = cursor.fetchone()
        cursor.execute('INSERT INTO users (username, password_hash, role_id) VALUES (%s, %s, %s)', (username, new_hash, admin_role['role_id']))
        print('Administrator account created for ' + username + '.')

conn.commit()
conn.close()