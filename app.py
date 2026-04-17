from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.contrib.google import google  # Flask UI proxy
from oauthlib.oauth2 import TokenExpiredError
from flask_cors import CORS
import mysql.connector
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask import request, jsonify
# from flask_wtf.csrf import CSRFProtect
import os
import pyotp
import time
from werkzeug.middleware.proxy_fix import ProxyFix
load_dotenv()  
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = os.getenv('OIT', '1')
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Read frontend URL from env — defaults to localhost for dev
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
FLASK_ENV = os.getenv('FLASK_ENV', 'development')

CORS(app, supports_credentials=True, origins=[FRONTEND_URL])

# Production: Secure cookies over real HTTPS (needed for cross-origin React)
# Development: Default cookies over plain HTTP (so v1 Flask/Jinja OAuth works)
if FLASK_ENV == 'production':
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
# csrf = CSRFProtect(app)
# Blueprint for Flask UI (localhost:5000)
google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ],
    redirect_to="google_login",
    reprompt_consent=True
)
google_bp.name = "google"
app.register_blueprint(google_bp, url_prefix="/login")

# Blueprint for React (localhost:5173)
google_react_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
    redirect_to="react_google_login",
)
google_react_bp.name = "google_react"
app.register_blueprint(google_react_bp, url_prefix="/react-login")
app.secret_key = os.getenv('APP_SECRET','supersecret')

app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_PORT"] = os.getenv('MAILPORT')
app.config["MAIL_USERNAME"] = os.getenv('EMAIL')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PWD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USERNAME'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_DBNAME'),
        buffered=True
    )


def get_current_user_id():
   """Return current user's user_id (cached in session) or look it up.

   This avoids ambiguous lookups when there are duplicate emails/usernames.
   Stores user_id in session for future requests.
   """
   if 'user_id' in session:
      return session['user_id']

   conn = get_db_connection()
   cursor = conn.cursor()
   try:
      if 'email' in session and session['email']:
         cursor.execute("SELECT user_id FROM customerdetails WHERE email=%s LIMIT 1", (session['email'],))
      elif 'username' in session and session['username']:
         cursor.execute("SELECT user_id FROM customerdetails WHERE username=%s LIMIT 1", (session['username'],))
      else:
         return None
      row = cursor.fetchone()
      if row:
         session['user_id'] = row[0]
         return row[0]
      return None
   finally:
      cursor.close()
      conn.close()


def generate_otp_secret():
    return pyotp.random_base32()

def send_otp(email, otp):
    msg = Message("Your OTP Code", sender=os.getenv('EMAIL'), recipients=[email])
    msg.body = f"Your OTP code is: {otp}. It is valid for 5 minutes."

    try:
        mail.send(msg)
        return True
    except Exception as e:
        print("Error sending OTP:", e)
        return False

@app.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html')

from flask import redirect, url_for, session, request, flash
from oauthlib.oauth2 import TokenExpiredError
import time

