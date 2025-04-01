# PERFECT PERFUME

A scalable e-commerce platform for direct perfume sales, focusing on backend system integration and user interface optimization. Implemented a dynamic cart system to enhance the shopping experience, ensuring smooth transactions and user interactions with an order confirmation email system. Now hosted on **Vercel** for seamless deployment.

---

## Technologies Used

### Frontend:
- HTML
- CSS
- JavaScript
- Bootstrap

### Backend:
- Python
- Flask
- MySQL
- werkzeug.security
- Flask-Mail (for email notifications)

### Programming Concepts:
- Object-Oriented Programming
- Data Structures & Algorithms (Stack, Sorting)

### Deployment:
- Hosted on **Vercel** with environment variables configured for secure access.

---

## HOW TO GET STARTED:

### Step 1: Clone the repository
Clone the repository to your local environment using:
```bash
 git clone https://github.com/yourusername/perfect-perfume.git
```

### Step 2: Set up Environment Variables
Create a `.env` file and add the following configurations:
```env
APP_SECRET=your_secret_key
EMAIL=your_email
EMAIL_PWD=your_app_password
```

### Step 3: Set Up MySQL Database
Open MySQL Workbench and execute the following SQL commands:

```sql
CREATE DATABASE perfume_company;
USE perfume_company;

CREATE TABLE customerdetails (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    password VARCHAR(200),
    email VARCHAR(50)
);

CREATE TABLE product (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(50),
    target_gender VARCHAR(10),
    item_form VARCHAR(10),
    ingredients VARCHAR(50),
    special_features VARCHAR(50),
    item_volume INT,
    country VARCHAR(20),
    price INT
);

INSERT INTO product VALUES
(1, 'Floral Perfume', 'Unisex', 'Spray', 'Jasmine', 'Natural Ingredients', 60, 'India', 599),
(2, 'Woody Perfume', 'Unisex', 'Spray', 'Cedarwood', 'Long-lasting', 60, 'India', 699),
(3, 'Citrus Perfume', 'Unisex', 'Spray', 'Essential Oils', 'Fresh Fragrance', 60, 'India', 799);

CREATE TABLE address (
    address_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    plot_no INT NOT NULL,
    street_address VARCHAR(50) NOT NULL,
    area VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    pincode INT NOT NULL,
    country VARCHAR(20) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES customerdetails(user_id)
);

CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    product_id INT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quantity INT,
    FOREIGN KEY (user_id) REFERENCES customerdetails(user_id),
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);

CREATE TABLE cart (
    cart_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    product_id INT,
    quantity INT DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES customerdetails(user_id),
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);
```

### Step 4: Install Dependencies
Navigate to the project directory and install the required dependencies:
```bash
pip install -r requirements.txt
```

### Step 5: Run the Application
Start the Flask application using:
```bash
python app.py
```



