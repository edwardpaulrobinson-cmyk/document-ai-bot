-- creating a database
CREATE DATABASE dena_bank;

-- make the db operational , USE
USE dena_bank;

-- creating the tables and then inserting the records
-- syntax : CREATE TABLE <tablename> (column_name datatype constraint)

CREATE TABLE dena_records (
customer_id INT PRIMARY KEY,
customerName VARCHAR(25),
transaction_id INT ,
transaction_date DATE,
transaction_amount DECIMAL(10,2),
transaction_type VARCHAR(20)
);

-- insert 10 records in the table

INSERT INTO Dena_Records (customer_id,customer_name,transaction_id,transaction_date,transaction_amount,transaction_type) VALUES

(1, 'John Doe', 1001, '2024-01-01', 150.75, 'Deposit'),
(2, 'Jane Smith', 1002, '2024-01-02', 200.00, 'Withdrawal'),
(3, 'Emily Johnson', 1003, '2024-01-03', 50.50, 'Deposit'),
(4, 'Michael Brown', 1004, '2024-01-04', 400.00, 'Deposit'),
(5, 'Chris Davis', 1005, '2024-01-05', 300.25, 'Withdrawal'),
(6, 'Jessica Miller', 1006, '2024-01-06', 100.00, 'Deposit'),
(7, 'Matthew Wilson', 1007, '2024-01-07', 600.75, 'Withdrawal'),
(8, 'Ashley Moore', 1008, '2024-01-08', 250.00, 'Deposit'),
(9, 'Daniel Taylor', 1009, '2024-01-09', 450.50, 'Deposit'),
(10, 'Laura Anderson', 1010, '2024-01-10', 50.00, 'Withdrawal'),
(11, 'James Thomas', 1011, '2024-01-11', 700.75, 'Deposit'),
(12, 'Patricia Jackson', 1012, '2024-01-12', 150.00, 'Withdrawal'),
(13, 'Robert White', 1013, '2024-01-13', 500.50, 'Deposit'),
(14, 'Linda Harris', 1014, '2024-01-14', 600.00, 'Deposit'),
(15, 'David Martin', 1015, '2024-01-15', 300.00, 'Withdrawal'),
(16, 'Barbara Thompson', 1016, '2024-01-16', 100.50, 'Deposit'),
(17, 'Joseph Garcia', 1017, '2024-01-17', 50.00, 'Withdrawal'),
(18, 'Susan Martinez', 1018, '2024-01-18', 700.00, 'Deposit'),
(19, 'Charles Robinson', 1019, '2024-01-19', 800.75, 'Withdrawal'),
(20, 'Karen Clark', 1020, '2024-01-20', 200.50, 'Deposit');


-- show the entire table created
-- SELECT RECORDS FROM TABLE;  -- * means selecting all the records
SELECT * FROM dena_records;

-- I only want to see selected number of columns

SELECT customer_id, customerName , Transaction_type
FROM dena_records;