def _handle_google_user(email, username):
    """Upsert Google user into DB and set session."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM customerdetails WHERE email=%s ORDER BY user_id LIMIT 1", (email,))
        user = cursor.fetchone()

        if user:
            if user['username'] != username:
                cursor.execute("SELECT user_id FROM customerdetails WHERE username=%s AND user_id != %s", (username, user['user_id']))
                if not cursor.fetchone():
                    cursor.execute("UPDATE customerdetails SET username=%s WHERE user_id=%s", (username, user['user_id']))
                    conn.commit()
                else:
                    username = user['username']
        else:
            cursor.execute("SELECT user_id FROM customerdetails WHERE username=%s", (username,))
            if cursor.fetchone():
                base = username
                username = f"{base}_{email.split('@')[0]}"
                cursor.execute("SELECT user_id FROM customerdetails WHERE username=%s", (username,))
                if cursor.fetchone():
                    username = f"{base}_{int(time.time())}"
            cursor.execute("INSERT INTO customerdetails (username, email, password) VALUES (%s, %s, %s)", (username, email, None))
            conn.commit()
            cursor.execute("SELECT * FROM customerdetails WHERE email=%s ORDER BY user_id LIMIT 1", (email,))
            user = cursor.fetchone()

        session.clear()
        session['username'] = user['username']
        session['email'] = user['email']
        session['user_id'] = user.get('user_id')
        session['user_status'] = "logged_in"
    finally:
        cursor.close()
        conn.close()


@app.route("/google-login")
def google_login():
    bp = app.blueprints.get("google")
    
    if not bp or not bp.session.token:
        return redirect(url_for("google.login"))

    resp = bp.session.get("/oauth2/v2/userinfo")
    if not resp or not resp.ok:
        flash("Failed to fetch user info from Google.", "danger")
        return redirect(url_for("login"))

    user_info = resp.json()
    email = user_info["email"]
    username = user_info.get("name", email.split("@")[0])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # fetch as dict

    try:
        # Check if user exists by email - use LIMIT 1 to get the first match
        # If there are duplicates, we'll use the first one (oldest user_id)
        cursor.execute("SELECT * FROM customerdetails WHERE email=%s ORDER BY user_id LIMIT 1", (email,))
        user = cursor.fetchone()

        if user:
            # User exists - link Google OAuth to existing account
            # Update username if it's different (Google might have a better name)
            # But first check if the new username is available
            if user['username'] != username:
                cursor.execute("SELECT user_id FROM customerdetails WHERE username=%s AND user_id != %s", 
                             (username, user['user_id']))
                username_taken = cursor.fetchone()
                
                if not username_taken:
                    # Username is available, update it
                    cursor.execute("UPDATE customerdetails SET username=%s WHERE user_id=%s", 
                                 (username, user['user_id']))
                    conn.commit()
                else:
                    # Username is taken, keep the existing username
                    username = user['username']
            
            flash(f"Welcome back! Linked your Google account to existing profile.", "success")
        else:
            # User doesn't exist - check if username is available before creating
            cursor.execute("SELECT user_id FROM customerdetails WHERE username=%s", (username,))
            username_taken = cursor.fetchone()
            
            if username_taken:
                # Username is taken, append email prefix to make it unique
                original_username = username
                username = f"{original_username}_{email.split('@')[0]}"
                
                # Double-check the new username is available
                cursor.execute("SELECT user_id FROM customerdetails WHERE username=%s", (username,))
                if cursor.fetchone():
                    # If still taken, append timestamp
                    username = f"{original_username}_{int(time.time())}"
            
            # Create new account
            cursor.execute(
                "INSERT INTO customerdetails (username, email, password) VALUES (%s, %s, %s)",
                (username, email, None)
            )
            conn.commit()
            
            # Get the newly created user
            cursor.execute("SELECT * FROM customerdetails WHERE email=%s ORDER BY user_id LIMIT 1", (email,))
            user = cursor.fetchone()
            
            if username_taken:
                flash(f"Account created! Username adjusted to '{username}' as '{original_username}' was taken.", "info")
            else:
                flash(f"Account created and logged in via Google!", "success")

        # Set session data
        session['username'] = user['username']
        session['email'] = user['email']
        session['user_id'] = user.get('user_id')
        session['user_status'] = "logged_in"

    except Exception as e:
        flash(f"Error during Google login: {str(e)}", "danger")
        return redirect(url_for("login"))
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("index"))




@app.route("/react-google-login")
def react_google_login():
    bp = app.blueprints.get("google_react")
    if not bp or not bp.session.token:
        return redirect(url_for("google_react.login"))
    try:
        resp = bp.session.get("/oauth2/v2/userinfo")
    except TokenExpiredError:
        session.pop("google_react_oauth_token", None)
        return redirect(url_for("google_react.login"))

    if not resp or not resp.ok:
        return redirect(url_for("google_react.login"))

    user_info = resp.json()
    email = user_info["email"]
    username = user_info.get("name", email.split("@")[0])
    _handle_google_user(email, username)
    return redirect(f"{FRONTEND_URL}/auth/callback")

@app.route('/Registration', methods=['GET', 'POST'])
def Registration():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Basic validation
        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template('Registration.html')
        
        # Check if username already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT user_id FROM customerdetails WHERE username=%s", (username,))
            if cursor.fetchone():
                flash("Username already taken. Please choose a different username.", "warning")
                return render_template('Registration.html')
            
            # Check if email already exists
            cursor.execute("SELECT user_id FROM customerdetails WHERE email=%s", (email,))
            if cursor.fetchone():
                flash("An account with this email already exists. Please login instead.", "warning")
                return render_template('Registration.html')
        finally:
            cursor.close()
            conn.close()
        
        # Store in session for OTP verification
        session['username'] = username
        session['password'] = generate_password_hash(password)
        session['email'] = email

        otp_secret = generate_otp_secret()
        session['otp_secret'] = otp_secret

        totp = pyotp.TOTP(otp_secret)
        timestamp = int(time.time())
        otp = totp.at(timestamp)
        session['otp_timestamp'] = timestamp

        if send_otp(session['email'], otp):
            flash("OTP sent to your email. Please verify within 5 minutes.", "info")
            return redirect(url_for('verify_otp'))
        else:
            flash("Failed to send OTP. Try again.", "danger")
            return redirect(url_for('Registration'))

    return render_template('Registration.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
   if request.method == 'POST':
      entered_otp = (request.form.get('otp') or '').strip()

      # basic session checks
      if 'otp_secret' not in session or 'otp_timestamp' not in session:
         flash("OTP session expired. Register again.", "danger")
         return redirect(url_for('Registration'))

      # expiry check
      if int(time.time()) - session['otp_timestamp'] > 300:
         flash("OTP expired. Register again.", "danger")
         return redirect(url_for('Registration'))

      totp = pyotp.TOTP(session['otp_secret'])
      otp_timestamp = session['otp_timestamp']
      time_window = 30

      valid = False
      for offset in (-1, 0, 1):
         test_time = otp_timestamp + (offset * time_window)
         expected_otp = totp.at(test_time)
         if entered_otp == expected_otp:
            valid = True
            break

      if not valid:
         flash("Invalid OTP. Try again.", "danger")
         return render_template('verify_otp.html')

      # OTP valid -> create user and send welcome email
      session["user_status"] = "Registered"
      conn = get_db_connection()
      cursor = conn.cursor()
      try:
         # Check if email already exists before creating account
         cursor.execute("SELECT user_id FROM customerdetails WHERE email=%s", (session.get('email'),))
         existing_email = cursor.fetchone()
         
         if existing_email:
            flash("An account with this email already exists. Please login instead.", "warning")
            return redirect(url_for('login'))

         # Check if username already exists before creating account
         cursor.execute("SELECT user_id FROM customerdetails WHERE username=%s", (session.get('username'),))
         existing_username = cursor.fetchone()
         
         if existing_username:
            flash("Username already taken. Please choose a different username.", "warning")
            return redirect(url_for('Registration'))

         # send welcome email (best-effort)
         try:
            msg = Message("Welcome to Perfect Perfume!", sender=os.getenv('EMAIL'), recipients=[session.get("email")])
            msg.body = f"""
