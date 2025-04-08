# Import necessary libraries
from flask import Flask,render_template,request,session,redirect,url_for,Response
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from camera import VideoCamera
import os
from werkzeug.utils import secure_filename
from camera import process_image

# Initialize the web app
app = Flask(__name__)

# configure for file uploads, the allowed file types and storage
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
PREDICTED_FOLDER = os.path.join('static', 'predicted')
app.config['PREDICTED_FOLDER'] = PREDICTED_FOLDER

# check if uploaded file has the allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# secret key for sessions
app.secret_key='default_key'

# Database configuration
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='emotion_db'

# initialize the MySQL connection
mysql=MySQL(app)

# Index page
@app.route('/',methods=['GET','POST'])
def index():
    #store the messages for errors
    msg=''
    #check if the request method is POST
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        #create a cursor
        cursor=mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email=%s AND password=%s',(email,password))
        account=cursor.fetchone()
        #check if account exists
        if account:
            session['loggedin']=True
            session['id']=account['id']
            session['email']=account['email']
            return redirect(url_for('home'))
        else:
            #if account does not exist, show an error message
            msg='Invalid email or password!'
    return render_template('index.html',msg=msg)

#register route
@app.route('/register',methods=['GET','POST'])
def register():
    msg=''
    if request.method=='POST':
        #get the form data
        fName=request.form['fName']
        lName=request.form['lName']
        gender=request.form['gender']
        email=request.form['email']
        password=request.form['password']

        cursor =mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email=%s',(email,))
        #check if the email already exists
        account=cursor.fetchone()
        if account:
            #display an error message, if the email already exists
            msg='Email already exists!'
            # ensure the format is correct
        elif not re.match(r'^[a-zA-Z0-9]+(?:\.[a-zA-Z0-9]+)*@gmail\.com$', email):
            msg = 'Invalid email address!'
        else:
            cursor.execute('INSERT INTO users (fName,lName,gender,email,password) VALUES (%s,%s,%s,%s,%s)',(fName,lName,gender,email,password))
            #commit the data to the database
            mysql.connection.commit()
            return redirect(url_for('index'))
    return render_template('register.html',msg=msg)

@app.route('/home')
def home():
    # check to see if the user is logged in
    if 'loggedin' not in session:
        # if not, redirect to the login page
        return redirect(url_for('index'))
    # if logged in, display the home page
    return render_template('home.html')

# Image prediction for emotion recognition
@app.route('/predict',methods=['GET', 'POST'])
def predict():
    msg=''
    # check if post request has file part
    if request.method=='POST':  
        # get the file from the post request
        file = request.files['imagefile'] 
        # only allow image files
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            predicted_path=os.path.join(app.config['PREDICTED_FOLDER'], filename)
            # write the filename for the predicted image
            predicted_filename = "predicted_" + filename
            # path for the saving the predicted image
            predicted_path = os.path.join(PREDICTED_FOLDER, predicted_filename)
            file.save(predicted_path)
            # call the process image function to predict the image
            result=process_image(predicted_path, predicted_path)

            # display the processed image
            return render_template('predict.html', image_path=predicted_filename)
        else:
            # display the an error message if the file is not allowed
            msg='Invalid file type! Only images are allowed!'
    return render_template('predict.html',msg=msg)

# Emotion recognition via webcam
@app.route('/main')
def main():
    return render_template('main.html')

def gen(camera):
    while True:
        frame=camera.get_frame()
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# Video frame in main page
@app.route('/video')
def video():
    return Response(gen(VideoCamera()),mimetype='multipart/x-mixed-replace; boundary=frame')

# logout user when they press logout
@app.route('/logout')
def logout():
    session.pop('loggedin',None)
    session.pop('id',None)
    session.pop('email',None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)