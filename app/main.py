import json
import os #to mess with env vars
from pathlib import Path
from typing import Any, Dict, List, Optional

import pymysql
from flask import Flask, jsonify, request 

#Flask app
app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent #function to find parent folder for current dir
DATA_DIR = BASE_DIR / "data" # where the data jsons are stored with pay info

# Opens full pay-table data for officer, enlisted, and warrant
with open(DATA_DIR / "pay_tables_full.json", "r", encoding="utf-8") as f:
    PAY_TABLES = json.load(f) #dictionary

# Opens the separate BAH data file, need to update*********************************************
with open(DATA_DIR / "bah_rates_separate.json", "r", encoding="utf-8") as f:
    BAH_DATA = json.load(f)

#List of years of service for the frontend to select
YOS_RANGES = [
    ("2_or_less", 0),
    ("over_2", 2),
    ("over_3", 3),
    ("over_4", 4),
    ("over_6", 6),
    ("over_8", 8),
    ("over_10", 10),
    ("over_12", 12),
    ("over_14", 14),
    ("over_16", 16),
    ("over_18", 18),
    ("over_20", 20),
    ("over_22", 22),
    ("over_24", 24),
    ("over_26", 26),
    ("over_28", 28),
    ("over_30", 30),
    ("over_32", 32),
    ("over_34", 34),
    ("over_36", 36),
    ("over_38", 38),
    ("over_40", 40),
]

#Flask runs function after each http response
@app.after_request

# "Cross-Origin Resource Sharing" for accessing diff ports 
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"#allows requests from all origins
    response.headers["Access-Control-Allow-Methods"] = "*"#allows requests from all http methods
    response.headers["Access-Control-Allow-Headers"] = "*"#allows requests from all headers
    return response

# This function opens a new MySQL connection using environment variables from docker-compose.
def get_connection():
    # This line returns a live database connection object.
    return pymysql.connect(
        host=os.getenv("DB_HOST", "db"),#default db
        user=os.getenv("DB_USER", "budgetuser"),# default budgetuser
        password=os.getenv("DB_PASSWORD", "budgetpass"),# default bugdetpass
        database=os.getenv("DB_NAME", "budgetdb"),# default budgetdb
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )

def db_execute(sql: str, params=None, fetchone: bool = False, fetchall: bool = False): #runs mySQL, returns rows
    connection = get_connection()
    with connection.cursor() as cursor:
        cursor.execute(sql, params or ())
        result = None # rows
        if fetchone:
            result = cursor.fetchone()#read a row
        if fetchall:
            result = cursor.fetchall()#read all rows
    connection.close()
    return result

def to_number(value: Any) -> float: #convert value to num, sanitize input
    try:
        return float(value or 0)
    except Exception:
        return 0.0 #base case

# Determines which pay table to use
def get_pay_table_group(pay_grade: str) -> str:

    if str(pay_grade).startswith("O-"):
        return "officer" 

    if str(pay_grade).startswith("W-"):
        return "warrant"

    return "enlisted" 

# Converts years of service num to pay-table range
def normalize_yos_range(years_of_service: int) -> str:
    selected = "2_or_less"
    for label, threshold in YOS_RANGES: #loop through list to find right range for pay
        if years_of_service > threshold or (label == "2_or_less" and years_of_service <= 2):
            selected = label

    return selected

# Looks up base pay from table under data folder
def get_base_pay(pay_grade: str, years_of_service: int) -> float:

    group = get_pay_table_group(pay_grade) #grab right pay table group

    range = normalize_yos_range(years_of_service)
    
    pay_row = PAY_TABLES.get(group, {}).get(pay_grade, {})#pay row for selected pay grade

    if range in pay_row: 
        return round(float(pay_row[range]), 2) # exact range val

    last_value = 0.0 
    for label, _threshold in YOS_RANGES: #if a range is not explicit, determines last range

        if label in pay_row:
            last_value = float(pay_row[label])

        if label == range:
            break # Correct range for pay found
    return round(last_value, 2)

