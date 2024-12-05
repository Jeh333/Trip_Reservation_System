from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import time
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def init_db():
    # Check if the database already exists
    if not os.path.exists("reservations.db"):
        with sqlite3.connect("reservations.db") as conn:
            with open("schema.sql") as f:
                conn.executescript(f.read())
        print("Database initialized.")
    else:
        # Verify the integrity of the existing database
        with sqlite3.connect("reservations.db") as conn:
            cur = conn.cursor()
            # Check for necessary tables
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reservations';")
            reservations_table_exists = cur.fetchone()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admins';")
            admins_table_exists = cur.fetchone()

            if not reservations_table_exists or not admins_table_exists:
                with open("schema.sql") as f:
                    conn.executescript(f.read())
                print("Missing tables were created.")
            else:
                print("Database is already initialized.")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        option = request.form['option']
        if option == 'admin':
            return redirect(url_for('admin'))
        elif option == 'reserve':
            return redirect(url_for('reserve'))
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check admin credentials
        with sqlite3.connect('reservations.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM admins WHERE username = ? AND password = ?", (username, password))
            admin = cur.fetchone()

        if admin:
            flash(f"Welcome, {username}!")
            return redirect(url_for('admin_portal'))  # Redirect to admin portal
        else:
            flash("Invalid username or password.")
            return redirect(url_for('admin'))  # Redirect back to login page

    # Render the login page for GET requests
    return render_template('admin.html')

def generate_eticket(first_name):
    base_string = "INFOTC4320"
    eticket = []
    
    # Alternate characters from first name and base string
    for i in range(max(len(first_name), len(base_string))):
        if i < len(first_name):
            eticket.append(first_name[i])  # Add character from first name
        if i < len(base_string):
            eticket.append(base_string[i])  # Add character from INFOTC4320

    # Join the list into a single string
    return ''.join(eticket)

@app.route('/admin_portal')
def admin_portal():
    with sqlite3.connect('reservations.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reservations")
        reservations = cur.fetchall()

        # Create seating chart
        seating_chart = [[None for _ in range(4)] for _ in range(12)]
        for res in reservations:
            row, col, name = res[2], res[3], res[1]
            seating_chart[row][col] = name

        # Calculate total sales
        total_sales = sum(get_cost_matrix()[res[2]][res[3]] for res in reservations)

    return render_template('admin_portal.html', seating_chart=seating_chart, total_sales=total_sales)

@app.route('/admin/seating_chart')
def view_seating_chart():
    with sqlite3.connect('reservations.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM reservations")
        reservations = cur.fetchall()

        # Generate seating chart
        seating_chart = [[None for _ in range(4)] for _ in range(12)]
        for res in reservations:
            row, col, name = res[2], res[3], res[1]
            seating_chart[row][col] = name

        # Calculate total sales
        total_sales = sum(get_cost_matrix()[res[2]][res[3]] for res in reservations)

    return render_template('seating_chart.html', seating_chart=seating_chart, total_sales=total_sales)

@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        passenger_name = request.form['first_name']
        row = int(request.form['seat_row']) - 1  # Subtract 1 to match 0-indexed seating
        column = int(request.form['seat_column']) - 1  # Subtract 1 to match 0-indexed seating

        # Check if the seat is already reserved
        with sqlite3.connect('reservations.db') as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM reservations WHERE seatRow = ? AND seatColumn = ?",
                (row, column)
            )
            seat_taken = cur.fetchone()[0] > 0  # If count > 0, the seat is taken

        if seat_taken:
            flash("This seat is already taken. Please choose a different seat.", "error")
            return redirect(url_for('reserve'))  # Redirect back to the reservation page

        # Generate the e-ticket using the updated function
        e_ticket = generate_eticket(passenger_name)

        # Insert reservation into the database
        with sqlite3.connect('reservations.db') as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber) VALUES (?, ?, ?, ?)",
                (passenger_name, row, column, e_ticket)
            )
            conn.commit()

        flash(f"Reservation successful! Your e-ticket number is {e_ticket}")
        return redirect(url_for('reserve'))

    # Generate the seating chart
    seating_chart = [["O" for _ in range(4)] for _ in range(12)]
    with sqlite3.connect('reservations.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT seatRow, seatColumn FROM reservations")
        reservations = cur.fetchall()
        for reservation in reservations:
            seat_row, seat_column = reservation
            seating_chart[seat_row][seat_column] = "X"

    return render_template('reserve.html', seating_chart=seating_chart)





def get_cost_matrix():
    return [[100, 75, 50, 100] for _ in range(12)]

# Initialize database and run the app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
