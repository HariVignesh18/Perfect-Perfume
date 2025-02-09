<h1>PERFECT PERFUME</h1>
<h4>A scalable e-commerce platform for direct perfume sales, focusing on backend system integration and user interface optimization. Also, implemented a dynamic cart system to enhance the shopping experience, ensuring smooth transactions and user interactions with order confirmation mail system. </h4>
<hr>
<h2>Technologies Used</h2>
<h3>Frontend:</h3>
<ul>
  <li>HTML.</li>
  <li>CSS.</li>
  <li>JavaScript.</li>
  <li>CSS Bootstrap.</li>
</ul>
<h3>Backend:</h3>
<ul>
  <li>Python.</li>
  <li>Flask.</li>
  <li>MySQL.</li>
  <li>werkzeug.security</li>
</ul>
<h3>Programming concepts</h3>
<ul>
  <li>Object Oriented Programming.</li>
  <li>DSA - Stack.</li>
  <li>Sorting.</li>
</ul>
<h3>HOW TO GET STARTED:</h3>
     <p> <b>Step 1:</b> Clone the Repository to your local Environment.</p>
     <p> <b>Step 2:</b> Open your MySQL Workbench.</p>
     <p> <b>Step 3:</b> Copy paste the following comments in the workspace of MySQL.</p>
     
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
    product_id INT,
    product_name VARCHAR(20),
    target_gender VARCHAR(6),
    item_form VARCHAR(5),
    Ingredients VARCHAR(20),
    special_features VARCHAR(30),
    item_volume INT,
    country VARCHAR(10),
    price INT
);

INSERT INTO product VALUES 
(1, 'Floral perfume', 'unisex', 'bar', 'jasmine', 'Natural_ingredients', 60, 'India', 599),
(2, 'Woody perfume', 'unisex', 'bar', 'Cedarwood', 'Natural_ingredients', 60, 'India', 599),
(3, 'Citrus Perfume', 'unisex', 'bar', 'Essential oils', 'Natural_ingredients', 60, 'India', 599),
(4, 'Oriental Perfume', 'unisex', 'bar', 'Spices', 'Natural_ingredients', 60, 'India', 599),
(5, 'Fresh Aqua Perfume', 'unisex', 'bar', 'Calone', 'Natural_ingredients', 60, 'India', 599),
(6, 'Gourmand Perfume', 'unisex', 'bar', 'honey', 'Natural_ingredients', 60, 'India', 599);

CREATE TABLE address (
    address_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    plot_no INT NOT NULL,
    street_address VARCHAR(10) NOT NULL,
    area VARCHAR(40) NOT NULL,
    state VARCHAR(40) NOT NULL,
    pincode INT NOT NULL,
    country VARCHAR(10) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES customerdetails(user_id)
);

CREATE TABLE orders (
    user_id INT,
    order_id INT AUTO_INCREMENT PRIMARY KEY,
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
<p> <b>Step 4:</b> After executing all these sql statements.Go to the terminal, and run the file app.py using the command "<b>Python app.py</b>"</p>
     <p> The website is now successfully developed and ready for deployment.</p>
