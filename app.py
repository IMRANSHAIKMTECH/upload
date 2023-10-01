from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
import psycopg2
from psycopg2 import sql



app = Flask(__name__)

app.secret_key = '154'

# PostgreSQL database configuration
db_params = {
    'dbname': 'users_mbbc',
    'user': 'users_mbbc_user',
    'password': 'SxOuCWvFkV5wQnWKeiyiOEzz0HN4pKeJ',
    'host': 'dpg-ckckb66ct0pc73chqta0-a.oregon-postgres.render.com',
    'port': '5432'
}

# Connect to the PostgreSQL database
def connect_to_db():
    try:
        conn = psycopg2.connect(**db_params)
        return conn
    except Exception as e:
        print("Connection failed:", str(e))
        return None

# Initialize the SQLAlchemy database
def initialize_db():
    conn = connect_to_db()
    if conn is not None:
        cursor = conn.cursor()
        # Create a User table if it doesn't exist
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS user_data (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            created_date DATE NOT NULL,
            expiry_date DATE
        );
        """
        cursor.execute(create_table_sql)
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialization completed.")

initialize_db()

# Define the User model to match the "user_data" table
class User:
    def __init__(self, id, email, password, created_date, expiry_date):
        self.id = id
        self.email = email
        self.password = password
        self.created_date = created_date
        self.expiry_date = expiry_date

excelfile=None
# Routes for login, admin, and user pages
@app.route('/', endpoint='homepage')
def homepage():   
    global excelfile
    session.clear()
    app.first_request_done = True
    students.clear()
    if excelfile is None:
        print("No file to process.") 

    # Delete the previous file
    elif os.path.exists(excelfile.filename):
        os.remove(excelfile.filename)

    # Clear the uploaded file variable
    excelfile = None
    print("claered all sessions")

    if 'user_id' in session:
         return redirect(url_for('user_dashboard'))
    return render_template('index.html')

# Route to fetch and display all data from the user_data table
@app.route('/all_data', methods=['GET'])
def all_data():
    try:
        conn = connect_to_db()
        if conn is not None:
            cursor = conn.cursor()

            # Execute a SELECT query to fetch all user records
            select_query = "SELECT id, email, password, created_date, expiry_date FROM user_data"
            cursor.execute(select_query)
            
            # Fetch all rows and store them in a list of dictionaries
            user_data = []
            for row in cursor.fetchall():
                id, email, password, created_date, expiry_date = row
                user_data.append({
                    'id': id,
                    'email': email,
                    'password': password,
                    'created_date': created_date.strftime('%Y-%m-%d'),
                    'expiry_date': expiry_date.strftime('%Y-%m-%d') if expiry_date else None
                })

            # Close the cursor and connection
            cursor.close()
            conn.close()

            return jsonify({'users': user_data})
        else:
            return jsonify({'error': 'Database connection failed'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/login', methods=['GET', 'POST'], endpoint='login')
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the user is an admin
        if username == "admin@admin" and password == "123":
            session['user_id'] = 'admin'  # Set a session variable for admin
            return redirect(url_for('admin_page'))

        try:
            conn = connect_to_db()
            if conn is not None:
                cursor = conn.cursor()

                # Execute a SELECT query to find a user with the given username and password
                select_query = "SELECT id FROM user_data WHERE email = %s AND password = %s"
                cursor.execute(select_query, (username, password))
                user_id = cursor.fetchone()

                # Close the cursor and connection
                cursor.close()
                conn.close()

                if user_id:
                    session['user_id'] = user_id[0]  # Set a session variable for the authenticated user
                    flash('Logged in successfully!', 'success')
                    return redirect(url_for('user_dashboard'))
                else:
                    flash('Login failed. Please check your credentials.', 'danger')
            else:
                flash('Database connection failed.', 'danger')
        except Exception as e:
            flash('Login failed. Please check your credentials.', 'danger')
            print("Error during login:", str(e))

    return render_template('index.html')

@app.route('/admin')
def admin_page():
    if 'user_id' in session:
        try:
            conn = connect_to_db()
            if conn is not None:
                cursor = conn.cursor()

                # Execute a SELECT query to fetch all user records
                select_query = "SELECT id, email, password, created_date, expiry_date FROM user_data"
                cursor.execute(select_query)

                # Fetch all rows and store them in a list of dictionaries
                users = []
                # Remove strftime calls when fetching data
                for row in cursor.fetchall():
                    id, email, password, created_date, expiry_date = row
                    users.append({
                        'id': id,
                        'email': email,
                        'password': password,
                        'created_date': created_date,  # Do not use strftime
                        'expiry_date': expiry_date if expiry_date else None  # Do not use strftime
                    })


                # Close the cursor and connection
                cursor.close()
                conn.close()

                return render_template('admin.html', users=users)
            else:
                flash('Database connection failed.', 'danger')
                return redirect(url_for('login'))
        except Exception as e:
            flash('Error fetching users: ' + str(e), 'danger')
            return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))


# Route to update user based on email address
@app.route('/update_user/<string:email>', methods=['POST'])
def update_user(email):
    updated_expiry_date_str = request.form.get('expiry_date')  # Get the date as a string from the form
    try:
        # Parse the date string to a datetime object
        updated_expiry_date = datetime.strptime(updated_expiry_date_str, '%Y-%m-%d')

        # Connect to the database
        conn = connect_to_db()
        if conn is not None:
            cursor = conn.cursor()

            # Execute an UPDATE query to update the user's expiry_date
            update_query = "UPDATE user_data SET expiry_date = %s WHERE email = %s"
            cursor.execute(update_query, (updated_expiry_date, email))

            # Commit the changes and close the cursor and connection
            conn.commit()
            cursor.close()
            conn.close()

            flash('User expiration date updated successfully!', 'success')
        else:
            flash('Database connection failed.', 'danger')
    except Exception as e:
        flash('Error updating user: ' + str(e), 'danger')

    return redirect(url_for('admin_page'))

# Route to delete user based on email address
@app.route('/delete_user/<string:email>')
def delete_user(email):
    try:
        # Connect to the database
        conn = connect_to_db()
        if conn is not None:
            cursor = conn.cursor()

            # Execute a DELETE query to delete the user by email
            delete_query = "DELETE FROM user_data WHERE email = %s"
            cursor.execute(delete_query, (email,))

            # Commit the changes and close the cursor and connection
            conn.commit()
            cursor.close()
            conn.close()

            flash('User deleted successfully!', 'success')
        else:
            flash('Database connection failed.', 'danger')
    except Exception as e:
        flash('Error deleting user: ' + str(e), 'danger')

    return redirect(url_for('admin_page'))


@app.route('/add_user', methods=['POST'])
def add_user():
    new_username = request.form.get('new_username')
    new_password = request.form.get('new_password')
    new_expiry_date = request.form.get('expiry_date')

    try:
        # Connect to the database
        conn = connect_to_db()
        if conn is not None:
            cursor = conn.cursor()

            # Execute an INSERT query to add the new user
            insert_query = "INSERT INTO user_data (email, password, created_date, expiry_date) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (new_username, new_password, datetime.now(), new_expiry_date))

            # Commit the changes and close the cursor and connection
            conn.commit()
            cursor.close()
            conn.close()

            flash('New user added successfully!', 'success')
        else:
            flash('Database connection failed.', 'danger')
    except Exception as e:
        flash('Error adding new user: ' + str(e), 'danger')

    return redirect(url_for('admin_page'))



@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' in session:
        user_id = session['user_id']
        user_data = None

        try:
            # Connect to the database
            conn = connect_to_db()
            if conn is not None:
                cursor = conn.cursor()

                # Execute a SELECT query to retrieve user data based on user_id
                select_query = "SELECT email, expiry_date FROM user_data WHERE id = %s"
                cursor.execute(select_query, (user_id,))
                user_data = cursor.fetchone()

                # Close the cursor and connection
                cursor.close()
                conn.close()

                if user_data:
                    user_email, expiry_date = user_data
                    # Check if the user has an expiry date
                    if expiry_date:
                        current_date = datetime.now().date()
                        days_left = (expiry_date - current_date).days
                        subscription_days_left = days_left
                    else:
                        subscription_days_left = None
                        return "Subscription Expired"

                    return render_template('user.html', user_email=user_email, subscription_days_left=subscription_days_left)
            else:
                flash('Database connection failed.', 'danger')
        except Exception as e:
            flash('Error retrieving user data: ' + str(e), 'danger')

    return redirect(url_for('login'))



driver = None

@app.route('/logout')
def logout():
    global driver
    if driver:
        driver.quit()
        driver = None

    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))


absent_students=[]
students=[]
students.clear()
absent_students.clear()
student_messages = {}
student_messages.clear()
import logging

# send messages
def create_driver():
    print("creating driver")

    # Use webdriver_manager to download and manage ChromeDriver
    driver = webdriver.Chrome(ChromeDriverManager().install())

    # Open WhatsApp Web
    driver.get('https://web.whatsapp.com/')

    # Wait for 30 seconds for the QR code to be scanned
    time.sleep(30)
  
    # Re-create the WebDriver in headless mode
    driver.minimize_window()

    return driver

def send_msgs(student_messages):
    print("send msgs")
    print(student_messages)

    driver = create_driver()

    for item in student_messages:
        phone_number, messages = item
        print(f"Sending messages to {phone_number}:")
        print(messages)
        print("inside for loop")

        # Wait for the search box to be present on the page
        search_box_locator = (By.XPATH, '//div[@contenteditable="true" and @data-tab="3"]')
        WebDriverWait(driver, 60).until(EC.presence_of_element_located(search_box_locator))
        print("located chat box")

        # Locate the search box and search for a contact by mobile number
        contact_number = phone_number  # Replace with the mobile number you want to chat with
        search_box = driver.find_element(*search_box_locator)
        search_box.send_keys(contact_number)
        search_box.send_keys(Keys.ENTER)

        # Wait for the chat to load (check if the input box is available)
        input_box_locator = (By.XPATH, '/html/body/div[1]/div/div/div[5]/div/footer/div[1]/div/span[2]/div/div[2]/div[1]/div[2]/div/p')
        WebDriverWait(driver, 30).until(EC.presence_of_element_located(input_box_locator))

        # Move the cursor to the message input box and send the messages
        message_box = driver.find_element(*input_box_locator)

        # Combine all messages into one string
        combined_message = "".join(messages)
        print("Combined Message:")
        print(combined_message)

        # Send the entire message at once
        ActionChains(driver).move_to_element(message_box).click().send_keys(combined_message).send_keys(Keys.ENTER).perform()
        print("sent")

    print("No numbers remaining")
    # Close the WebDriver when you're done
    time.sleep(5)
    driver.quit()

df=None
# displaying columnsname
@app.route('/show', methods=['GET', 'POST'])
def show():
    columns = []
    global df
    if request.method == 'POST':
        # Check if a file is uploaded
        if 'attfile' not in request.files:
            return render_template('user.html', error='No file part')

        file = request.files['attfile']
        # excelfile= request.files['attfile']

        # Check if the file has a name
        if file.filename == '':
            return render_template('user.html', error='No selected file')

        # Check if it's an Excel file
        if not file.filename.endswith('.xlsx') and not file.filename.endswith('.xls'):
            return render_template('user.html', error='Invalid file format. Please upload an Excel file')

        try:
            import pandas as pd

            # Read the Excel file and extract column names
            df = pd.read_excel(file)
            columns = df.columns.tolist()
        except Exception as e:
            return render_template('user.html', error=str(e))

    return render_template('user.html', columns=columns)

combined_data = []

@app.route('/pr', methods=['POST'])
def pr():
    print("working pr")
    global combined_data,df

    # Get the user's message from the form
    user_message = request.form.get('usermessage')

    # Ensure that there are selected columns
    if not user_message:
        return "User message is missing."
    import pandas as pd

# Assuming 'excelfile' contains the file path or a file object
    print(df)
    # if excelfile is not None and not excelfile.closed:
    #     try:
    #         with pd.ExcelFile(excelfile) as xls:
    #             df = pd.read_excel(xls, sheet_name='Sheet1')  # Replace 'Sheet1' with the actual sheet name
    #     except Exception as e:
    #         return f"Error reading Excel file: {str(e)}"
    # else:
    #     return "No file to process."


            

    # Combine phone numbers with messages based on selected columns
    combined_data = []
    for index, row in df.iterrows():
        message = user_message

        # Replace placeholders like @columnname with actual data
        for col in df.columns:
            placeholder = f"@{col}"
            data = str(row[col])  # Convert data to string
            message = message.replace(placeholder, f"{data}")

        combined_data.append([str(row['number']), str(message)])

    print("sending messages")
    send_msgs(combined_data)
    # Print the combined data in the terminal
    for number, message in combined_data:
        print(f"Phone: {number}, Message: {message}")

    flash('Messages sent successfully!', 'success')

    # Redirect to the user_dashboard route
    return redirect(url_for('user_dashboard'))

if __name__ == "__main__":
    app.run( debug=True)
