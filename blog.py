from unittest import result
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from numpy import asscalar
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps



#-----user login required  decorater-----------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfaya gitmek için giriş yapmanız gerek","danger")
            return redirect(url_for("login"))
    return decorated_function



class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")


class RegisterFrom(Form):
    name = StringField("İsim Soyisim: ",validators=[validators.DataRequired(message="Lütfen doldurunuz"),validators.Length(min=2)])
    username = StringField("Kullanıcı Adı: ",validators=[validators.DataRequired(message="Lütfen doldurunuz"),validators.Length(min=3,max=25)])
    email = StringField("Email : ",validators=[validators.DataRequired(message="Lütfen doldurunuz"),validators.Length(min=2),validators.Email(message="Geçerli E-mail Girin")])
    password = PasswordField("Şifrenizi Girin: ",validators=[validators.DataRequired("Lütfen Doldurunuz"),validators.EqualTo(fieldname="confirm",message="Şifreler Eşleşmedi...")])
    confirm = PasswordField("Parola Doğrula")


app = Flask(__name__)
app.secret_key="blog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)



#-------------------Index--------------------
@app.route("/")
def index():
    return render_template("index.html")

#-------------------About--------------------
@app.route("/about")
def about():
    return render_template("about.html")

#-------------------Article_Details--------------------
@app.route("/article/<string:id>",methods = ["GET","POST"])
def article(id):
    comment = CommentForm()
    if request.method == "GET":
        sorgu = "Select * from articles where id = %s"
        
        cursor = mysql.connection.cursor()
        result = cursor.execute(sorgu,(id,))
        if result > 0:
            article = cursor.fetchone()
            return render_template("article.html",article = article,comment = comment)

        else:
            return render_template("article.html")
    else:
        sorgu = "Select * from articles where id = %s"
        
        cursor = mysql.connection.cursor()
        result = cursor.execute(sorgu,(id,))
        if result > 0:
            article = cursor.fetchone()
            return render_template("article.html",comment=comment,article = article)

        

    