# Grabs BAS from file
def get_bas(pay_grade: str) -> float:
    latest_date = sorted(PAY_TABLES["bas_history"].keys())[-1]
    bas_row = PAY_TABLES["bas_history"][latest_date]#reads the BAS row for that latest date.

    #Officer BAS for officers and enlisted BAS for everyone else.
    return float(bas_row["officers"] if str(pay_grade).startswith("O-") else bas_row["enlisted"])

# This function returns a sorted list of available BAH locations from the external BAH file.
def get_location_list() -> List[Dict[str, str]]:
    items = []

    for year_key, year_rows in BAH_DATA.items():
        if year_key == "_meta":
            continue
        #Loops each location row for the year.
        for code, row in year_rows.items():
            items.append({
                "label": row.get("mha_name", code),
                "code": code,
                "year": year_key
            })
    #Sorts the locations by label and code and returns them.
    return sorted(items, key=lambda x: (x["label"], x["code"]))

# Find BAH row by name of location instead of location code.
def find_location_record(location_label: str) -> Optional[Dict[str, Any]]:

    target = (location_label or "").strip().lower()
    if not target:#no location given
        return None

    for year_key, year_rows in BAH_DATA.items():
        if year_key == "_meta":
            continue
        for code, row in year_rows.items():#each location row
            label = str(row.get("mha_name", "")).strip().lower()#label name in BAH row

            if target == label or target == str(code).strip().lower(): #matches label name to code
                return {
                    "year": year_key,
                    "code": code,
                    "label": row.get("mha_name", code),
                    "row": row
                }
    return None

def bah_grade_key(pay_grade: str) -> str:
    # E-5 -> E5; O-3 -> O3
    return str(pay_grade).replace("-", "")

# Looks up BAH
def get_bah(location_label: str, has_dependents: str, pay_grade: str, bah_override: Optional[float]) -> Dict[str, Any]:
    
    if bah_override not in (None, "", 0): #exact BAH entered, so function override
        return {
            "amount": round(float(bah_override), 2),
            "location_label": location_label or "",
            "location_code": "",
            "source": "override"
        }
    # Looks up matching location from the BAH file.
    match = find_location_record(location_label)
    if not match:
        return {
            "amount": 0.0,
            "location_label": location_label or "",
            "location_code": "",
            "source": "not_found"
        }
    dep_key = "with_dependents" if str(has_dependents).lower() == "yes" else "without_dependents"
    rates = match["row"].get(dep_key, {}) #rate table for dependents

    lookup_grade = bah_grade_key(pay_grade)

    amount = float(rates.get(lookup_grade, 0.0))#matches to pay grade
    return {
        "amount": round(amount, 2),
        "location_label": match["label"],
        "location_code": match["code"],
        "source": "bah_file"
    }

# Monthly federal income tax based on annual brackets
def estimate_federal_monthly(annual_taxable: float, filing_status: str) -> float:

    federal_brackets = { # yay taxes
        "single": [(12400, 0.10), (50400, 0.12), (105700, 0.22), (201775, 0.24), (256225, 0.32), (640600, 0.35), (10**12, 0.37)],
        "married": [(24800, 0.10), (100800, 0.12), (211400, 0.22), (403550, 0.24), (512450, 0.32), (768700, 0.35), (10**12, 0.37)],
        "hoh": [(17700, 0.10), (67450, 0.12), (105700, 0.22), (201750, 0.24), (256200, 0.32), (640600, 0.35), (10**12, 0.37)],
    }
    #Tax deductions
    standard_deduction = {"single": 16100, "married": 32200, "hoh": 24150}

    #after deductions
    taxable = max(annual_taxable - standard_deduction.get(filing_status, 16100), 0)
    tax = 0.0
    last = 0.0
    #loop for current tax bracket, MAJ Gee had to explain to me before how tax brackets worked
    for ceiling, rate in federal_brackets.get(filing_status, federal_brackets["single"]):

        amount = min(taxable, ceiling) - last #how much income falls into bracket

        if amount > 0: #if income falls into bracket
            tax += amount * rate

        last = ceiling #for next bracket

        if taxable <= ceiling:
            break

    return round(tax / 12.0, 2)# Monthly tax

