from flask import Flask,request,redirect, url_for, render_template,send_from_directory,session
from flask_sqlalchemy import SQLAlchemy
import re
import os
from werkzeug.utils import secure_filename
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] ='super-secret-key'
app.config['USERNAME'] = 'admin'
app.config['PASSWORD'] = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_accounts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

UPLOAD_FOLDER = 'static'

ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png','JPG'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['DataSet1'] = 'YoutubeSpamMergedData.csv'

app.config['DataSet2'] = 'impermium_verification_labels.csv'

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

db=SQLAlchemy(app)

class custdetails(db.Model):
	"""docstring for ClassName"""
	id=db.Column(db.Integer,primary_key=True)
	images = db.Column(db.String(100))
	category = db.Column(db.String(100))
	description = db.Column(db.String(100))
	price = db.Column(db.String(100))
	name = db.Column(db.String(100))
	phno= db.Column(db.String(100))
	Sold = db.Column(db.Boolean())

	def __init__(self, images,category,description,price,name,phno,Sold):
		self.images=images
		self.category=category
		self.description=description
		self.price=price
		self.name=name
		self.phno=phno
		self.Sold=Sold


class Login(db.Model):
    # __tablename__ = 'users'
    email = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(50))
    name = db.Column(db.String(30))
    Mobile = db.Column(db.String(11),unique=True)

    def __init__(self, email, password,name,Mobile):
        self.email = email
        self.password = password
        self.name = name
        self.Mobile=Mobile

    def __repr__(self):
        return '<Entry %r %r %r %r>' % (self.email, self.password,self.name,self.Mobile)

class showComments(db.Model):

	id = db.Column(db.Integer,primary_key=True)
	email= db.Column(db.String(100))
	discussion = db.Column(db.String(250))
	name = db.Column(db.String(30))
	ad=db.Column(db.String(30))

	def __init__(self,discussion,email,name,ad):
		self.email = email
		self.discussion = discussion
		self.name = name
		self.ad= ad



db.create_all()

@app.route('/')
def homepage():
	target1 = os.path.join(APP_ROOT,"static")
	if not os.path.isdir(target1):
		os.mkdir(target1)
	image_names = os.listdir(os.path.join(APP_ROOT,"static"))
	print(image_names)
	stmt = "SELECT description,phno FROM custdetails"
	cur=db.engine.execute(stmt).fetchall()
	print(cur)
	print(combineData(image_names,cur),len(cur))
	if len(cur) == 0:
		return render_template("mock.html")
	return render_template('ads.html',image_names=combineData(image_names,cur),length=len(cur),ad1=image_names[0],cnt=cur[0][0],ph=cur[0][1])


def authenticate(e, p):
    print(e)
    details=Login.query.filter_by(email=e).filter_by(password=p).all()
    print(details)
    if(len(details)>0):
        return True
    else:
        return False

@app.route('/signup',methods=['GET','POST'])
def signup():
	error=None
	if request.method=='POST':
		email=request.form['username']
		password=request.form['password']
		name=request.form['uname']
		confirmpassword = request.form['confirmpassword']
		Mobile=request.form['Mobile']
		error=validatenumber(Mobile)
		if error!="":
			return render_template("signup.html",error=error)
		count1=Login.query.filter_by(email=email).count()
		count2=Login.query.filter_by(Mobile=Mobile).count()
		if(count1 > 0 or count2 >0):
			error="User Already exists"
		else:
			if password!=confirmpassword:
				error="passwords did not match"

			else:
				user=Login(email=email,password=password,name=name,Mobile=Mobile)
				db.session.add(user)
				db.session.commit()
				return redirect(url_for('login'))
	return render_template('signup.html',error=error)

@app.route('/login',methods=['GET','POST'])
def login():
	error = None
	if request.method == 'POST':
		if(authenticate(request.form['username'], request.form['password'])):
		    users = db.engine.execute("select * from Login").fetchall()
		    for user in users:
		    	if request.form['username'] == user[0] and request.form['password'] == user[1]:
		    		cur= user
		    		break
		    print(users)
		    session['email'] = request.form['username']
		    session[request.form['username']]=request.form['password']
		    session['logged_in'] = True
		    session['user'] = cur[2]
		    session['Mobile'] = cur[3]
		    print("logged in session",session)
		    return redirect(url_for('displayAds'))
		else:
			count1=Login.query.filter_by(email=request.form['username']).count()
			if(count1>0):
				error="passwords dont match"
			else:
				error='user does not exist'
	return render_template('mock.html', error=error)

def validatenumber(string):
	if string[0] in ['9','8','7'] and len(string)==10:
		return ""
	else :
		return "Use a Valid Mobile Number"

def isDigit(string):
	return string.isdigit()

