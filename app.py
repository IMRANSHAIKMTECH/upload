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



app = Flask(__name__, static_url_path='/static', template_folder='E:\\python\\school-(whatsapp application)\\templates')

app.secret_key = '154'




app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://users_mbbc_user:SxOuCWvFkV5wQnWKeiyiOEzz0HN4pKeJ@dpg-ckckb66ct0pc73chqta0-a/users_mbbc'

# try:
#     conn = psycopg2.connect(
#         "dbname=users_mbbc user=users_mbbc_user password=SxOuCWvFkV5wQnWKeiyiOEzz0HN4pKeJ host=dpg-ckckb66ct0pc73chqta0-a port=5432"
#     )
#     print("Connection successful!")
#     conn.close()
# except Exception as e:
#     print("Connection failed:", str(e))


# Initialize the SQLAlchemy database
db = SQLAlchemy(app)
print("working db")
# Define the User model to match the "user_data" table
class User(db.Model):
    __tablename__ = 'user_data'  # Specify the table name
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date)

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
        users = User.query.all()
        user_data = []

        for user in users:
            user_data.append({
                'id': user.id,
                'email': user.email,
                'password': user.password,
                'created_date': user.created_date.strftime('%Y-%m-%d'),
                'expiry_date': user.expiry_date.strftime('%Y-%m-%d') if user.expiry_date else None
            })

        return jsonify({'users': user_data})
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

        # Query the User table to find a user with the given username and password
        user = User.query.filter_by(email=username, password=password).first()

        if user is not None:
            session['user_id'] = user.id  # Set a session variable for the authenticated user
            flash('Logged in successfully!', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Login failed. Please check your credentials.', 'danger')

    return render_template('index.html')

@app.route('/admin')
def admin_page():
    if 'user_id' in session:
        # Use SQLAlchemy to fetch users
        users = User.query.all()
        return render_template('admin.html', users=users)
    else:
        return redirect(url_for('login'))

# Route to update user based on email address
@app.route('/update_user/<string:email>', methods=['POST'])
def update_user(email):
    updated_expiry_date_str = request.form.get('expiry_date')  # Get the date as a string from the form
    try:
        # Parse the date string to a datetime object
        updated_expiry_date = datetime.strptime(updated_expiry_date_str, '%Y-%m-%d')
        
        # Use SQLAlchemy to query for the user by email
        user = User.query.filter_by(email=email).first()
        
        if user:
            user.expiry_date = updated_expiry_date  # Update the user's expiry date
            db.session.commit()  # Commit changes using SQLAlchemy
            flash('User expiration date updated successfully!', 'success')
        else:
            flash('User not found.', 'danger')
    except Exception as e:
        flash(f'Error updating user: {str(e)}', 'danger')
    
    return redirect(url_for('admin_page'))


# Route to delete user based on email address
@app.route('/delete_user/<string:email>')
def delete_user(email):
    try:
        # Use SQLAlchemy to query for the user by email
        user = User.query.filter_by(email=email).first()
        
        if user:
            db.session.delete(user)  # Delete the user object
            db.session.commit()  # Commit changes using SQLAlchemy
            flash('User deleted successfully!', 'success')
        else:
            flash('User not found.', 'danger')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('admin_page'))


@app.route('/add_user', methods=['POST'])
def add_user():
    new_username = request.form.get('new_username')
    new_password = request.form.get('new_password')  
    new_expiry_date = request.form.get('expiry_date')
    
    try:
        new_user = User(email=new_username, password=new_password, created_date=datetime.now(), expiry_date=new_expiry_date)
        db.session.add(new_user)  # Add the new user object to the session
        db.session.commit()  # Commit changes using SQLAlchemy

        flash('New user added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding new user: {str(e)}', 'danger')
        print(f"Error adding new user: {str(e)}")  

    return redirect(url_for('admin_page'))


@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])  # Retrieve the user based on user_id

        # Check if the user has an expiry date
        if user.expiry_date:
            current_date = datetime.now().date()
            days_left = (user.expiry_date - current_date).days
            subscription_days_left = days_left
        else:
            subscription_days_left = None
            return("Subscription Expired")

        return render_template('user.html', user_email=user.email, subscription_days_left=subscription_days_left)
    
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