#FICA withholding
def estimate_fica_monthly(annual_taxable: float) -> float:
    ss_taxable = min(annual_taxable, 184500)
    ss = ss_taxable * 0.062 #annual social security withholding
    return round(ss / 12.0, 2)

# Estimates monthly state tax using rate table.
def estimate_state_monthly(annual_taxable: float, state: str) -> float:
    state_rates = {"AK": 0.0, "FL": 0.0, "NV": 0.0, "NH": 0.0, "SD": 0.0, "TN": 0.0, "TX": 0.0, "WA": 0.0, "WY": 0.0, "CA": 0.07, "NY": 0.06, "VA": 0.05, "NC": 0.0425, "PA": 0.0307}

    rate = state_rates.get((state or "").upper(), 0.04)# if for some reason no state, 4% default
    taxable = max(annual_taxable - 5000, 0)

    return round((taxable * rate) / 12.0, 2)# monthly

# Builds the budget response shown on the website frontend
def build_budget(row: Dict[str, Any]) -> Dict[str, Any]:
    base_pay = to_number(row["base_pay"])
    bas = to_number(row["bas"])
    bah = to_number(row["bah"])
    special_pay = to_number(row["special_pay"])
    other_taxable = to_number(row["other_taxable"])
    other_nontaxable = to_number(row["other_nontaxable"])
    
    #Annual taxable income from monthly taxable items.
    annual_taxable = (base_pay + special_pay + other_taxable) * 12
    federal_tax = estimate_federal_monthly(annual_taxable, row["filing_status"])
    fica = estimate_fica_monthly(annual_taxable)
    state_tax = estimate_state_monthly(annual_taxable, row["resident_state"])
    
    #Gross monthly income.
    gross = round(base_pay + bas + bah + special_pay + other_taxable + other_nontaxable, 2)
    #Monthly costs out
    outflows = round(federal_tax + fica + state_tax + to_number(row["tsp"]) + to_number(row["allotments"]) + to_number(row["debts"]) + to_number(row["sgli"]), 2)
    #Monthly net pay.
    net = round(gross - outflows, 2)

    #Housing Budget is min of BAH vs 35% of net pay
    housing = round(min(bah, net * 0.35), 2)
    #Food budget as the min of BAS and 12% of net pay.
    food = round(min(bas, net * 0.12), 2)
    #Savings budget as the max of TSP and 10% of net pay
    savings = round(max(to_number(row["tsp"]), net * 0.10), 2)
    #Debt budget as the max of current debts and 5% of net pay
    debt = round(max(to_number(row["debts"]), net * 0.05), 2)
    #Money remaining after everything else
    remaining = round(net - housing - food - savings - debt, 2)

    #Half of money left over is expendable
    spending = max(round(remaining * 0.5, 2), 0)
    #everything else is for emergencies
    emergency = max(round(remaining - spending, 2), 0)

    return {
        "summary": {
            "name": row["name"],
            "branch": row["branch"],
            "pay_grade": row["pay_grade"],
            "years_of_service": row["years_of_service"],
            "resident_state": row["resident_state"],
            "duty_location": row["duty_location"],
            "duty_location_code": row["duty_location_code"],
            "base_pay": base_pay,
            "bas": bas,
            "bah": bah,
            "federal_tax": federal_tax,
            "fica": fica,
            "state_tax": state_tax,
            "net_pay": net
        },
        "budget": [
            {"category": "Housing", "amount": housing, "reason": "Anchored to BAH when available."},
            {"category": "Food", "amount": food, "reason": "Anchored to BAS when available."},
            {"category": "Savings / TSP", "amount": savings, "reason": "At least current TSP or 10% of net pay."},
            {"category": "Debt Paydown", "amount": debt, "reason": "Covers current debts or 5% of net pay."},
            {"category": "Emergency Fund", "amount": emergency, "reason": "Uses part of remaining pay as reserve."},
            {"category": "Flexible Spending", "amount": spending, "reason": "Remaining money for household and misc."}
        ]
    }

