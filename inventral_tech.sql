-- PostgreSQL database dump
-- Converted from MySQL/phpMyAdmin SQL Dump

-- Set timezone
SET TIMEZONE = '+00:00';

-- Create database (commented out as you may want to create it separately)
-- CREATE DATABASE inventral_tech;
-- \c inventral_tech;

-- Table structure for table 'index_contact'
CREATE TABLE index_contact (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Dumping data for table 'index_contact'
INSERT INTO index_contact (id, name, email, message, created_at) VALUES
(1, 'Ian', 'odiwuorian@gmail.com', 'wwerwr', '2025-06-27 11:16:06');

-- Reset the sequence to avoid primary key conflicts
SELECT setval('index_contact_id_seq', (SELECT MAX(id) FROM index_contact));

-- Table structure for table 'signup_table'
CREATE TABLE signup_table (
  fullname TEXT NOT NULL,
  email VARCHAR(50) PRIMARY KEY,
  password VARCHAR(50) NOT NULL
);

-- Dumping data for table 'signup_table'
INSERT INTO signup_table (fullname, email, password) VALUES
('Joe Dee', 'odiwuorian@gmail.com', 'audiA7@2024');
-- converted it to a postgreSQL format @n00b01 >>github