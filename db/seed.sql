-- FieldAI Seed Data
-- Standard Reference Libraries, Sampling Tables, SoD Rules, and Framework Mappings

-- 1. Sampling Table (Standard IIA / Internal Audit Frequency-Based Rules)
INSERT INTO sampling_table (frequency, risk_level, sample_size, rationale) VALUES
('Annual', 'Low', 1, 'Standard 100% testing for annual controls'),
('Annual', 'Medium', 1, 'Standard 100% testing for annual controls'),
('Annual', 'High', 1, 'Standard 100% testing for annual controls'),
('Quarterly', 'Low', 2, '2 of 4 quarters tested'),
('Quarterly', 'Medium', 2, '2 of 4 quarters tested'),
('Quarterly', 'High', 4, 'All 4 quarters tested for high risk'),
('Monthly', 'Low', 2, 'Minimum 2 representative monthly items'),
('Monthly', 'Medium', 5, 'Sample of 5 months across the year'),
('Monthly', 'High', 10, 'Sample of 10 months for high risk'),
('Weekly', 'Low', 5, '5 items spread across quarters'),
('Weekly', 'Medium', 10, '10 items spread across quarters'),
('Weekly', 'High', 15, '15 items spread across quarters'),
('Daily', 'Low', 20, '20 daily transaction samples'),
('Daily', 'Medium', 25, 'Standard 25 daily samples for 95% confidence'),
('Daily', 'High', 40, '40 daily samples for heightened risk'),
('per transaction', 'Low', 25, 'Standard non-statistical sample 25 items'),
('per transaction', 'Medium', 25, 'Standard non-statistical sample 25 items'),
('per transaction', 'High', 45, 'Sample of 45-60 items for high inherent risk');

-- 2. Segregation of Duties (SoD) Incompatible Rules
INSERT INTO sod_rules (rule_code, function_a, function_b, risk_description, severity) VALUES
('SOD-01', 'Vendor Creation/Maintenance', 'Payment Processing', 'Risk of creating fictitious vendors and redirecting disbursements', 'High'),
('SOD-02', 'Purchase Order Creation', 'Purchase Order Approval', 'Risk of unauthorized commitments without independent supervisory approval', 'High'),
('SOD-03', 'Purchase Order Approval', 'Goods Receipt Entry', 'Risk of ordering and acknowledging receipt of unauthorized goods', 'High'),
('SOD-04', 'Invoice Entry', 'Payment Approval / Release', 'Risk of generating and releasing unauthorized vendor disbursements', 'High'),
('SOD-05', 'Payment Release / Signoff', 'Bank Account Reconciliation', 'Risk of concealing fraudulent disbursements or unrecorded disbursements', 'High'),
('SOD-06', 'User Security Admin', 'Business Transaction Processing', 'Risk of assigning privileged roles to self and posting unauthorized transactions', 'High'),
('SOD-07', 'Payroll Master Maintenance', 'Payroll Disbursement', 'Risk of creating ghost employees and collecting paychecks', 'High');

-- 3. Risk Library (Standard Procurement & Financial Controls)
INSERT INTO risk_library (category, risk_code, name, description, inherent_rating_hint) VALUES
('Procurement', 'R-LIB-01', 'Fictitious or Unqualified Vendor', 'Vendors added without vetting may lead to fraud, non-compliance, or poor service quality', 'High'),
('Procurement', 'R-LIB-02', 'Unauthorized Procurement Commitments', 'Purchase orders issued without delegation of authority approvals', 'High'),
('Procurement', 'R-LIB-03', 'Sub-division of Purchase Orders', 'Purchases split below threshold to bypass mandatory executive approvals', 'Medium'),
('Procurement', 'R-LIB-04', 'Inaccurate or Non-Received Goods', 'Payment released for goods or services that were not received or are defective', 'High'),
('Procurement', 'R-LIB-05', 'Duplicate or Overpayment of Invoices', 'Failure to match invoices against PO and receipt leads to duplicate disbursement', 'High'),
('Procurement', 'R-LIB-06', 'Excessive User System Access', 'Users possess unauthorized or conflicting permissions in the ERP system', 'High'),
('Procurement', 'R-LIB-07', 'Late Payment or Lost Discounts', 'Delay in invoice verification results in late penalties and strained supplier relations', 'Low');