Dear {session.get('username')},

We're thrilled to have you as part of our fragrance family. Explore our exquisite collection of perfumes crafted to enchant your senses. Whether you're seeking a signature scent or a gift for someone special, we have something perfect for you!

✨ Enjoy exclusive discounts and special offers as a valued member.  
🚚 Free delivery on your first order!  

Feel free to reach out if you have any questions or need assistance. Happy exploring!

Best wishes,  
Perfect Perfume Team
"""
            mail.send(msg)
         except Exception:
            # don't block registration if email fails
            pass

         cursor.execute("INSERT INTO customerdetails (username, password, email) VALUES (%s, %s, %s)",
                     (session.get('username'), session.get('password'), session.get('email')))
         conn.commit()

         # cache the inserted user's id
         cursor.execute("SELECT user_id FROM customerdetails WHERE email=%s LIMIT 1", (session.get('email'),))
         row = cursor.fetchone()
         if row:
            session['user_id'] = row[0]
      finally:
         cursor.close()
         conn.close()

      session.pop('otp_secret', None)
      session.pop('otp_timestamp', None)

      flash("OTP Verified! Registration successful.", "success")
      return redirect(url_for('index'))

   return render_template('verify_otp.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
   if request.method == 'POST':
      username = request.form.get('username')
      password = request.form.get('password')

      conn = get_db_connection()
      # use dictionary cursor so columns are clearer
      cursor = conn.cursor(dictionary=True)

      # try to find user by email (if present in session) or by username
      if 'email' in session:
         cursor.execute("SELECT * FROM customerdetails WHERE email=%s", (session['email'],))
      else:
         cursor.execute("SELECT * FROM customerdetails WHERE username=%s", (username,))

      user = cursor.fetchone()

      if user and user.get('password') and check_password_hash(user.get('password'), password):
         # successful login
         session['username'] = user.get('username')
         session['email'] = user.get('email')
         session['user_id'] = user.get('user_id')
         session["user_status"] = "logged_in"
         cursor.close()
         conn.close()
         flash("Login successful!", "success")
         return redirect(url_for('index'))
      else:
         # close resources before returning
         cursor.close()
         conn.close()
         flash("Invalid username or password.", "danger")

   return render_template('login.html')
@app.route('/view_cart', methods=['GET'])
def view_cart():
    if 'user_status' in session and session['user_status'] in ["Registered", "logged_in"]:
        user_id = get_current_user_id()
        if user_id:
            conn = get_db_connection()   # <-- create connection
            cursor = conn.cursor()       # <-- create cursor

            cursor.execute("""
                SELECT p.product_id, p.product_name, p.target_gender, p.item_form, p.Ingredients, 
                       p.special_features, p.item_volume, p.country, c.quantity, 
                       (p.price * c.quantity) as price
                FROM cart c
                JOIN product p ON p.product_id = c.product_id
                WHERE c.user_id = %s
                ORDER BY c.added_time DESC
            """, (user_id,))
            
            cart_items = cursor.fetchall()

            total_price_cart = sum(item[9] for item in cart_items)  # sum price column (now index 9)

            cursor.close()
            conn.close()

            return render_template('cart.html', cart_items=cart_items, grand_total=total_price_cart)

    return redirect(url_for('login'))


@app.route('/myprofile',methods=['POST','GET'])
def myprofile():
   if 'user_status' in session and (session['user_status'] == 'Registered' or session['user_status'] == 'logged_in'):
      username = session.get('username')
      conn = get_db_connection()
      # use dictionary cursor so we can access columns by name in template
      cursor = conn.cursor(dictionary=True)
      try:
         if 'email' in session and session['email']:
            cursor.execute("SELECT username, email FROM customerdetails WHERE email=%s", (session['email'],))
         else:
            cursor.execute("SELECT username, email FROM customerdetails WHERE username=%s", (username,))
         user_details = cursor.fetchone()
      finally:
         cursor.close()
         conn.close()

      if user_details:
         return render_template('myprofile.html', user=user_details)
      else:
         return "user not found",400
   else:
      return redirect(url_for('login'))
      

@app.route('/Floral',methods=['POST','GET'])
def Floral():
   return render_template('Floral.html')

@app.route('/Woody',methods=['POST','GET'])
def Woody():
   return render_template('Woody.html')

@app.route('/Citrus',methods=['POST','GET'])
def Citrus():
   return render_template('Citrus.html')

@app.route('/Oriental',methods=['POST','GET'])
def Oriental():
   return render_template('Oriental.html')

@app.route('/Fresh_Aquatic',methods=['POST','GET'])
def Fresh_Aquatic():
   return render_template('Fresh_Aquatic.html')

@app.route('/Gourmand',methods=['POST','GET'])
def Gourmand():
   return render_template('Gourmand.html')

@app.route('/home',methods=['POST','GET'])
def home():
   return redirect(url_for('index'))

@app.route('/add_to_cart/<int:product_id>',methods=['GET','POST'])
def add_to_cart(product_id):
   if 'user_status' in session and (session['user_status']=="Registered" or session['user_status']=="logged_in"):
      username = session.get('username')
      conn = get_db_connection()
      cursor = conn.cursor()
      user_id = get_current_user_id()
      if user_id:
         quantity = int(request.form.get('quantity',1))
         cursor.execute("SELECT quantity from cart where user_id = %s and product_id = %s",(user_id,product_id))
         product_exists = cursor.fetchone()
         if product_exists:
            new_quantity = product_exists[0] + quantity
            cursor.execute("UPDATE cart SET quantity = %s where user_id = %s and product_id = %s",(new_quantity,user_id,product_id))
         else:
            cursor.execute("INSERT INTO cart(user_id,product_id,quantity) values(%s,%s,%s)",(user_id,product_id,quantity))
         conn.commit()
         cursor.close()
         conn.close()
      return redirect(url_for('view_cart'))
   else:
      return redirect(url_for('login'))

@app.route('/Buy_now/<int:product_id>',methods=['POST','GET'])
def Buy_now(product_id):
   if 'user_status' in session and (session['user_status']=="Registered" or session['user_status']=="logged_in"):
      username = session.get('username')
      conn = get_db_connection()
      cursor = conn.cursor()
      try:
         user_id = get_current_user_id()
         if user_id:
            if request.method == "POST":
               plot_no = request.form.get('plotno')
               street_address = request.form.get('street')
               area = request.form.get('areaname')
               state = request.form.get('state')
               pincode = request.form.get('pincode')
               country = request.form.get('country')
               quantity = request.form.get('quantity')
               if not plot_no or not street_address or not area or not country or not pincode or not state:
                  return "All fields are required!",400
               address = f"{plot_no},{street_address},{area},{state},{pincode},{country}"
               cursor.execute("""INSERT INTO address(user_id,plot_no,street_address,area,country,state,pincode) 
                              values(%s,%s,%s,%s,%s,%s,%s) 
                              on duplicate key update 
                              plot_no = values(plot_no),
                              street_address=values(street_address),
                              area=values(area),
                              country=values(country),
                              state = values(state),
                              pincode = values(pincode)""",
                              (user_id,plot_no,street_address,area,country,state,pincode)
                           )
               cursor.execute("INSERT INTO orders(user_id,product_id,address,quantity) values(%s,%s,%s,%s)",(user_id,product_id,address,quantity))
               conn.commit()
               # determine user's email
               if 'email' in session and session['email']:
                  user_email = session['email']
               else:
                  cursor.execute("SELECT email FROM customerdetails WHERE username=%s", (username,))
                  row = cursor.fetchone()
                  user_email = row[0] if row else None
               if user_email:
                  msg = Message("Order placed Successfully - Perfect Perfume", sender=os.getenv('EMAIL'), recipients=[user_email])
                  msg.body = f"Dear {username},\nYou will receive your order in two to three days... \n\nRegards,\nPerfect-Perfume"
                  mail.send(msg)
               return redirect(url_for('confirmation',product_id=product_id,quantity=quantity))
         return render_template('Buy_now.html',product_id=product_id)
      finally:
         cursor.close()
         conn.close()
   else:
      return redirect(url_for('login'))

@app.route('/Buy_cart',methods=['POST','GET'])
def Buy_cart():
   if 'user_status' in session and (session['user_status'] == "Registered" or session['user_status'] == "logged_in"):
      username = session.get('username')
      conn = get_db_connection()
      cursor = conn.cursor()
      try:
         user_id = get_current_user_id()
         if user_id:
            if request.method == "POST":
               plot_no = request.form.get('plotno')
               street_address = request.form.get('street')
               area = request.form.get('areaname')
               state = request.form.get('state')
               pincode = request.form.get('pincode')
               country = request.form.get('country')
               if not plot_no or not street_address or not area or not state or not pincode or not country:
                  return "All fields are required!",400
               # insert/update address and create orders for cart items
               address(plot_no,street_address,area,state,pincode,country)

               # fetch email (or use session email if available)
               if 'email' in session and session['email']:
                  user_email = session['email']
               else:
                  cursor.execute("SELECT email FROM customerdetails WHERE username=%s", (username,))
                  row = cursor.fetchone()
                  user_email = row[0] if row else None
               if user_email:
                  msg = Message("Order placed Successfully - Perfect Perfume", sender=os.getenv('EMAIL'), recipients=[user_email])
                  msg.body = f"Dear {username},\nYou will receive your order in two to three days... \n\nRegards,\nPerfect-Perfume"
                  mail.send(msg)
               return redirect(url_for('confirmation_cart'))
            return render_template('Buy_cart.html') 
      finally:
         cursor.close()
         conn.close()
   else:
      return redirect(url_for('login'))

def address(plot_no,street_address,area,state,pincode,country):
   if 'user_status' in session and (session['user_status'] == "Registered" or session['user_status'] == "logged_in"):
      username = session.get('username')
      conn = get_db_connection()
      cursor = conn.cursor()
      try:
         user_id = get_current_user_id()
         if user_id:
            cursor.execute("""INSERT INTO address(user_id,plot_no,street_address,area,country,state,pincode) 
                                 values(%s,%s,%s,%s,%s,%s,%s) 
                                 on duplicate key update 
                                 plot_no = values(plot_no),
                                 street_address=values(street_address),
                                 area=values(area),
                                 country=values(country),
                                 state = values(state),
                                 pincode = values(pincode)""",
                                 (user_id,plot_no,street_address,area,country,state,pincode)
                              )
            address = f"{plot_no},{street_address},{area},{state},{pincode},{country}"
            cursor.execute("SELECT * from cart where user_id = %s",(user_id,))
            cart_items = cursor.fetchall()
            for item in cart_items:
               product_id = item[2]
               quantity = item[3]
               cursor.execute("INSERT INTO orders(user_id,product_id,quantity,address) VALUES(%s,%s,%s,%s)",(user_id,product_id,quantity,address))
            conn.commit()

      finally:
         cursor.close()
         conn.close()

@app.route('/confirmation_cart',methods=['POST','GET'])
def confirmation_cart():
   if 'user_status' in session and (session['user_status'] == "Registered" or session['user_status'] == "logged_in"):
      username = session.get('username')
      conn = get_db_connection()
      cursor = conn.cursor()
      user_id = get_current_user_id()
      if user_id:
         cursor.execute("""SELECT p.product_name,p.Ingredients,p.price,c.quantity
                              FROM cart c
                              JOIN product p ON  p.product_id = c.product_id
                              where c.user_id = %s""",(user_id,))
         cart_items = cursor.fetchall()
         grand_total = sum(item[2]*item[3] for item in cart_items)
         cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
         conn.commit()
         cursor.execute("SELECT plot_no,street_address,area,country,state,pincode from address where user_id = %s",(user_id,))
         address_details = cursor.fetchone()
         if address_details:
            address = f"{address_details[0]},{address_details[1]},{address_details[2]},{address_details[3]},{address_details[4]},{address_details[5]}"
         return render_template('confirmation_cart.html',cart_items=cart_items,address=address,grand_total=grand_total)
      cursor.close()
      conn.close()
      if not user_id:
         return "user not found",400
   else:
      return redirect(url_for('login'))
               
@app.route('/confirmation/<int:product_id>/<int:quantity>',methods=['GET'])
def confirmation(product_id,quantity):
   if 'user_status' in session and (session['user_status']=="Registered" or session['user_status']=="logged_in"):
      username = session.get('username')
      conn = get_db_connection()
      cursor = conn.cursor()
      try:
         cursor.execute("SELECT product_name,Ingredients,price from product where product_id = %s", (product_id,))
         product_details = cursor.fetchone()
         if product_details:
            product_name, Ingredients, price = product_details
            cursor.execute("""SELECT address.plot_no, address.street_address, address.area, address.state, address.country, address.pincode 
                            FROM address
                            JOIN customerdetails ON address.user_id = customerdetails.user_id
                            WHERE customerdetails.username = %s
                            LIMIT 1""", (username,))
            address_details = cursor.fetchone()
            if address_details:
               # safely join only non-empty parts
               address = ",".join([str(part) for part in address_details if part])
            else:
               address = "Not available"
            return render_template('confirmation.html',product_id=product_id,product_name=product_name,Ingredients=Ingredients,price=price,address=address,quantity=quantity)
         else:
            return "Product is not available",400
      except mysql.connector.Error as err:
         print(f"Database error: {err}")
         return "An error occurred while processing your request.", 500
      finally:
         cursor.close()
         conn.close()

    
@app.route('/delete_cart_item/<int:product_id>', methods=['POST'])
def delete_cart_item(product_id):
    if 'user_status' not in session or session['user_status'] not in ["Registered", "logged_in"]:
        flash("You must be logged in to modify your cart.", "danger")
        return redirect(url_for('login'))
    
    user_id = get_current_user_id()
    if not user_id:
        flash("User not found.", "danger")
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if the item exists in user's cart
        cursor.execute("SELECT product_id FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
        if not cursor.fetchone():
            flash("Item not found in your cart.", "warning")
            return redirect(url_for('view_cart'))
        
        # Delete the specific item from cart
        cursor.execute("DELETE FROM cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
        conn.commit()
        
        flash("Item removed from cart successfully.", "success")
        
    except Exception as e:
        flash(f"Error removing item from cart: {str(e)}", "danger")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('view_cart'))

@app.route('/Delete_cart',methods=['POST','GET'])
def Delete_cart():
   if 'user_status' in session and (session['user_status'] == "Registered" or session['user_status'] == "logged_in"):
      username = session.get('username')
      conn = get_db_connection()
      cursor = conn.cursor()
      user_id = get_current_user_id()
      if user_id:
         cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
         conn.commit()
         flash("Cart emptied successfully.", "success")
         return redirect(url_for('view_cart'))
      cursor.close()
      conn.close()
      if not user_id:
         return "user not found",400
   else:
      return redirect(url_for('login'))
   
@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_status' not in session or session['user_status'] not in ['Registered', 'logged_in']:
        flash("You must be logged in to delete your account.", "danger")
        return redirect(url_for('login'))
    
    user_id = get_current_user_id()
    if not user_id:
        flash("User not found.", "danger")
        return redirect(url_for('login'))
    
    # Get confirmation from form
    confirmation = request.form.get('confirmation', '').strip().lower()
    if confirmation != 'delete':
        flash("Account deletion cancelled. You must type 'delete' to confirm.", "warning")
        return redirect(url_for('myprofile'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        conn.start_transaction()
        
        # Delete user's data in order (respecting foreign key constraints)
        # 1. Delete cart items
        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
        
        # 2. Delete orders
        cursor.execute("DELETE FROM orders WHERE user_id = %s", (user_id,))
        
        # 3. Delete address
        cursor.execute("DELETE FROM address WHERE user_id = %s", (user_id,))
        
        # 4. Finally delete user account
        cursor.execute("DELETE FROM customerdetails WHERE user_id = %s", (user_id,))
        
        # Commit transaction
        conn.commit()
        
        # Clear session
        session.clear()
        
        flash("Your account has been permanently deleted. We're sorry to see you go!", "info")
        return redirect(url_for('index'))
        
    except Exception as e:
        # Rollback on error
        conn.rollback()
        flash(f"Error deleting account: {str(e)}", "danger")
        return redirect(url_for('myprofile'))
    finally:
        cursor.close()
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))




@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check username
        cursor.execute("SELECT user_id FROM customerdetails WHERE username=%s", (username,))
        if cursor.fetchone():
            return jsonify({"error": "Username already exists"}), 400

        # Check email
        cursor.execute("SELECT user_id FROM customerdetails WHERE email=%s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "Email already exists"}), 400

        # Insert user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        cursor.execute(
            "INSERT INTO customerdetails (username, email, password) VALUES (%s, %s, %s)",
            (username, email, hashed_password)
        )
        conn.commit()

        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "All fields are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM customerdetails WHERE username=%s", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        if not user.get('password') or not check_password_hash(user.get('password'), password):
            return jsonify({"error": "Invalid credentials"}), 401

        # Store session (optional but useful)
        session['user_id'] = user['user_id']
        session['username'] = user['username']
        session['email'] = user['email']
        session['user_status'] = "logged_in"

        return jsonify({
            "message": "Login successful",
            "user": {
                "username": user['username'],
                "email": user['email']
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/api/me', methods=['GET'])
def api_me():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401

    return jsonify({
        "username": session.get('username'),
        "email": session.get('email')
    }), 200

@app.route('/api/cart', methods=['GET'])
def get_cart():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = get_current_user_id()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT p.product_id as id, p.product_name as name, 
               p.target_gender as gender, p.item_form as form,
               p.Ingredients as ingredients, p.special_features as feature,
               p.item_volume as volume, p.country,
               c.quantity, p.price
        FROM cart c
        JOIN product p ON p.product_id = c.product_id
        WHERE c.user_id = %s
    """, (user_id,))

    items = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(items), 200

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart_api():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    user_id = get_current_user_id()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT quantity FROM cart WHERE user_id=%s AND product_id=%s",
                   (user_id, product_id))
    existing = cursor.fetchone()

    if existing:
        new_qty = existing[0] + quantity
        cursor.execute("UPDATE cart SET quantity=%s WHERE user_id=%s AND product_id=%s",
                       (new_qty, user_id, product_id))
    else:
        cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                       (user_id, product_id, quantity))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Added to cart"}), 200