@app.route('/postAd',methods=["GET","POST"])
def postAd():
	print(session)
	if request.method == "POST":
		category=request.form['producttype']
		description=request.form['description']
		price=request.form['price']
		print("is digit",isDigit(price))

		if session['Mobile'] == None:
			name = request.form['name']
			phno=request.form['phno']
		else:
			name=session['user']
			phno=session['Mobile']

		print(session)

		error=validatenumber(phno)

		if(error!="" and isDigit(price)==False):
			return render_template('postAd.html',error=error,phoneNumber="Give NaturalNumbers!!!",name=session['user'],Mobile=session['Mobile'])
		if(error!=""):
			return render_template('postAd.html',error=error,phoneNumber="",name=session['user'],Mobile=session['Mobile'])
		if(isDigit(price)==False):
			return render_template('postAd.html',error="",phoneNumber="Give NaturalNumbers!!!",name=session['user'],Mobile=session['Mobile'])

		target = os.path.join(APP_ROOT,app.config['UPLOAD_FOLDER'])

		if not os.path.isdir(target):
			os.mkdir(target)

		# if not os.path.isdir()

		if "file" not in request.files:
			msg="Upload the image"
			return render_template("postAd.html",error=msg)

		file = request.files['file']
		print(file)

		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			MYDIR = os.path.dirname(__file__)
			file.save(os.path.join(MYDIR,app.config['UPLOAD_FOLDER'],filename))
			image=os.path.join(MYDIR,app.config['UPLOAD_FOLDER'],filename)
			user2=custdetails(images=image,category=category,description=description,price=price,name=session['user'],phno=session['Mobile'],Sold=False)
			# file.save(os.path.join(MYDIR + "/" + app.config['UPLOAD_FOLDER'] + "/" + filename))
			print(file)
			db.session.add(user2)
			db.session.commit()
			renameFile(filename)
			return redirect(url_for('displayAds'))
		else:
			error="File Format Not Allowed"
			return render_template('postAd.html',error=error,name = session['user'],Mobile=session['Mobile'])
	return render_template('postAd.html',error=None,name = session['user'],Mobile=session['Mobile'])

def allowed_file(filename):
	return '.' in filename and \
			filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def predictSpamOrAbuse(string,csv,Column1,Column2):
	a=string
	MYDIR = os.path.dirname(__file__)
	csv=os.path.join(MYDIR,csv)
	df = pd.read_csv(csv)
	df_data = df[[Column1,Column2]]

	df_x = df_data[Column1]
	df_y = df_data[Column2]

	print(df_y)
	print(df_x)

	corpus = df_x

	cv = CountVectorizer()
	X=cv.fit_transform(corpus)


	X_train,X_test,y_train,y_test = train_test_split(X,df_y,test_size=0.33,random_state=42)

	clf= MultinomialNB()
	clf.fit(X_train,y_train)
	clf.score(X_test,y_test)
	vect = cv.transform(a).toarray()
	my_prediction = clf.predict(vect)
	print("predicting Spam",my_prediction[0])
	print("predicting Abuse",my_prediction[0])
	return my_prediction[0]

def renameFiles(filename):
    MYDIR = os.path.dirname(__file__)
    images=os.path.join(MYDIR,app.config['UPLOAD_FOLDER'])
    i=1
    ordered_images = sorted(os.listdir(images), key=lambda x: (int(re.sub('\D','',x)),x))
    print(ordered_images)
    print(os.listdir(images))
    delete = "ThisIsTheImage"
    for image in os.listdir(os.path.join(MYDIR,app.config['UPLOAD_FOLDER'])):
        print(image)
        if image == filename:
            os.rename(os.path.join(os.path.join(MYDIR,app.config['UPLOAD_FOLDER']),image),os.path.join(os.path.join(MYDIR,app.config['UPLOAD_FOLDER']),delete))
        else:
            os.rename(os.path.join(os.path.join(MYDIR,app.config['UPLOAD_FOLDER']),image),os.path.join(os.path.join(MYDIR,app.config['UPLOAD_FOLDER']),str(i)))
            i+=1
        print("after renaming---->>>>>",os.listdir(os.path.join(MYDIR,app.config['UPLOAD_FOLDER'])))
    print("After deleting images---*****",os.listdir(os.path.join(MYDIR,app.config['UPLOAD_FOLDER'])))
    return delete


def update(file,content,Mobile):
	admin = custdetails.query.filter_by(id = file ).first()
	admin.Sold = True
	db.session.commit()

