import os
import json
import requests
import urllib3

# Təhlükəsizlik xəbərdarlıqlarını söndürürük (SSL sertifikatı yoxdursa)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Splunk Məlumatları (Bunlar sonra GitHub Secrets-ə qoyulacaq)
SPLUNK_HOST = os.environ.get('SPLUNK_HOST', '13.60.84.204') # Sənin Splunk İP-n
SPLUNK_PORT = "8089"
SPLUNK_USER = os.environ.get('SPLUNK_USER', 'hummatli')
SPLUNK_PASS = os.environ.get('SPLUNK_PASS')

RULES_DIR = "rules"
API_URL = f"https://{SPLUNK_HOST}:{SPLUNK_PORT}/servicesNS/hummatli/search/saved/searches"

def sync_rules():
    if not SPLUNK_PASS:
        print("Xəta: SPLUNK_PASS tapılmadı!")
        return

    # Rules qovluğundakı bütün .json fayllarını tapırıq
    for filename in os.listdir(RULES_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(RULES_DIR, filename), "r") as f:
                rule_data = json.load(f)
                
                print(f"Syncing: {rule_data['name']}...")
                
                # Splunk API-nə göndəriləcək parametrlər
                payload = {
                    "name": rule_data['name'],
                    "search": rule_data['search'],
                    "description": rule_data['description'],
                    "cron_schedule": rule_data['cron_schedule'],
                    "is_scheduled": 1,
                    "dispatch.earliest_time": rule_data['earliest_time'],
                    "dispatch.latest_time": rule_data['latest_time'],
                    "actions": "webhook", # Ehtiyac olsa bura telegram da əlavə edilə bilər
                    "output_mode": "json"
                }

                # Əvvəlcə yoxlayırıq, bu adda rule varmı?
                check_url = f"{API_URL}/{rule_data['name']}"
                response = requests.get(check_url, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)

                if response.status_code == 200:
                    # Varsa - Update (POST)
                    print(f"Rule '{rule_data['name']}' artıq var. Yenilənir (Update)...")
                    res = requests.post(check_url, data=payload, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)
                else:
                    # Yoxdursa - Create (POST)
                    print(f"Rule '{rule_data['name']}' yaradılır (Create)...")
                    res = requests.post(API_URL, data=payload, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)

                if res.status_code in [200, 201]:
                    print(f"Uğurlu: {rule_data['name']}")
                else:
                    print(f"Xəta: {rule_data['name']} - {res.text}")

if __name__ == "__main__":
    sync_rules()
