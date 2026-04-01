import os
import json
import requests
import urllib3

# SSL sertifikatı xətalarını görməzdən gəlirik
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Parametrlər (GitHub Secrets-dən gəlir)
SPLUNK_HOST = os.environ.get('SPLUNK_HOST', '13.60.84.204')
SPLUNK_PORT = "8089"
SPLUNK_USER = os.environ.get('SPLUNK_USER', 'hummatli')
SPLUNK_PASS = os.environ.get('SPLUNK_PASS')

# Splunk-da 'hummatli' istifadəçisinin 'search' tətbiqi sahəsi
API_URL = f"https://{SPLUNK_HOST}:{SPLUNK_PORT}/servicesNS/hummatli/search/saved/searches"

def sync_rules():
    if not SPLUNK_PASS:
        print("Xeta: SPLUNK_PASS environment variable tapilmadi!")
        return

    rules_dir = "rules"
    if not os.path.exists(rules_dir):
        print(f"Xeta: '{rules_dir}' qovlugu tapilmadi!")
        return

    for filename in os.listdir(rules_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(rules_dir, filename)
            with open(file_path, "r") as f:
                try:
                    rule_data = json.load(f)
                    rule_name = rule_data.get('name')
                except Exception as e:
                    print(f"Xeta: {filename} oxunarkən problem: {e}")
                    continue

                print(f"Syncing: {rule_name}...")

                # MÜHÜM: Bütün rəqəmlər və bool-lar string ("1") olmalıdır
                payload = {
                    "search": rule_data['search'],
                    "description": rule_data['description'],
                    "cron_schedule": rule_data['cron_schedule'],
                    "is_scheduled": "1",                 # Timer-i aktiv edir (None-u düzəldir)
                    "alert_type": "always",              # Həmişə işləsin
                    "alert.track": "1",                  # Triggered Alerts siyahısında görünsün
                    "dispatch.earliest_time": rule_data['earliest_time'],
                    "dispatch.latest_time": rule_data['latest_time'],
                    "actions": "webhook",                # Email xətasına görə yalnız webhook saxladıq
                    "request.ui_dispatch_app": "search",
                    "output_mode": "json"
                }

                # Qaydanın hədəf URL-i
                check_url = f"{API_URL}/{rule_name}"
                
                # Əvvəlcə Update etməyə çalışırıq
                res = requests.post(check_url, data=payload, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)

                if res.status_code in [200, 201]:
                    print(f"--- YENILENDI (Update): {rule_name}")
                    # PAYLAŞIM (ACL) tənzimləməsi - Hamı görə bilsin deyə
                    acl_url = f"{check_url}/acl"
                    requests.post(acl_url, data={"sharing": "app", "owner": "hummatli"}, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)
                
                elif res.status_code == 404:
                    # Əgər qayda yoxdursa, yeni yaradırıq
                    create_payload = {"name": rule_name, **payload}
                    create_res = requests.post(API_URL, data=create_payload, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)
                    
                    if create_res.status_code in [200, 201]:
                        print(f"+++ YARADILDI (Create): {rule_name}")
                        # Yeni yaradılan qayda üçün də paylaşımı aktiv edirik
                        requests.post(f"{check_url}/acl", data={"sharing": "app", "owner": "hummatli"}, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)
                    else:
                        print(f"!!! XETA (Yaratma): {rule_name} - {create_res.text}")
                else:
                    print(f"!!! XETA (Update): {rule_name} - {res.text}")

if __name__ == "__main__":
    sync_rules()
