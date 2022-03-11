######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'Poopdragon123$'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		first_name=request.form.get('first_name')
		last_name=request.form.get('last_name')
		hometown=request.form.get('hometown')
		gender=request.form.get('gender')
		birth_date=request.form.get('birth_date')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, first_name, last_name, hometown, gender, birth_date) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, first_name, last_name, hometown, gender, birth_date)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile", photos=getUsersPhotos(uid), friends = getUserFriendList(uid), base64=base64 )


###################### Photos and Albums #################################
#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getAllPhotos():
	cursor = conn.cursor()
	cursor.execute("SELECT data, photo_id, caption FROM Photos")
	return cursor.fetchall()


@app.route('/see_all_photos', methods = ['GET'])
def search_for_photos ():
		photos = getAllPhotos ()
		return render_template('see_all_photos.html', photos = photos, base64=base64, message = 'Welcome')

@app.route('/delete_photo', methods=['GET', 'POST'])
@flask_login.login_required
def delete_photo():
	if request.method == 'POST':
		photo_id = request.form.get('photo_id')
		cursor = conn.cursor()
		cursor.execute("DELETE FROM Comments WHERE photo_id = {0}".format(photo_id))
		cursor.execute("DELETE FROM Photos WHERE photo_id = {0}".format(photo_id))
		conn.commit()
		return flask.redirect(flask.url_for('protected', message = 'you have deleted a picture and all of its comments '))
	else:
		return render_template('delete_photo_input.html')

@app.route('/create_an_album', methods=['GET', 'POST'])
@flask_login.login_required
def create_an_album():
	if request.method == 'POST':
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		nameofalbum = request.form.get('name')
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Albums (name, user_id) VALUES ('{0}', '{1}')".format(nameofalbum, user_id))
		conn.commit()
		return render_template ('congrat_album.html', name = nameofalbum)
	else:
		return render_template ('create_an_album.html')


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Photos (data, user_id, caption) VALUES (%s, %s, %s )''' ,(photo_data, uid, caption))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid),base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code



################################## Friends ########################################
def getNamefromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, last_name FROM Users WHERE email = {0}".format(email))
    result = cursor.fetchone()
    name = [str(i) for i in result]
    return name

def getnamefromId(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, last_name FROM Users WHERE user_id = {0}".format(uid))
    result = cursor.fetchone()
    name = [str(i) for i in result]
    return name

def getUserFriendList(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = {0}".format(uid))
    result = cursor.fetchall()
    fid = [i[0] for i in result]
    friend = []
    for f in fid:
        cursor.execute("SELECT first_name, last_name FROM Users WHERE user_id = {0}".format(f))
        friend.append(cursor.fetchone())
    friendList = [(str(i[0]), str(i[1])) for i in friend]
    return friendList


@app.route('/add_friend', methods = ['GET','POST'])
@flask_login.login_required
def add_friends ():
	if request.method == 'POST':
		user_id1 = getUserIdFromEmail(flask_login.current_user.id)
		user_id2 = request.form.get('user_id2')
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Friends (user_id1, user_id2) VALUE ('{0}', '{1}')".format(user_id1, user_id2))
		conn.commit()
		return render_template('congrat.html', friend = getnamefromId(user_id2))
	else:
		return render_template('add_friend.html')

########################################## Comments #################################################

#get comments for a certain picture
def getPicComments(photo_id):
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM Comments WHERE photo_id = {0}".format(photo_id))
    c = cursor.fetchall()
    Comments = [i[0] for i in c]
    return Comments

@app.route('/write_comments', methods=['GET', 'POST'])
def write_comments ():
	if request.method == 'POST' :
		photo_id = request.form.get('photo_id')
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		text = request.form.get('text')
		date = request.form.get('date')
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Comments (text, user_id, photo_id, date) VALUES ('{0}', '{1}', '{2}', '{3}')".format(text, user_id, photo_id, date))
		conn.commit()
		return render_template('congratcomment.html', comment = text)
	else:
		return render_template('write_comments.html')

@app.route('/show_comments', methods=['GET', 'POST'])
def show_comments ():
	if request.method == 'POST' :
		photo_id = request.form.get('photo_id')
		user_id = getUserIdFromEmail(flask_login.current_user.id)
		texts = getPicComments(photo_id)
		cursor = conn.cursor()
		conn.commit()
		return render_template('show_comment.html', comment = texts, photoID = photo_id, owner = getnamefromId(user_id))
	else:
		return render_template('search_for_comments.html')


#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welcome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)


##########################Recommendation###########################

@app.route('/recommendation', methods = ['GET','POST'])
@flask_login.login_required
def recommendation ():
	if request.method == 'POST':
		user_id1 = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute("SELECT user_id FROM Users ORDER BY RAND () LIMIT 1")
		result = cursor.fetchone()
		conn.commit()
		return render_template('recommendation.html', user = result, message = 'Here is your recommendation for friend!')
	else:
		return render_template('recommendation.html')




