# 🌸 Perfect Perfume

**Perfect Perfume** is an elegant e-commerce web application built using **Flask**, featuring secure user authentication (manual + Google OAuth), OTP-based registration, shopping cart management, order tracking, and email notifications — all designed for a seamless perfume shopping experience.

---

## 🚀 Live Demo

🔗 **Website:** [https://perfect-perfume-three.vercel.app](https://perfect-perfume-three.vercel.app)
💻 **Repository:** [https://github.com/HariVignesh18/Perfect-Perfume](https://github.com/HariVignesh18/Perfect-Perfume)

---

## 🧰 Tech Stack

| Component                  | Technology                                                     |
| -------------------------- | -------------------------------------------------------------- |
| **Frontend**               | HTML, CSS (Bootstrap 5), Jinja2 Templates                      |
| **Backend**                | Flask (Python)                                                 |
| **Database**               | MySQL                                                          |
| **Authentication**         | Google OAuth (Flask-Dance), Manual login with password hashing |
| **Email Service**          | Flask-Mail (SMTP via Gmail)                                    |
| **OTP Verification**       | PyOTP                                                          |
| **Hosting**                | Vercel                                                         |
| **Environment Management** | python-dotenv                                                  |

---

## ✨ Features

### 👤 User Management

* Secure registration with OTP verification via email
* Passwords stored using `werkzeug.security` hashing
* Google OAuth login via Flask-Dance
* Session-based authentication
* View and delete profile functionality

### 🛍️ Shopping Experience

* Add products to cart
* Modify or delete cart items
* “Buy Now” and “Buy from Cart” options
* Address management (auto-update on next orders)
* Automatic email confirmation on order placement

### 💌 Email Notifications

* OTP email during registration
* Welcome email after account creation
* Order confirmation emails

### 🔒 Security

* Encrypted passwords (SHA256 via Werkzeug)
* Environment variables for secrets & credentials
* Transaction-safe account deletion (with rollback on error)

---

## 🧩 Project Structure

```
Perfect-Perfume/
│
├── app.py                 # Main Flask application
├── templates/             # HTML templates (Jinja2)
│   ├── index.html
│   ├── Registration.html
│   ├── login.html
│   ├── cart.html
│   ├── myprofile.html
│   ├── confirmation.html
│   └── ...
├── static/                # CSS, JS, images
├── .env                   # Environment variables
├── requirements.txt        # Python dependencies
└── README.md               # Documentation
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/HariVignesh18/Perfect-Perfume.git
cd Perfect-Perfume
```

### 2️⃣ Create and Activate Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a `.env` file in the root directory and add:

```env
DB_HOST=localhost
DB_USERNAME=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_DBNAME=perfect_perfume

EMAIL=youremail@gmail.com
EMAIL_PWD=your_app_password
MAILPORT=465

APP_SECRET=your_flask_secret_key

GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret

OIT=1
```

### 5️⃣ Run the App

```bash
python app.py
```

Visit `http://127.0.0.1:5000` in your browser.

---

## 📦 Database Schema (MySQL)

Tables used:

* **customerdetails** (user_id, username, email, password)
* **product** (product_id, product_name, price, category, etc.)
* **cart** (user_id, product_id, quantity, added_time)
* **address** (user_id, plot_no, street_address, area, country, state, pincode)
* **orders** (order_id, user_id, product_id, quantity, address)

---

## 🧠 Key Functional Highlights

| Feature            | Description                                            |
| ------------------ | ------------------------------------------------------ |
| OTP Authentication | Time-based OTP valid for 5 minutes                     |
| Session Tracking   | User info cached with `user_id`, `email`, and `status` |
| Account Deletion   | Cascading delete (cart → orders → address → user)      |
| Email Integration  | Uses Flask-Mail for SMTP Gmail delivery                |
| Google OAuth       | Automatically links or creates user accounts           |

---

## 🧾 License

This project is for educational and demonstration purposes.
© 2025 Hari Vignesh B. All Rights Reserved.
