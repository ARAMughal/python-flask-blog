from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime
import json
from werkzeug import secure_filename
import os
import math
import smtplib
import pyodbc
import urllib.request, urllib.parse, urllib.error 

# from __future__ import print_function
# import httplib2
# import os

# from apiclient import discovery
# import oauth2client
# from oauth2client import client
# from oauth2client import tools

# import smtplib

# from email.mime.multipart import MIMEMultipart

# from email.mime.text import MIMEText





with open('config.json','r')as c:
    params = json.load(c)['params']

local_server = True
app = Flask(__name__)
app.secret_key = 'super-sectret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
))
mail = Mail(app)

if local_server:
    parameters = urllib.parse.quote_plus('DRIVER={SQL Server Native Client 11.0};SERVER=HAIER-PC;DATABASE=Python;Trusted_Connection=yes;')
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri'] % parameters
else:
    parameters = urllib.parse.quote_plus('DRIVER={SQL Server Native Client 11.0};SERVER=HAIER-PC;DATABASE=Python;Trusted_Connection=yes;')
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri'] % parameters

db = SQLAlchemy(app)


class Contact(db.Model):
    __tablename__ = "contact"
    srno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(60), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    msg = db.Column(db.String(50), nullable=False)



class Posts(db.Model):
    __tablename__ = "posts"
    srno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(60), nullable=False)
    postContent = db.Column(db.String(12), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    imgFile = db.Column(db.String(50), nullable=False)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    #[0:params['no_of_posts']]
    last = math.ceil(len(posts) / int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[((page-1) * int(params['no_of_posts'])):((page-1) * int(params['no_of_posts'])+int(params['no_of_posts']))]
    #start
    if (page == 1):
        prev = "#"
        next = "/?page="+str(page+1)
    #Last
    elif (page == last):
        next = "#"
        prev = "/?page="+str(page-1)
    #Middle
    else:
        prev = "/?page="+str(page-1)
        next = "/?page="+str(page+1)

    return render_template('index.html',params=params, posts=posts, prev=prev, next=next)


@app.route("/about")
def about():
    return render_template('about.html',params=params)



@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")


@app.route("/uploader",  methods=['GET', 'POST'])
def uploader():
    if('user' in session and session['user'] == params['admin_mail']):
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded successfully"

@app.route("/delete/<string:srno>", methods=['GET', 'POST'])
def delete(srno):
    if('user' in session and session['user'] == params['admin_mail']):
        post = Posts.query.filter_by(srno=srno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")

@app.route("/dashboard",  methods=['GET', 'POST'])
def dashboard():
    if('user' in session and session['user'] == params['admin_mail']):
        posts = Posts.query.all()
        return render_template('dashboard.html',params=params, posts=posts)

    elif request.method == 'POST':
        userMail = request.form.get('email')
        userpass = request.form.get('pass')
        
        if ((userMail == params['admin_mail']) and (userpass == params['admin_password'])):
            session['user'] = userMail
            posts = Posts.query.all()
            return render_template('dashboard.html',params=params, posts=posts)
    return render_template('login.html',params=params)
@app.route("/edit/<string:srno>", methods=['GET', 'POST'])
def edit(srno):
    if('user' in session and session['user'] == params['admin_mail']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('postContent')
            imgFile = request.form.get('imgFile')
            date = datetime.now()
            if srno =='0':
                post = Posts(title=box_title,slug=slug,postContent=content,imgFile=imgFile,date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(srno=srno).first()
                post.title = box_title
                post.slug = slug
                post.postContent = content
                post.imgFile = imgFile
                post.date = date
                db.session.commit()
                return redirect('/edit/'+srno)
        post = Posts.query.filter_by(srno=srno).first()
        return render_template('edit.html',params=params,post=post,srno=srno)





@app.route("/post/<string:post_slug>", methods=['GET'])
def blogPosts(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=post)


@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if (request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contact(name=name,email=email,phone=phone,msg=message,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message("New Message from"+name,
         sender=email, recipients=[params['gmail-user']],
         body = message +"\n"+ phone
         )
    return render_template('contact.html',params=params)

app.run(debug=True)

