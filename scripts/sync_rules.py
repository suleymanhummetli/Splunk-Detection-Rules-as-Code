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

    for filename in os.listdir("rules"):
        if filename.endswith(".json"):
            with open(os.path.join("rules", filename), "r") as f:
                rule = json.load(f)
                rule_name = rule['name']
                print(f"Sinxronizasiya edilir: {rule_name}...")

                payload = {
                    "search": rule['search'],
                    "description": rule['description'],
                    "cron_schedule": rule['cron_schedule'],
                    "is_scheduled": "1",
                    "disabled": "0",
                    "alert_type": "always",
                    "alert.track": "1",
                    "dispatch.earliest_time": rule['earliest_time'],
                    "dispatch.latest_time": rule['latest_time'],
                    "actions": "webhook",
                    "request.ui_dispatch_app": "search"
                }

                # 1. ADDIM: Köhnə qaydanı SİL (Conflict-i aradan qaldırmaq üçün)
                delete_url = f"{API_URL}/{rule_name}"
                requests.delete(delete_url, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)

                # 2. ADDIM: Qaydanı TƏMİZ şəkildə YARAT
                res = requests.post(API_URL, data={"name": rule_name, **payload}, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)

                if res.status_code in [200, 201]:
                    # 3. ADDIM: PAYLAŞIMI (Sharing) GLOBAL ET
                    acl_url = f"{delete_url}/acl"
                    acl_payload = {"sharing": "app", "owner": "nobody"}
                    acl_res = requests.post(acl_url, data=acl_payload, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)
                    
                    if acl_res.status_code == 200:
                        print(f"+++ MÜKƏMMƏL: {rule_name} (Aktiv və Paylaşıldı)")
                    else:
                        print(f"--- ACL Xətası: {rule_name} - {acl_res.status_code}")
                else:
                    print(f"!!! Yaratma Xətası: {rule_name} - {res.text}")

if __name__ == "__main__":
    sync_rules()