@app.route('/api/cart/remove/<int:product_id>', methods=['DELETE'])
def remove_cart_item(product_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = get_current_user_id()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM cart WHERE user_id=%s AND product_id=%s",
                   (user_id, product_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Removed"}), 200

@app.route('/api/cart/clear', methods=['DELETE'])
def clear_cart():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = get_current_user_id()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM cart WHERE user_id=%s", (user_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Cart cleared"}), 200

@app.route('/api/order/cart', methods=['POST','OPTIONS'])
def place_order_cart():
    if request.method == 'OPTIONS':
        return jsonify({"message": "OK"}), 200
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json

    plot_no = data.get('plotno')
    street = data.get('street')
    area = data.get('area')
    state = data.get('state')
    pincode = data.get('pincode')
    country = data.get('country')

    # ✅ Validation
    if not all([plot_no, street, area, state, pincode, country]):
        return jsonify({"error": "All fields required"}), 400

    user_id = get_current_user_id()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # ✅ Save / Update Address
        cursor.execute("""
            INSERT INTO address(user_id, plot_no, street_address, area, country, state, pincode)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            plot_no = VALUES(plot_no),
            street_address = VALUES(street_address),
            area = VALUES(area),
            country = VALUES(country),
            state = VALUES(state),
            pincode = VALUES(pincode)
        """, (user_id, plot_no, street, area, country, state, pincode))

        address_str = f"{plot_no},{street},{area},{state},{pincode},{country}"

        # ✅ Fetch cart items
        cursor.execute("""
            SELECT c.product_id, c.quantity, p.price
            FROM cart c
            JOIN product p ON p.product_id = c.product_id
            WHERE c.user_id = %s
        """, (user_id,))

        cart_items = cursor.fetchall()

        if not cart_items:
            return jsonify({"error": "Cart is empty"}), 400

        total_amount = 0

        # ✅ Insert into orders
        for item in cart_items:
            product_id = item['product_id']
            quantity = item['quantity']
            price = item['price']

            cursor.execute("""
                INSERT INTO orders(user_id, product_id, quantity, address)
                VALUES (%s, %s, %s, %s)
            """, (user_id, product_id, quantity, address_str))

            total_amount += price * quantity

        # ✅ Clear cart
        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))

        conn.commit()

        return jsonify({
            "message": "Order placed successfully",
            "total": total_amount
        }), 200

    except Exception as e:
        # ❗ VERY IMPORTANT
        conn.rollback()
        print("ERROR in /api/order/cart:", str(e))
        return jsonify({"error": "Server error"}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/api/order/confirmation', methods=['GET'])
def order_confirmation_api():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = get_current_user_id()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # ✅ Step 1: Get latest order timestamp
        cursor.execute("""
            SELECT order_date
            FROM orders
            WHERE user_id = %s
            ORDER BY order_id DESC
            LIMIT 1
        """, (user_id,))

        latest = cursor.fetchone()

        if not latest:
            return jsonify({"orders": []}), 200

        latest_date = latest['order_date']

        # ✅ Step 2: Fetch only that order batch
        cursor.execute("""
            SELECT p.product_name, p.Ingredients, p.price, o.quantity, o.address
            FROM orders o
            JOIN product p ON p.product_id = o.product_id
            WHERE o.user_id = %s AND o.order_date = %s
            ORDER BY o.order_id ASC
        """, (user_id, latest_date))

        orders = cursor.fetchall()

        return jsonify({
            "orders": orders
        }), 200

    finally:
        cursor.close()
        conn.close()
@app.route('/api/order/buy-now', methods=['POST'])
def buy_now_api():
    if 'user_id' not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json
    print("✅ BUY NOW API HIT")
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)

    plot_no = data.get('plotno')
    street = data.get('street')
    area = data.get('area')
    state = data.get('state')
    pincode = data.get('pincode')
    country = data.get('country')

    if not all([product_id, plot_no, street, area, state, pincode, country]):
        return jsonify({"error": "Missing fields"}), 400

    user_id = get_current_user_id()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        address_str = f"{plot_no},{street},{area},{state},{pincode},{country}"

        cursor.execute("""
            INSERT INTO orders(user_id, product_id, quantity, address, order_date)
            VALUES(%s,%s,%s,%s,NOW())
        """, (user_id, product_id, quantity, address_str))

        conn.commit()

        return jsonify({"message": "Order placed"}), 200

    except Exception as e:
        print("🔥 BUY NOW ERROR:", e)   # 👈 THIS IS CRITICAL
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    if FLASK_ENV == 'production':
        app.run(debug=False, ssl_context='adhoc')
    else:
        app.run(debug=True)