@app.route('/render_add/<filename>/<des>/<phno1>',methods=['GET','POST'])
def render_add(filename,des,phno1):
	ad = filename
	if request.method == 'POST':
		if request.form.get('Mark') != None:
			update(filename,des,phno1)
			return redirect(url_for('displayAds'))
		email = session['email']
		print(email)
		comment=request.form['content']
		print(comment)
		stmt= Login.query.filter_by(email=email).all()
		print(stmt)
		x=stmt[0].name
		print(x)
		print(app.config['DataSet1'])
		if(predictSpamOrAbuse([request.form['content']],app.config['DataSet2'],'Comment','Insult') == 0 and predictSpamOrAbuse([request.form['content']],app.config['DataSet1'],'CONTENT','CLASS') == 0):
		    user=showComments(email=email,name=x,discussion=comment,ad=ad)
		    print(user)
		    db.session.add(user)
		    db.session.commit()
		    db.session.close()
		stmt1 = "SELECT * FROM custdetails"
		print(stmt1)
		cur1=db.engine.execute(stmt1).fetchall()
		print(cur1)
		cur2=()
		for rows in cur1:
			if des == rows[3] and phno1 == rows[6]:
				cur2=rows
				break
		d=[]
		d.append(filename)
		d.append(cur2)
		print(d)
		a = ad.split(".")
		print(a[0])
		stmt1= showComments.query.filter_by(ad=ad).all()
		print(stmt1)
		return render_template('display.html',d=d,stmt=stmt1)
	print(session)
	print("rendering add ----------------------------------------->>>>>",filename,des,phno1)
	stmt1 = "SELECT * FROM custdetails"
	print(stmt1)
	cur1=db.engine.execute(stmt1).fetchall()
	print(cur1)
	cur2=()
	for rows in cur1:
		if des == rows[3] and phno1 == rows[6]:
			cur2=rows
			break
	d=[]
	d.append(filename)
	d.append(cur2)
	print(d)
	a = filename.split(".")
	print(a[0])
	stmt1= showComments.query.filter_by(ad=ad).all()
	print(stmt1)
	return render_template('display.html',d=d,stmt=stmt1)

def sessionclear():
	if not session:
		return redirect(url_for('displayAds'))
	email = session['email']
	session.pop(email,None)
	session.pop('logged_in', None)
	session.pop('email',None)
	session.pop('user',None)
	session.pop('Mobile',None)
	return

@app.route('/logout',methods=["GET"])
def logout():
	if not session:
		return redirect(url_for('displayAds'))
	sessionclear()
	print(session)
	return redirect(url_for('displayAds'))

@app.route('/upload/<filename>')
def send_image(filename):
	print(APP_ROOT,filename)
	return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def combineData(imgs,curs):
	d = {}
	i=0
	ordered_images = sorted(imgs, key=lambda x: (int(re.sub('\D','',x)),x))
	print(ordered_images)
	for image in ordered_images:
		print(image)
		if i>=0:
			d[image] = curs[i]
			print("Combing Data",d,curs[i])
		i=i+1

	print("Combined data",d)
	return d

def renameFile(filename):
	MYDIR = os.path.dirname(__file__)
	images=os.path.join(MYDIR,app.config['UPLOAD_FOLDER'])
	print(images)
	files = os.listdir(images)
	print(len(files))
	count = len(files)
	new_file_name = str(count)
	os.rename(os.path.join(images,filename),os.path.join(images,new_file_name))

@app.route("/displayAds")
def displayAds():
	target = os.path.join(APP_ROOT,app.config['UPLOAD_FOLDER'])
	if not os.path.isdir(target):
		os.mkdir(target)
	# target1 = os.path.join(APP_ROOT+"\\"+app.config['UPLOAD_FOLDER'])
	# MYDIR = os.path.dirname(__file__)
	# images=os.path.join(MYDIR + "/" + app.config['UPLOAD_FOLDER'])
	# if not os.path.isdir(target1):
		# os.mkdir(target1)
	image_names = os.listdir(target)
	print(image_names)
	stmt = "SELECT description,phno FROM custdetails"
	cur=db.engine.execute(stmt).fetchall()
	print(cur)
	ordered_images = sorted(image_names, key=lambda x: (int(re.sub('\D','',x)),x))
	print(ordered_images)
	print(combineData(ordered_images,cur))
	if(len(ordered_images)<1):
		return render_template('ads.html',image_names= None,length=0,ad1=None,cnt= None,ph=None)
	return render_template('ads.html',image_names=combineData(ordered_images,cur),length=len(cur),ad1=ordered_images[0],cnt=cur[0][0],ph=cur[0][1])

@app.route("/gmailSignIn/<Name>/<Email>",methods=["POST"])
def gmailSignIn(Name,Email):
	# if request.method == "POST":
	if(len(Login.query.filter_by(email=Email).all())==0):
		User = Login(email=Email,name=Name,password="",Mobile=None)
		db.session.add(User)
		db.session.commit()
		session['email'] = Email
		session[Email]=""
		session['logged_in'] = True
		session['Mobile'] = None
		print(session)
	else:
		session['email'] = Email
		session[Email]=""
		session['logged_in'] = True
		session['Mobile'] = None
	return redirect(url_for('displayAds'))

if __name__ == '__main__':
    app.run(host="localhost",port=8085,debug=True)

