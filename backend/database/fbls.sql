
CREATE TABLE IF NOT EXISTS faculty (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    department VARCHAR(100) NOT NULL,
    role ENUM('faculty', 'admin') DEFAULT 'faculty',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create equipment table
CREATE TABLE IF NOT EXISTS equipment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    status ENUM('available', 'borrowed', 'maintenance') DEFAULT 'available',
    serial_number VARCHAR(50) UNIQUE,
    condition_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create borrowing_logs table
CREATE TABLE IF NOT EXISTS borrowing_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    faculty_id INT,
    equipment_id INT,
    borrow_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expected_return_date TIMESTAMP NOT NULL,
    actual_return_date TIMESTAMP NULL,
    status ENUM('pending', 'approved', 'rejected', 'returned') DEFAULT 'pending',
    remarks TEXT,
    FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
);

-- Insert default admin user
INSERT INTO faculty (name, email, password, department, role) 
VALUES (
    'Admin User', 
    'admin@fbls.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewTE3w1UJt4S.J/2', -- password: admin123
    'IECS',
    'admin'
);

-- Insert sample equipment categories
INSERT INTO equipment (name, category, serial_number, condition_notes) VALUES
('Projector 1', 'Multimedia', 'PRJ001', 'Good condition'),
('Laptop 1', 'Computer', 'LPT001', 'New'),
('Speaker Set', 'Audio', 'SPK001', 'Working perfectly'),
('Digital Camera', 'Photography', 'CAM001', 'Slightly used');

-- Create indexes for better performance
CREATE INDEX idx_faculty_email ON faculty(email);
CREATE INDEX idx_equipment_status ON equipment(status);
CREATE INDEX idx_borrowing_status ON borrowing_logs(status);