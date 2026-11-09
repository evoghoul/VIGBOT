import sqlite3
import json

db_path = "database/vigbot.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# 1. Insert or update policies
cur.execute("DELETE FROM policies WHERE policy_id = 'POL-CONDONATION-ANNEXURE2'")
cur.execute("""
    INSERT INTO policies (policy_id, title, clause_no, effective_date, summary, authority)
    VALUES (
        'POL-CONDONATION-ANNEXURE2',
        'Procedure for paying Condonation fee',
        'Annexure – 2',
        '2024-07-01',
        'Students have to pay Rs. 500/- for each course as condonation fee for shortage of attendance. Students having four or more courses has to pay Rs 2000/-. Payment should be made by voucher (Not online): Bank name: PNB Bank, Branch: Vadlamudi. After payment, original copy of the challan should be submitted at the Examination section by the Student and get a receipt. Hall-Tickets will be issued to the candidate only after paying the condonation fee.',
        'Office of Dean – Academics, Assessment and Awards'
    )
""")

# 2. Insert or update administrative_procedures
steps = [
    "Step 1: Calculate condonation fee — Rs. 500/- for each course as condonation fee for shortage of attendance, or flat Rs. 2,000/- if having four or more courses.",
    "Step 2: Remit payment by voucher (Not online) at PNB Bank (Punjab National Bank), Vadlamudi Branch.",
    "Step 3: Collect the original stamped copy of the bank challan after remittance.",
    "Step 4: Submit the original copy of the challan at the Examination section by the Student and get an official receipt.",
    "Step 5: Hall-Tickets will be issued to the candidate only after paying the condonation fee and submitting receipt."
]

cur.execute("DELETE FROM administrative_procedures WHERE procedure_id = 'condonation_fee_payment'")
cur.execute("""
    INSERT INTO administrative_procedures (
        procedure_id, title, category, phase1_digital_instructions,
        phase2_physical_location, phase2_steps_json, fee_amount,
        office_location, sla_turnaround_days
    )
    VALUES (
        'condonation_fee_payment',
        'Procedure for paying Condonation fee',
        'Academic Regulations',
        'Attendance shortage condonation fee payment is strictly offline (Not online). Remit fee via bank voucher at PNB Bank Vadlamudi branch.',
        'PNB Bank (Punjab National Bank), Vadlamudi Branch & Examination Section',
        ?,
        500.0,
        'Office of Dean – Academics, Assessment and Awards & Examination Section',
        1
    )
""", (json.dumps(steps),))

# 3. Insert or update ai_knowledge_base
cur.execute("SELECT id FROM ai_knowledge_base WHERE question LIKE '%condonation fee%'")
row = cur.fetchone()
kb_ans = (
    "According to VFSTR Office of Dean – Academics, Assessment and Awards (Annexure – 2: Procedure for paying Condonation fee):\n"
    "1. Students have to pay Rs. 500/- for each course as condonation fee for shortage of attendance.\n"
    "2. Students having four or more courses has to pay Rs 2000/-.\n"
    "3. Payment should be made by voucher (Not online):\n"
    "   • Bank name: PNB Bank\n"
    "   • Branch: Vadlamudi\n"
    "4. After payment, original copy of the challan should be submitted at the Examination section by the Student and get a receipt.\n"
    "5. Hall-Tickets will be issued to the candidate only after paying the condonation fee."
)
meta = json.dumps({"tags": ["condonation", "fee", "pnb bank", "challan", "hall ticket", "examination section", "annexure-2"]})

if row:
    cur.execute("UPDATE ai_knowledge_base SET answer = ?, metadata = ? WHERE id = ?", (kb_ans, meta, row[0]))
else:
    cur.execute(
        "INSERT INTO ai_knowledge_base (category, question, answer, metadata) VALUES (?, ?, ?, ?)",
        ("Academics", "Procedure for paying Condonation fee", kb_ans, meta)
    )

# 4. Insert or update knowledge_procedure & knowledge_procedure_step
cur.execute("""
    INSERT INTO knowledge_procedure (procedure_id, title, description, rules)
    VALUES (
        'PROC_CONDONATION',
        'Procedure for paying Condonation fee',
        'VFSTR Annexure – 2: Rules and procedure for paying condonation fee for attendance shortage.',
        'Rs. 500/- per course; Rs. 2,000/- for 4 or more courses. Voucher payment only (Not online) at PNB Bank Vadlamudi. Hall-Tickets issued only after payment.'
    )
    ON CONFLICT(procedure_id) DO UPDATE SET
        title=excluded.title,
        description=excluded.description,
        rules=excluded.rules;
""")

cur.execute("DELETE FROM knowledge_procedure_step WHERE procedure_id='PROC_CONDONATION'")
p_steps = [
    ('P_COND_1', 'PROC_CONDONATION', 1, 'Pay condonation fee via bank voucher (Not online) at PNB Bank, Vadlamudi Branch (Rs. 500/- for each course; Rs. 2000/- for 4 or more courses).'),
    ('P_COND_2', 'PROC_CONDONATION', 2, 'Submit the original copy of the paid bank challan to the Examination Section and get a receipt.'),
    ('P_COND_3', 'PROC_CONDONATION', 3, 'Collect Hall-Ticket from Examination Section (issued only after paying condonation fee).')
]
cur.executemany("INSERT INTO knowledge_procedure_step (step_id, procedure_id, step_order, instruction) VALUES (?, ?, ?, ?)", p_steps)

conn.commit()
conn.close()
print("Successfully updated SQLite vigbot.db with Annexure – 2 records!")
