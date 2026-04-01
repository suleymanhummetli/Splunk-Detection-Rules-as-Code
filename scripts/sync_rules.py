import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SPLUNK_HOST = os.environ.get('SPLUNK_HOST', '13.60.84.204')
SPLUNK_PORT = "8089"
SPLUNK_USER = os.environ.get('SPLUNK_USER', 'hummatli')
SPLUNK_PASS = os.environ.get('SPLUNK_PASS')

# Qaydaların hara yazılacağı: hummatli istifadəçisinin search proqramı
API_URL = f"https://{SPLUNK_HOST}:{SPLUNK_PORT}/servicesNS/hummatli/search/saved/searches"

def sync_rules():
    if not SPLUNK_PASS:
        print("Xeta: SPLUNK_PASS tapilmadi!")
        return

    for filename in os.listdir("rules"):
        if filename.endswith(".json"):
            with open(os.path.join("rules", filename), "r") as f:
                rule = json.load(f)
                
                print(f"Syncing: {rule['name']}...")
                
                # Bu payload Splunk-a bütün lazım olanları deyir
                payload = {
                    "search": rule['search'],
                    "description": rule['description'],
                    "cron_schedule": rule['cron_schedule'],
                    "is_scheduled": 1,
                    "dispatch.earliest_time": rule['earliest_time'],
                    "dispatch.latest_time": rule['latest_time'],
                    "actions": "webhook",
                    "request.ui_dispatch_app": "search"
                }

                check_url = f"{API_URL}/{rule['name']}"
                res = requests.post(check_url, data=payload, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)

                if res.status_code in [200, 201]:
                    # PAYLAŞIM (Sharing) üçün əlavə zəng - BU ÇOX VACİBDİR
                    acl_url = f"{check_url}/acl"
                    acl_payload = {"sharing": "app", "owner": "hummatli"}
                    requests.post(acl_url, data=acl_payload, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)
                    print(f"UGURLU: {rule['name']}")
                else:
                    # Əgər qayda yoxdursa, yaradırıq
                    res = requests.post(API_URL, data={"name": rule['name'], **payload}, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)
                    print(f"YARADILDI: {rule['name']}")

if __name__ == "__main__":
    sync_rules()
