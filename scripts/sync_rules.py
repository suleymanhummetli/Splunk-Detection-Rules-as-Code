import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SPLUNK_HOST = os.environ.get('SPLUNK_HOST', '13.60.84.204')
SPLUNK_PORT = "8089"
SPLUNK_USER = os.environ.get('SPLUNK_USER', 'hummatli')
SPLUNK_PASS = os.environ.get('SPLUNK_PASS')

# Peşəkar standart: nobody (Global) namespace
API_URL = f"https://{SPLUNK_HOST}:{SPLUNK_PORT}/servicesNS/nobody/search/saved/searches"

def sync_rules():
    if not SPLUNK_PASS:
        print("Xeta: SPLUNK_PASS tapilmadi!")
        return

    rules_dir = "rules"
    for filename in os.listdir(rules_dir):
        if filename.endswith(".json"):
            with open(os.path.join(rules_dir, filename), "r") as f:
                rule = json.load(f)
                rule_name = rule['name']
                print(f"Sinxronizasiya edilir: {rule_name}...")

                # PAYLOAD DÜZƏLİŞİ: Bütün problemləri burada həll edirik
                payload = {
                    "search": rule['search'],
                    "description": rule.get('description', 'SOC Automation'),
                    "cron_schedule": rule.get('cron_schedule', '*/1 * * * *'),
                    "is_scheduled": "1",
                    "disabled": "0",
                    "alert_type": "number of events",
                    "alert_comparator": "greater than",
                    "alert_threshold": "0",
                    "alert.track": "1",
                    "dispatch.earliest_time": rule.get('earliest_time', 'rt-1h'),
                    "dispatch.latest_time": rule.get('latest_time', 'rt'),
                    
                    # --- BİZİM ÜÇÜN KRİTİK OLAN HİSSƏ ---
                    "actions": "script", # Webhook yerinə SCRIPT etdik
                    "action.script.filename": rule.get('action.script.filename', 'sdp_ticket.py'),
                    "alert.digest_mode": "0", # Per-Result rejimini aktiv edir
                    "alert.suppress": "0",    # Boğmanı (Throttle) söndürür
                    "request.ui_dispatch_app": "search"
                }

                # 1. ADDIM: Köhnə qaydanı SİL
                delete_url = f"{API_URL}/{rule_name}"
                requests.delete(delete_url, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)

                # 2. ADDIM: Qaydanı TƏMİZ şəkildə YARAT
                res = requests.post(API_URL, data={"name": rule_name, **payload}, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)

                if res.status_code in [200, 201]:
                    # 3. ADDIM: PAYLAŞIMI GLOBAL ET
                    acl_url = f"{delete_url}/acl"
                    acl_payload = {"sharing": "app", "owner": "nobody"}
                    acl_res = requests.post(acl_url, data=acl_payload, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)
                    
                    if acl_res.status_code == 200:
                        print(f"+++ MÜKƏMMƏL: {rule_name} (Boğma Söndürüldü və Bilet Skripti Qoşuldu)")
                    else:
                        print(f"--- ACL Xətası: {rule_name} - {acl_res.status_code}")
                else:
                    print(f"!!! Yaratma Xətası: {rule_name} - {res.text}")

if __name__ == "__main__":
    sync_rules()
