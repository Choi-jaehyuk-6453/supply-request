import json
import os
import uuid
from datetime import datetime

DATA_FILE = "reference_data.json"

def get_default_data():
    return {
        "sites": [],
        "applicants": [],
        "email_recipients": [],
        "supply_products": [],
        "uniform_products": [],
        "last_updated": None
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        return get_default_data()
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "sites" not in data:
                data["sites"] = []
            if "applicants" not in data:
                data["applicants"] = []
            if "email_recipients" not in data:
                data["email_recipients"] = []
            if "supply_products" not in data:
                data["supply_products"] = []
            if "uniform_products" not in data:
                data["uniform_products"] = []
            return data
    except (json.JSONDecodeError, Exception):
        return get_default_data()

def save_data(data):
    data["last_updated"] = datetime.now().isoformat()
    temp_file = DATA_FILE + ".tmp"
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_file, DATA_FILE)
        return True
    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise e

def add_site(name, address, contact):
    data = load_data()
    site = {
        "id": str(uuid.uuid4()),
        "name": name,
        "address": address,
        "contact": contact,
        "created_at": datetime.now().isoformat()
    }
    data["sites"].append(site)
    save_data(data)
    return site

def update_site(site_id, name, address, contact):
    data = load_data()
    for site in data["sites"]:
        if site["id"] == site_id:
            site["name"] = name
            site["address"] = address
            site["contact"] = contact
            site["updated_at"] = datetime.now().isoformat()
            save_data(data)
            return site
    return None

def delete_site(site_id):
    data = load_data()
    data["sites"] = [s for s in data["sites"] if s["id"] != site_id]
    save_data(data)

def get_sites():
    data = load_data()
    return data.get("sites", [])

def get_site_by_name(name):
    sites = get_sites()
    for site in sites:
        if site["name"] == name:
            return site
    return None

def add_applicant(name, contact):
    data = load_data()
    applicant = {
        "id": str(uuid.uuid4()),
        "name": name,
        "contact": contact,
        "created_at": datetime.now().isoformat()
    }
    data["applicants"].append(applicant)
    save_data(data)
    return applicant

def update_applicant(applicant_id, name, contact):
    data = load_data()
    for applicant in data["applicants"]:
        if applicant["id"] == applicant_id:
            applicant["name"] = name
            applicant["contact"] = contact
            applicant["updated_at"] = datetime.now().isoformat()
            save_data(data)
            return applicant
    return None

def delete_applicant(applicant_id):
    data = load_data()
    data["applicants"] = [a for a in data["applicants"] if a["id"] != applicant_id]
    save_data(data)

def get_applicants():
    data = load_data()
    return data.get("applicants", [])

def get_applicant_by_name(name):
    applicants = get_applicants()
    for applicant in applicants:
        if applicant["name"] == name:
            return applicant
    return None

def search_sites(query):
    if not query:
        return get_sites()
    sites = get_sites()
    return [s for s in sites if query.lower() in s["name"].lower()]

def search_applicants(query):
    if not query:
        return get_applicants()
    applicants = get_applicants()
    return [a for a in applicants if query.lower() in a["name"].lower()]

def add_email_recipient(company_name, email):
    data = load_data()
    recipient = {
        "id": str(uuid.uuid4()),
        "company_name": company_name,
        "email": email,
        "created_at": datetime.now().isoformat()
    }
    data["email_recipients"].append(recipient)
    save_data(data)
    return recipient

def update_email_recipient(recipient_id, company_name, email):
    data = load_data()
    for recipient in data["email_recipients"]:
        if recipient["id"] == recipient_id:
            recipient["company_name"] = company_name
            recipient["email"] = email
            recipient["updated_at"] = datetime.now().isoformat()
            save_data(data)
            return recipient
    return None

def delete_email_recipient(recipient_id):
    data = load_data()
    data["email_recipients"] = [r for r in data["email_recipients"] if r["id"] != recipient_id]
    save_data(data)

def get_email_recipients():
    data = load_data()
    return data.get("email_recipients", [])


def add_supply_product(name, spec, unit_price):
    data = load_data()
    product = {
        "id": str(uuid.uuid4()),
        "name": name,
        "spec": spec,
        "unit_price": int(unit_price),
        "created_at": datetime.now().isoformat()
    }
    data["supply_products"].append(product)
    save_data(data)
    return product

def update_supply_product(product_id, name, spec, unit_price):
    data = load_data()
    for product in data["supply_products"]:
        if product["id"] == product_id:
            product["name"] = name
            product["spec"] = spec
            product["unit_price"] = int(unit_price)
            product["updated_at"] = datetime.now().isoformat()
            save_data(data)
            return product
    return None

def delete_supply_product(product_id):
    data = load_data()
    data["supply_products"] = [p for p in data["supply_products"] if p["id"] != product_id]
    save_data(data)

def get_supply_products():
    data = load_data()
    return data.get("supply_products", [])

def get_supply_product_by_name(name):
    products = get_supply_products()
    for product in products:
        if product["name"] == name:
            return product
    return None


def add_uniform_product(name, unit_price):
    data = load_data()
    product = {
        "id": str(uuid.uuid4()),
        "name": name,
        "unit_price": int(unit_price),
        "created_at": datetime.now().isoformat()
    }
    data["uniform_products"].append(product)
    save_data(data)
    return product

def update_uniform_product(product_id, name, unit_price):
    data = load_data()
    for product in data["uniform_products"]:
        if product["id"] == product_id:
            product["name"] = name
            product["unit_price"] = int(unit_price)
            product["updated_at"] = datetime.now().isoformat()
            save_data(data)
            return product
    return None

def delete_uniform_product(product_id):
    data = load_data()
    data["uniform_products"] = [p for p in data["uniform_products"] if p["id"] != product_id]
    save_data(data)

def get_uniform_products():
    data = load_data()
    return data.get("uniform_products", [])

def get_uniform_product_by_name(name):
    products = get_uniform_products()
    for product in products:
        if product["name"] == name:
            return product
    return None
