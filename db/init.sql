
CREATE TABLE les_entries (
  
  id INT PRIMARY KEY AUTO_INCREMENT,
  
  name VARCHAR(100) NOT NULL,
  
  branch VARCHAR(50) NOT NULL,
  
  pay_grade VARCHAR(20) NOT NULL,
  
  years_of_service INT NOT NULL,
  
  filing_status VARCHAR(20) NOT NULL,
  
  resident_state VARCHAR(10) NOT NULL,
  
  duty_location VARCHAR(120) NOT NULL,
  
  duty_location_code VARCHAR(20) NOT NULL,
  
  has_dependents VARCHAR(5) NOT NULL,
  
  base_pay DECIMAL(12,2) NOT NULL DEFAULT 0,
  
  bas DECIMAL(12,2) NOT NULL DEFAULT 0,
  
  bah DECIMAL(12,2) NOT NULL DEFAULT 0,
  
  special_pay DECIMAL(12,2) NOT NULL DEFAULT 0,
  
  other_taxable DECIMAL(12,2) NOT NULL DEFAULT 0,
  
  other_nontaxable DECIMAL(12,2) NOT NULL DEFAULT 0,
  
  tsp DECIMAL(12,2) NOT NULL DEFAULT 0,
  
  allotments DECIMAL(12,2) NOT NULL DEFAULT 0,
  
  debts DECIMAL(12,2) NOT NULL DEFAULT 0,
  
  sgli DECIMAL(12,2) NOT NULL DEFAULT 0,
  
  notes VARCHAR(255) NOT NULL DEFAULT '',
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
