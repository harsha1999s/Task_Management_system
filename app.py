from flask import Flask,request,render_template,redirect,url_for,flash,session,send_file
from flask_mysqldb import MySQL
from flask_session import Session
from cemail import sendmail
from remail import rsendmail
from otp import genotp
import random
import MySQLdb.cursors
import re
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from admintokenreset import token
from emptokenreset import token
from io import BytesIO


app=Flask (__name__)
app.secret_key ='234567uihgdx'

app.config['SESSION_TYPE']='filesystem'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='harsha@19s'
app.config['MYSQL_DB']='task'

Session(app)
mysql=MySQL(app)

@app.route('/')
@app.route('/home')
def index():
    return render_template('index.html')

# admin registration
@app.route('/adminregistration',methods=['GET','POST'])
def adminregister():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form :
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admin WHERE email = % s', (email, ))
        admin = cursor.fetchone()
        if admin:
            flash('Account already exists !')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address !')
        
        elif not username or not password or not email:
            flash('Please fill out the form !')
        else:
            
            # Send OTP to user's email
            otp = genotp()
            subject='Thanks for registering to Work Space'
            body=f'Use this otp to register {otp}'
            rsendmail(email,subject,body)
            mysql.connection.commit()
            cursor.close()
            flash('otp has sent to your mail!')
            return render_template('otp.html',otp=otp,username=username,email=email,password=password)
            
           
 
            '''
            cursor.execute('INSERT INTO admin VALUES ( % s, % s, % s)', (username, email, password))
            mysql.connection.commit()
            flash('You have successfully registered !')
            return redirect(url_for('adminlogin'))
            '''
            
    return render_template('adminregistration.html')

#admin registration of otp
@app.route('/otp/<otp>/<username>/<email>/<password>',methods=['GET','POST'])
def otp(otp,username,email,password):
    if request.method == 'POST':
        uotp = request.form['otp']
        if otp == uotp:
            cursor = mysql.connection.cursor()
            lst=[username,email,password]
            query='insert into admin values (%s,%s,%s)'
            cursor.execute(query,lst)
            mysql.connection.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('adminlogin'))
        else:
            flash('Wrong OTP')
            return render_template('otp.html',otp=otp,username=username,email=email,password=password)
    



# admin login
@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():

    if session.get('user'):
        return redirect(url_for('admindashboard')) #admin dashboard
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from admin where email=%s and password=%s',[email,password])
        count=cursor.fetchone()[0]
        if count==0:
           
            flash('Invalid mail or password')
            return render_template('adminlogin.html')
        
        else:
            session['user']=email
            return redirect(url_for('admindashboard')) #admin dashboard
            
    return render_template('adminlogin.html')

#employee registration
@app.route('/empregistration',methods=['GET','POST'])
def empregistration():
     if session.get('user'):
        if request.method == 'POST':
            ename = request.form['ename']
            empdept = request.form['empdept']
            empemail = request.form['empemail']
            emppassword = request.form['emppassword']
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT count(*) FROM emp WHERE empemail=%s',[empemail])
            count= cursor.fetchone()[0]
            #print(count)
            if count!=0:
                return "mail already exists!"
            else:
                cursor.execute('INSERT INTO emp VALUES ( %s,%s,%s,%s,%s)', (ename,empdept,empemail,emppassword,session.get('user')))
                mysql.connection.commit()
                cursor.close()
                
                flash('You have successfully registered !')
                
                subject='Work Space Employee Credintials'
                body=f' Thanks for registering to Work Space please use this credintials to login mail:{empemail} and password:{emppassword}'
                rsendmail(empemail,subject,body)
                
                
                return redirect(url_for('admindashboard'))
        return render_template('empregistration.html')
     else:
        return render_template('empregistration.html')

#employee login
@app.route('/emplogin',methods=['GET','POST'])
def emplogin():
    
    if session.get('empuser'):
        return redirect(url_for('userdashboard')) #admin dashboard
     
    if request.method=='POST':
        empemail=request.form['empemail']
        emppassword=request.form['emppassword']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from emp where empemail=%s and emppassword=%s',[empemail,emppassword])
        count=cursor.fetchone()[0]
        if count==0:
           
            flash('Invalid id or password')
            return render_template('emplogin.html')
        
        else:
            session['empuser']=empemail
            return redirect(url_for('userdashboard')) #admin dashboard
            
    return render_template('emplogin.html')