#route list of BAH locations for dropdown and search
@app.route("/locations", methods=["GET"])
def locations():
    # Location list as JSON.
    return jsonify(get_location_list())

#route for frontend to preview pay, BAS, and BAH
@app.route("/pay-lookup", methods=["POST"])
def pay_lookup():
    #reads the request JSON
    payload = request.get_json(force=True, silent=True) or {}
    pay_grade = payload.get("pay_grade", "E-5")
    years_of_service = int(payload.get("years_of_service", 6))
    duty_location = payload.get("duty_location", "")
    has_dependents = payload.get("has_dependents", "yes")
    bah_override = payload.get("bah_override")
    bah_result = get_bah(duty_location, has_dependents, pay_grade, bah_override)

    return jsonify({
        "base_pay": get_base_pay(pay_grade, years_of_service),
        "bas": get_bas(pay_grade),
        "bah": bah_result["amount"],
        "duty_location": bah_result["location_label"],
        "duty_location_code": bah_result["location_code"],
        "bah_source": bah_result["source"]
    })

#Route saves LES row and returns budget built
@app.route("/les", methods=["POST", "OPTIONS"])
def save_les():

    if request.method == "OPTIONS":
        return jsonify({"ok": True})
    
    # This line reads the JSON body from the request
    payload = request.get_json(force=True, silent=True) or {}
    #defaults set
    pay_grade = payload.get("pay_grade", "E-5")
    years_of_service = int(payload.get("years_of_service", 6))
    bah_result = get_bah(payload.get("duty_location", ""), payload.get("has_dependents", "yes"), pay_grade, payload.get("bah_override"))
    base_pay = get_base_pay(pay_grade, years_of_service)
    bas = get_bas(pay_grade)
    bah = bah_result["amount"]
    #MySQL statement inserts a new LES row.
    sql = (
        "INSERT INTO les_entries ("
        "name, branch, pay_grade, years_of_service, filing_status, resident_state, duty_location, duty_location_code, has_dependents, "
        "base_pay, bas, bah, special_pay, other_taxable, other_nontaxable, "
        "tsp, allotments, debts, sgli, notes"
        ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    params = (
        payload.get("name", "Service Member"),
        payload.get("branch", "Army"),
        pay_grade,
        years_of_service,
        payload.get("filing_status", "single"),
        payload.get("resident_state", "FL"),
        bah_result["location_label"],
        bah_result["location_code"],
        payload.get("has_dependents", "yes"),
        base_pay,
        bas,
        bah,
        to_number(payload.get("special_pay")),
        to_number(payload.get("other_taxable")),
        to_number(payload.get("other_nontaxable")),
        to_number(payload.get("tsp")),
        to_number(payload.get("allotments")),
        to_number(payload.get("debts")),
        to_number(payload.get("sgli")),
        payload.get("notes", "")
    )
    #Runs MySQL insert statement.
    db_execute(sql, params)
    #Finds newest row from database.
    row = db_execute("SELECT * FROM les_entries ORDER BY id DESC LIMIT 1", fetchone=True)

    if not row:
        return jsonify({"error": "database not ready"}), 503 #row not read

    return jsonify(build_budget(row))

@app.route("/budget", methods=["GET"])# Gets latest budget data
def latest_budget():
    row = db_execute("SELECT * FROM les_entries ORDER BY id DESC LIMIT 1", fetchone=True)#newest row
    if not row:
        return jsonify({"error": "no LES data yet"}), 404 #if nothing saved
    return jsonify(build_budget(row))#returns budget built

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)#runs on localhost:8080