#-------------------Register--------------------
@app.route("/register",methods = ["GET","POST"])
def register(): 
    form = RegisterFrom(request.form)
    
    if request.method == "POST" and form.validate():

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data) 
        
        cursor = mysql.connection.cursor()
        
        sorgu = "INSERT INTO users(name,username,email,password) VALUES(%s,%s,%s,%s)"
        
        cursor.execute(sorgu,(name,username,email,password))
        mysql.connection.commit()
        cursor.close()

        flash("Başarıyla Kayıt Olundu","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)


#-------------------Login--------------------
@app.route("/login", methods = ["GET","POST"])
def login():

    form = LoginForm(request.form)
    if request.method == "POST":
        username_entered = form.username.data
        password_entered = form.password.data

        sorgu = "Select * From users where username = %s"

        cursor = mysql.connection.cursor()

        result = cursor.execute(sorgu,(username_entered,))

        if result > 0:
            data = cursor.fetchone()
            real_username = data["password"]
            if sha256_crypt.verify(password_entered,real_username): 
                flash("Başarıyla Giriş Yaptınız","success")     

                session["logged_in"] = True
                session["username"] = username_entered

                return redirect(url_for("index")) 
            else:
                flash("Parola Yanlış...","danger")
                return redirect(url_for("login"))
        else:

            flash("Böyle bir kullanıcı yok","danger")
            return redirect(url_for("login"))
    else:
    
        return render_template("login.html", form = form)
    


#---------------------Logout------------------
@app.route("/logout")
def logout():

    session.clear()
    return redirect(url_for("index"))


#------------Dashboard-------------------
@app.route("/dashboard")
@login_required
def dashboard():
    
    sorgu = "Select * from articles where author = %s"

    cursor = mysql.connection.cursor()

    result = cursor.execute(sorgu,(session["username"],))
    
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")


#--------------ADDARTICLE-------------------
@app.route('/addarticle',methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():

        title = form.title.data
        content = form.content.data

        sorgu = "INSERT INTO articles(title,author,content)  VALUES(%s,%s,%s)"

        cursor = mysql.connection.cursor()
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()

        cursor.close()
        flash("Başarıyla Makaleniz Yüklendi","success")
        return redirect(url_for("dashboard"))
    else:

        return render_template("addarticle.html",form = form)

    

#------------Articles------------
@app.route("/articles")
def articles():
    
    sorgu = "Select * from articles"

    cursor = mysql.connection.cursor()

    result = cursor.execute(sorgu)
   

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:

        return render_template("articles.html")


#------------Article Delete-------------

@app.route("/delete/<string:id>")
@login_required
def article_delete(id):
    sorgu = "Select * from articles where author = %s and id = %s"
    
    cursor = mysql.connection.cursor()

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        flash("Başarıyla Silinmiştir","success")
        return redirect(url_for("dashboard"))
    else:
        flash("Makale Yok ya da Sizin Makaleniz Değil","danger")
        return redirect(url_for("index"))



#--------------Article Update-------------
@app.route('/edit/<string:id>',methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":

        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where author = %s and id = %s"
        result = cursor.execute(sorgu,(session["username"],id))
        
        if result > 0:
            data = cursor.fetchone()
            form = ArticleForm()
            form.title.data = data["title"]
            form.content.data = data["content"]
            return render_template("edit.html",form = form)
        else:
            flash("Böyle bir makale yok yada yetkiniz yok...","danger")
            return redirect(url_for("index"))
    else:
        form = ArticleForm(request.form)
        newtitle = form.title.data
        newcontent = form.content.data
        cursor = mysql.connection.cursor()
        sorgu2 = "Update articles Set title = %s ,content = %s where id = %s"

        cursor.execute(sorgu2,(newtitle,newcontent,id))
        mysql.connection.commit()

        flash("Başarıyla Düzenlendi","success")
        return redirect(url_for("dashboard"))
        
        
#search
@app.route('/search',methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keywords = request.form.get("keyword")

        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where title  like '%"+keywords+"%'"
        result = cursor.execute(sorgu)
        if result > 0:
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)
        else:
            flash("Böyle bir makale yok...","danger")
            return redirect(url_for("articles"))
        



@app.route('/profile/<string:id>',methods = ["GET","POST"])
@login_required
def profile(id):

    if request.method == "GET":
        profileform = ProfileForm()
        cursor = mysql.connection.cursor()
        
        sorgu = "Select * from users where username = %s and id = %s"

        result = cursor.execute(sorgu,(session["username"],id))

        if result > 0:
            users_data = cursor.fetchone()
            
            profileform.profile_name.data = users_data["name"]
            profileform.profile_email.data = users_data["email"]
            

            return render_template("profile.html",profileform = profileform)
        else:
            return render_template("profile.html",profileform = profileform)

    
    else:
        cursor = mysql.connection.cursor()
        profileform  = ProfileForm(request.form)

        sorgu = "Select * from users where id = %s"
        result = cursor.execute(sorgu,(id,))

        if result > 0:
            data = cursor.fetchone()
            password = data["password"]
            new_name = profileform.profile_name.data
            new_email = profileform.profile_email.data
            entered_password = profileform.profile_password.data

            if sha256_crypt.verify(entered_password,password):

                sorgu2 = "Update  users Set name = %s,email = %s where id = %s"
                cursor.execute(sorgu2,(new_name,new_email,id))
                mysql.connection.commit()

                flash("Profil Düzenleme Başarılı","success")
                return redirect(url_for("index"))  
            else:
                flash("Şifre Yanlış","danger")
                return render_template("profile.html",profileform = profileform)  

        else:
            flash("Hata","danger")
            return render_template("profile.html",profileform = profileform)
            


#------------------Makale Form------------------------

class ArticleForm(Form):

    title = StringField("Makale Başlığı",validators=[validators.Length(min=5,max=100,message="Fazla Karakter veyaz Az Karakter Girdiniz")])
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min=10,message="10'dan Az Karakter")])




#------------Yorum Form-------------
class CommentForm(Form):

    comment = TextAreaField("Yorum Yap",validators=[validators.Length(min=10,max=300,message="10 Karakterden Az ya da 300 Karakterden Fazla Girdiniz")])


#---------------Profile Form------------
class ProfileForm(Form):
    profile_name = StringField("İsim Soyisim",validators=[validators.Length(min=3,max=50,message="3 karakterden küçük yada 50 karakterden büyük")])
    profile_email = StringField("E-MAİL",validators=[validators.Email(message="Geçerli Email Gir.")])
    profile_password = PasswordField("Mevcut Şifre",validators=[validators.EqualTo(fieldname="confirm"),validators.DataRequired(message="Kayıt işlemi için şifre girmek zorundasınız")])
    confirm = PasswordField("Şifer Doğrula")

if __name__ == "__main__": 
    app.run(debug=True)