# forgot page in login for admin
@app.route('/adminforgot',methods=['GET','POST'])
def adminforgot():
    if request.method=='POST':
        email=request.form['email']
        cursor=mysql.connection.cursor()
        cursor.execute('select email from admin')
        edata=cursor.fetchall()
        
        print(edata)
        if (email,) in edata:
            cursor.execute('select %s from admin',[email])
            deta=cursor.fetchone()[0]
            print(deta)
            cursor.close()
            subject=f'Reset Password for {deta}'
            body=f'Reset the passwword using {url_for("admincreatepassword",token=token(email,320),_external=True)}'
            rsendmail(deta,subject,body)
            flash('Reset link sent to your mail')
            
        else:
            flash( 'Invalid email')
    return render_template('forgot.html')

        
# after clicking on the link,for new password creation for admin
@app.route('/admincreatepassword/<token>',methods=['GET','POST'])

def admincreatepassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        email=s.loads(token)['user']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mysql.connection.cursor()
                cursor.execute('update admin set password=%s where email=%s',[npass,email])
                mysql.connection.commit()
                flash('Password reset Successfully')
                return redirect(url_for('adminlogin'))
            else:
                flash('Password mismatch')
        return render_template('newpassword.html')
    except:
        return 'Link expired try again'


# forgot page in login for emp
@app.route('/empforgot',methods=['GET','POST'])
def empforgot():
    if request.method=='POST':
        empemail=request.form['email']
        cursor=mysql.connection.cursor()
        cursor.execute('select empemail from emp')
        edata=cursor.fetchall()
        
        print(edata)
        if (empemail,) in edata:
            cursor.execute('select %s from emp',[empemail])
            deta=cursor.fetchone()[0]
            print(deta)
            cursor.close()
            subject=f'Reset Password for {deta}'
            body=f'Reset the passwword using {url_for("empcreatepassword",token=token(empemail,320),_external=True)}'
            rsendmail(deta,subject,body)
            flash('Reset link sent to your mail')
            
        else:
            flash( 'Invalid email')
    return render_template('forgot.html')


