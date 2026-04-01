import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SPLUNK_HOST = os.environ.get('SPLUNK_HOST', '13.60.84.204')
SPLUNK_PORT = "8089"
SPLUNK_USER = os.environ.get('SPLUNK_USER', 'hummatli')
SPLUNK_PASS = os.environ.get('SPLUNK_PASS')

# Əsas API URL
API_URL = f"https://{SPLUNK_HOST}:{SPLUNK_PORT}/servicesNS/hummatli/search/saved/searches"

def sync_rules():
    if not SPLUNK_PASS:
        print("XETA: SPLUNK_PASS tapilmadi!")
        return

    for filename in os.listdir("rules"):
        if filename.endswith(".json"):
            with open(os.path.join("rules", filename), "r") as f:
                rule = json.load(f)
                rule_name = rule['name']
                print(f"Sinxronizasiya edilir: {rule_name}...")

                # 1. ADDIM: Qaydanın özünü yenilə və ya yarat
                payload = {
                    "search": rule['search'],
                    "description": rule['description'],
                    "cron_schedule": rule['cron_schedule'],
                    "is_scheduled": "1",                 # Məcburi String "1"
                    "disabled": "0",                     # Aktiv olsun
                    "alert_type": "always",
                    "alert.track": "1",
                    "dispatch.earliest_time": rule['earliest_time'],
                    "dispatch.latest_time": rule['latest_time'],
                    "actions": "webhook",
                    "request.ui_dispatch_app": "search"
                }

                check_url = f"{API_URL}/{rule_name}"
                res = requests.post(check_url, data=payload, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)

                if res.status_code not in [200, 201]:
                    # Əgər yoxdursa, yaradırıq
                    res = requests.post(API_URL, data={"name": rule_name, **payload}, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)

                # 2. ADDIM: PAYLAŞIM VƏ CƏDVƏLİ MƏCBURİ AKTİV ET (ACL Update)
                # Bu hissə "Private" yazısını "App" edəcək və Scheduler-i işə salacaq
                acl_url = f"{check_url}/acl"
                acl_payload = {
                    "sharing": "app",
                    "owner": "hummatli",
                    "perms.read": "*",
                    "perms.write": "admin,hummatli"
                }
                acl_res = requests.post(acl_url, data=acl_payload, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)
                
                if res.status_code in [200, 201] and acl_res.status_code == 200:
                    print(f"+++ UGURLU: {rule_name} (Aktiv və Paylaşıldı)")
                else:
                    print(f"--- PROBLEM: {rule_name} - Search: {res.status_code}, ACL: {acl_res.status_code}")

if __name__ == "__main__":
    sync_rules()
