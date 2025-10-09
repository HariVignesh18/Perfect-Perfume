-- merge_duplicates.sql
-- WARNING: Backup your database before running this. This script assumes
-- - you want to keep the smallest user_id (MIN) for each duplicated email
-- - tables: customerdetails(user_id), cart(user_id), orders(user_id), address(user_id)
-- Run in a transaction and test on a copy first.

-- 1) Preview duplicate emails
SELECT email, COUNT(*) AS cnt, GROUP_CONCAT(user_id ORDER BY user_id) AS ids
FROM customerdetails
GROUP BY email
HAVING cnt > 1;

-- 2) For each duplicated email, choose keep_id (here we use MIN(user_id)) and list duplicates
-- Example for one email (replace 'the@email' with the actual email):
-- SELECT MIN(user_id) AS keep_id, GROUP_CONCAT(user_id) AS all_ids FROM customerdetails WHERE email='the@email';

-- 3) Migrate related rows from duplicates to keep_id (REPLACE <keep_id> and <dup_id> accordingly)
-- UPDATE cart SET user_id = <keep_id> WHERE user_id = <dup_id>;
-- UPDATE orders SET user_id = <keep_id> WHERE user_id = <dup_id>;
-- UPDATE address SET user_id = <keep_id> WHERE user_id = <dup_id>;

-- 4) Once migrated, remove duplicate user rows (keep only keep_id)
-- DELETE FROM customerdetails WHERE user_id = <dup_id>;

-- 5) After verifying, add unique constraint on email
-- ALTER TABLE customerdetails ADD CONSTRAINT uq_customerdetails_email UNIQUE (email);

-- Important: don't run this file blindly. Use the accompanying Python script to dry-run and apply changes.