-- 4. Control Library
INSERT INTO control_library (category, control_code, name, description, control_type, nature, frequency_hint) VALUES
('Procurement', 'C-LIB-01', 'Vendor Vetting and Dual Approval', 'New vendor onboarding requires commercial registration check and dual finance sign-off', 'preventive', 'manual', 'per transaction'),
('Procurement', 'C-LIB-02', 'System-Enforced PO Approval Matrix', 'ERP enforces delegation of authority thresholds before PO release', 'preventive', 'automated', 'per transaction'),
('Procurement', 'C-LIB-03', 'Mandatory 3-Way Matching', 'ERP automatically blocks payment unless PO, Goods Receipt, and Invoice match within tolerance', 'preventive', 'automated', 'per transaction'),
('Procurement', 'C-LIB-04', 'Warehouse Receiving Inspection', 'Warehouse personnel perform physical counts against delivery note before signing GRN', 'detective', 'manual', 'per transaction'),
('Procurement', 'C-LIB-05', 'Periodic User Access Certification', 'IT and department heads conduct quarterly access reviews and revoke orphaned accounts', 'detective', 'manual', 'quarterly'),
('Procurement', 'C-LIB-06', 'Dual Payment Batch Release', 'Electronic banking disbursements require two authorized signatories with hardware tokens', 'preventive', 'automated', 'daily');

-- 5. Framework Mappings (COSO 2013, COBIT 2019, ISO 27001, NCA ECC, SAMA CSF)
INSERT INTO framework_controls (framework_name, requirement_code, title, description, mapped_control_category) VALUES
('COSO 2013', 'Principle 10', 'Control Activities Selection', 'The organization selects and develops control activities that contribute to mitigation of risks', 'Procurement'),
('COSO 2013', 'Principle 11', 'General IT Controls', 'The organization selects and develops general control activities over technology', 'Procurement'),
('COSO 2013', 'Principle 12', 'Policies and Procedures', 'The organization deploys control activities through policies that establish what is expected', 'Procurement'),
('COBIT 2019', 'APO11.06', 'Quality Management', 'Monitor and maintain quality of business processes and deliverables', 'Procurement'),
('COBIT 2019', 'BAI03.05', 'System Controls and Auditability', 'Implement controls, integrity verification, and audit trails in applications', 'Procurement'),
('ISO 27001:2022', 'A.5.15', 'Access Control', 'Access to information and other associated assets shall be restricted in accordance with business requirements', 'Procurement'),
('ISO 27001:2022', 'A.5.3', 'Segregation of Duties', 'Conflicting duties and conflicting areas of responsibility shall be segregated', 'Procurement'),
('NCA ECC', 'ECC-1-2-3', 'Access Control and Privilege Management', 'Enforce least privilege and segregation of conflicting responsibilities', 'Procurement'),
('NCA ECC', 'ECC-2-1-1', 'Third-Party / Vendor Cybersecurity', 'Cybersecurity requirements must be verified for all approved suppliers', 'Procurement'),
('SAMA CSF', '3.1.1', 'Identity and Access Management', 'User authentication and access rights are managed and periodically reviewed', 'Procurement');

-- 6. Analytics Test Definitions
INSERT INTO analytics_library (test_id, name, description, required_fields_json, logic_code) VALUES
('AN-01', 'Duplicate Invoice Payments', 'Detects duplicate disbursements with identical vendor, amount, invoice number or date', '["vendor_id", "invoice_no", "amount", "date"]', 'duplicate_payments'),
('AN-02', 'Split Purchases Below Approval Limit', 'Identifies multiple purchase orders issued to the same vendor on the same day just below approval threshold', '["vendor_id", "po_number", "amount", "date"]', 'split_purchases'),
('AN-03', 'Weekend and Holiday Postings', 'Flags transactions posted on non-working days or outside operating business hours', '["transaction_id", "amount", "date", "user_id"]', 'weekend_postings'),
('AN-04', 'Round Dollar / Round Amount Analysis', 'Highlights high-value round-figure payments indicative of estimated or unverified fees', '["transaction_id", "vendor_id", "amount"]', 'round_amounts'),
('AN-05', 'Just-Below Threshold Testing', 'Finds transactions within 5% below delegated authority tiers', '["transaction_id", "amount", "approver"]', 'below_threshold'),
('AN-06', 'Benfords Law 1st Digit Analysis', 'Evaluates first-digit frequency distribution against Benford law expectation to detect anomalies', '["amount"]', 'benford_analysis'),
('AN-07', 'Missing Approval Verification', 'Identifies POs and payment batches where approval timestamp or approver ID is null', '["transaction_id", "amount", "approver_id"]', 'missing_approvals'),
('AN-08', 'Three-Way Match Discrepancies', 'Calculates quantity and unit price variance between PO, Goods Receipt, and Invoice', '["po_qty", "receipt_qty", "inv_qty", "po_price", "inv_price"]', 'three_way_match'),
('AN-09', 'Sequential Number Gaps', 'Detects missing document numbers in sequential voucher or invoice series', '["document_no"]', 'sequence_gaps');

-- 7. Initial Seed Engagement & Process
INSERT INTO engagements (name, entity, period, status) VALUES
('FY2026 Operational & Financial Controls Audit', 'Alpha Manufacturing Corp', 'FY2026', 'In Progress');

INSERT INTO processes (engagement_id, name, code_prefix, current_version) VALUES
(1, 'Procure-to-Pay (P2P)', 'P2P', 'v1.0');
