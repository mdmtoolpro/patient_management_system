import random
import string
from datetime import datetime

def generate_patient_id():
    timestamp = datetime.now().strftime('%y%m%d')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"P{timestamp}{random_str}"

def generate_lab_test_id():
    timestamp = datetime.now().strftime('%y%m%d')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"LT{timestamp}{random_str}"

def generate_bill_number():
    timestamp = datetime.now().strftime('%y%m%d')
    random_str = ''.join(random.choices(string.digits, k=4))
    return f"B{timestamp}{random_str}"

def calculate_age(born):
    from datetime import date
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def generate_prescription_id():
    return f"RX{random.randint(10000, 99999)}"