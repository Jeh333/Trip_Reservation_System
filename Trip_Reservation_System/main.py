from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import time

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Initialize the database
def init_db():
    with sqlite3.connect("reservations.db") as conn:
        with open("schema.sql") as f:
            conn.executescript(f.read())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect('reservations.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM admins WHERE username = ? AND password = ?", (username, password))
            admin = cur.fetchone()

        if admin:
            return redirect(url_for('view_seating_chart'))
        else:
            flash("Invalid username or password.")
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')

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
def reserve_seat():
    if request.method == 'POST':
        passenger_name = request.form['passengerName']
        row = int(request.form['seatRow'])
        column = int(request.form['seatColumn'])

        cost_matrix = get_cost_matrix()
        price = cost_matrix[row][column]
        e_ticket = f"ET-{row}-{column}-{int(time.time())}"  # Generate unique e-ticket

        with sqlite3.connect('reservations.db') as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO reservations (passengerName, seatRow, seatColumn, eTicketNumber) VALUES (?, ?, ?, ?)",
                (passenger_name, row, column, e_ticket)
            )
            conn.commit()

        flash(f"Reservation successful! Your e-ticket number is {e_ticket}")
        return redirect(url_for('index'))

    return render_template('reserve_seat.html')

def get_cost_matrix():
    return [[100, 75, 50, 100] for _ in range(12)]

# Initialize database and run the app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
