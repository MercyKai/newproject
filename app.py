# Import necessary libraries
from flask import Flask,render_template,request,session,redirect,url_for,Response
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re, os
from camera import VideoCamera, process_image
from werkzeug.utils import secure_filename

# Initialize the web app
app = Flask(__name__)

# Secret key for sessions
app.secret_key='default_key'

# Configure the allowed file extensions and folder for storage
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
PREDICTED_FOLDER = os.path.join('static', 'predicted')
app.config['PREDICTED_FOLDER'] = PREDICTED_FOLDER

# Check if an uploaded file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database configuration
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='emotion_db'

# initialize the MySQL connection
mysql=MySQL(app)

# Index page for login
@app.route('/',methods=['GET','POST'])
def index():
    # Store the messages for errors
    msg=''
    if request.method=='POST':
        # Get the form data
        email=request.form['email']
        password=request.form['password']
        # Create a database cursor
        cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Execute query to find if the account exists
        cursor.execute('SELECT * FROM users WHERE email=%s AND password=%s',(email,password))
        account=cursor.fetchone()
        if account:
            # If the account exists, mark the user as logged in and redirect to the home page
            session['loggedin'] = True
            return redirect(url_for('home'))
        else:
            # If the account does not exist, show an error message
            msg='Invalid email or password!'
    return render_template('index.html',msg=msg)

# Registration route
@app.route('/register',methods=['GET','POST'])
def register():
    msg=''
    if request.method=='POST':
        # Get the form data
        fName=request.form['fName']
        lName=request.form['lName']
        email=request.form['email']        
        password=request.form['password']

        cursor =mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email=%s',(email,))
        # Check if the email already exists
        account=cursor.fetchone()
        if account:
            # Display an error message, if the email already exists
            msg='Email already exists!'
            # Ensure the format is correct and if not, display an error message
        elif not re.match(r'^[a-zA-Z0-9](\.?[a-zA-Z0-9]){5,29}@gmail\.com$', email):
            msg = 'Invalid email address!'
        else:
            # Insert the new user into the database
            cursor.execute('INSERT INTO users (fName,lName,email,password) VALUES (%s,%s,%s,%s)',(fName,lName,email,password))
            # Commit the data to the database
            mysql.connection.commit()
            # Redirect to the login page
            return redirect(url_for('index'))
    return render_template('register.html',msg=msg)

# Home page route
@app.route('/home')
def home():
    # Check to see if the user is logged in
    if 'loggedin' not in session:
        # If not, redirect to the login page
        return redirect(url_for('index'))
    # If logged in, display the home page
    return render_template('home.html')

# Image prediction route for file uploads
@app.route('/predict',methods=['GET', 'POST'])
def predict():
    msg=''
    if request.method=='POST':  
        # Get the file from the post request
        file = request.files['imagefile'] 
        # Only allow image files with the allowed extensions
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Write a new filename for the predicted image
            predicted_filename = "predicted_" + filename
            # Define the path to save the predicted image
            predicted_path = os.path.join(app.config['PREDICTED_FOLDER'], predicted_filename)
            # Save the uploaded file to the predicted folder
            file.save(predicted_path)
            # Call the process image function to predict the image
            process_image(predicted_path)
            # Display the predicted image
            return render_template('predict.html', image_path=predicted_filename)
        else:
            # Display an error message if the file type is not allowed
            msg= 'Invalid file type! Only PNG, JPG, and JPEG are allowed.'
    return render_template('predict.html',msg=msg)

# Real-time Emotion recognition via webcam
@app.route('/main')
def main():
    return render_template('main.html')

# Function to generate video frames
def gen(camera):
    while True:
        # Capture and process frames
        frame=camera.get_frame()
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# Video streaming using webcam
@app.route('/video')
def video():
    # Stream video frames 
    return Response(gen(VideoCamera()),mimetype='multipart/x-mixed-replace; boundary=frame')

# Logout route for clearing session and redirects to login page
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)