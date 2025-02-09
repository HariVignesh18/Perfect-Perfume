<h1>PERFECT PERFUME</h1>
<h4>A scalable e-commerce platform for direct perfume sales, focusing on backend system integration and user interface optimization. Implemented a dynamic cart system to enhance the shopping experience, ensuring smooth transactions and user interactions with an order confirmation email system. Now hosted on <b>Vercel</b> for seamless deployment.</h4>
<hr>

<h2>Technologies Used</h2>
<h3>Frontend:</h3>
<ul>
  <li>HTML</li>
  <li>CSS</li>
  <li>JavaScript</li>
  <li>Bootstrap</li>
</ul>

<h3>Backend:</h3>
<ul>
  <li>Python</li>
  <li>Flask</li>
  <li>MySQL</li>
  <li>werkzeug.security</li>
  <li>Flask-Mail (for email notifications)</li>
</ul>

<h3>Programming Concepts</h3>
<ul>
  <li>Object-Oriented Programming</li>
  <li>Data Structures & Algorithms (Stack, Sorting)</li>
</ul>

<h3>Deployment:</h3>
<ul>
  <li>Hosted on <b>Vercel</b> with environment variables configured for secure access.</li>
</ul>

<h3>HOW TO GET STARTED:</h3>
<p><b>Step 1:</b> Clone the repository to your local environment.</p>
<p><b>Step 2:</b> Set up environment variables in a <code>.env</code> file:</p>

```env
APP_SECRET=your_secret_key
EMAIL=your_email
EMAIL_PWD=your_app_password
<p><b>Step 3:</b> Open your MySQL Workbench and execute the following commands:</p>
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
<p><b>Step 4:</b> Install dependencies and run the application.</p>
pip install -r requirements.txt
python app.py
<p>The website is now successfully deployed on <b>Vercel</b> and ready for use!</p> ```