# after clicking on the link,for new password creation for emp
@app.route('/empcreatepassword/<token>',methods=['GET','POST'])
def empcreatepassword(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        empemail=s.loads(token)['empuser']
        if request.method=='POST':
            npass=request.form['npassword']
            cpass=request.form['cpassword']
            if npass==cpass:
                cursor=mysql.connection.cursor()
                cursor.execute('update emp set emppassword=%s where empemail=%s',[npass,empemail])
                mysql.connection.commit()
                flash('Password reset Successfully')
                return redirect(url_for('emplogin'))
            else:
                flash('Password mismatch')
        return render_template('newpassword.html')
    except:
        return 'Link expired try again'    
  

#admin addtask
@app.route('/addtask',methods =['GET','POST'])
def addtask():
    if session.get('user'):
        email = session.get('user')
        cursor = mysql.connection.cursor()
        cursor.execute('select * from emp where addedby=%s',[session.get('user')])
        adddata = cursor.fetchall()
        print(adddata)
            
        if request.method == 'POST':
        
            taskid = request.form['taskid']
            tasktitle = request.form['tasktitle']
            duedate = request.form['duedate']
            taskcontent = request.form['taskcontent']
            empemail = request.form['empemail']
                    
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT count(*) FROM task WHERE taskid=%s',[taskid])
            count= cursor.fetchone()[0]
            #print(count)
            if count!=0:
                return "task id already exists!"
            else:
                cursor.execute('insert into task (taskid,tasktitle,duedate,taskcontent,empemail,assignedby)values(%s,%s,%s,%s,%s,%s)',[taskid,tasktitle,duedate,taskcontent,empemail,email])
                mysql.connection.commit() 
                flash(f'{taskid} added successfully ',)

                subject='New Task from Work Space'
                body=f'This is the information about the task, task title:"{tasktitle}", duedate:"{duedate}",about the task:"{taskcontent}". '
                rsendmail(empemail,subject,body)

                
                
            return redirect(url_for('admindashboard'))#adminhome
        else:
            return render_template('addtask.html',adddata=adddata)
    return redirect(url_for('adminlogin'))
        




#delete task
@app.route('/deletenotes/<taskid>')
def deletenotes(taskid):
    cursor = mysql.connection.cursor()
    #cursor.execute('select  title from notes',[title])
    cursor.execute('delete from notes where taskid = %s',[taskid])
    mysql.connection.commit()
    cursor.close()
    flash('Task is deleted')
    return redirect(url_for('admindashboard'))


#task update
@app.route('/updatetask/<taskid>', methods=['GET','POST'])
def updatetask(taskid):
    if session.get('user'):
        cursor = mysql.connection.cursor()
        cursor.execute('select tasktitle,duedate,taskcontent from task where taskid = %s',[taskid])
        updata = cursor.fetchone()
        cursor.execute('select empemail from task where taskid=%s',[taskid])
        data=cursor.fetchone()[0]
        cursor.close()

        
        if request.method == 'POST':
            tasktitle = request.form['tasktitle']
            duedate = request.form['duedate']
            taskcontent = request.form['taskcontent']
            
            cursor = mysql.connection.cursor()
            cursor.execute('update task set tasktitle = %s, duedate = %s, taskcontent = %s where taskid = %s',[tasktitle,duedate,taskcontent,taskid])
            mysql.connection.commit()
            cursor.close()

            
            subject='Updated Task from Work Space'
            body=f'This is the information about the updated task, task title:"{tasktitle}", duedate:"{duedate}",about the task:"{taskcontent}". '
            rsendmail(data,subject,body)

            
            flash('task updated successfully')
            return redirect(url_for('admindashboard'))
        
        return render_template('updatetask.html',updata = updata)
    else:
        return redirect (url_for('adminlogin'))


#admin logout
@app.route('/logoutadmin')
def logoutadmin():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('index'))
    else:
        flash('Logged out ')
        return redirect(url_for('adminlogin'))

@app.route('/deletetask/<taskid>')
def deletetask(taskid):
    cursor = mysql.connection.cursor()
    #cursor.execute('select  title from notes',[title])
    cursor.execute('delete from task where taskid = %s',[taskid])
    mysql.connection.commit()
    cursor.close()
    flash('Notes is deleted')
    return redirect(url_for('admindashboard'))

#redirecting to admin home page    
@app.route('/admindashboard')
def admindashboard():
    if session.get('user'):
        email = session.get('user')
        cursor = mysql.connection.cursor()
        cursor.execute('select * from task where assignedby = %s', [email])
        data = cursor.fetchall()
        print(data)
        cursor.close()
        return render_template('adminstatus.html', data = data)
    else:
        return redirect( url_for('adminlogin'))

#user logout
@app.route('/logoutuser')
def logoutuser():
    if session.get('empuser'):
        session.pop('empuser')
        return redirect(url_for('index'))
    else:
        flash('Logged out ')
        return redirect(url_for('emplogin'))
    


#redirecting to user home page    
@app.route('/userdashboard')
def userdashboard():
    if session.get('empuser'):
        email = session.get('empuser')
        cursor = mysql.connection.cursor()
        cursor.execute('select * from task where empemail = %s', [email])
        data = cursor.fetchall()
        print(data)
        cursor.close()
        return render_template('userstatus.html', data = data)
    else:
        return redirect( url_for('emplogin'))
    
#status button route
@app.route('/statusbutton/<taskid>',methods=['POST'])
def statusbutton(taskid):
    status = request.form['status']
    cursor = mysql.connection.cursor()
    cursor.execute('update task set status = %s where taskid= %s',[status,taskid])
        
    dstatus = cursor.fetchone()
    print(dstatus)
    mysql.connection.commit()
    cursor.close()
    return redirect( url_for('userdashboard'))


@app.route('/errorring')
def errorring():
    return render_template('errorimg.html')        

app.run(use_reloader =True,debug=True)