import os
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFİQURASİYA ---
SPLUNK_HOST = os.environ.get('SPLUNK_HOST', '13.60.84.204')
SPLUNK_PORT = "8089"
SPLUNK_USER = os.environ.get('SPLUNK_USER', 'admin') # Diqqət: 'hummatli' deyilse 'admin' yoxla
SPLUNK_PASS = os.environ.get('SPLUNK_PASS')

API_URL = f"https://{SPLUNK_HOST}:{SPLUNK_PORT}/servicesNS/nobody/search/saved/searches"

def sync_rules():
    if not SPLUNK_PASS:
        print("Xeta: SPLUNK_PASS tapilmadi! GitHub Secrets-i yoxla.")
        return

    # Rules qovluğunu yoxla
    rules_dir = "rules"
    if not os.path.exists(rules_dir):
        print(f"Xeta: '{rules_dir}' qovlugu tapilmadi!")
        return

    for filename in os.listdir(rules_dir):
        if filename.endswith(".json"):
            with open(os.path.join(rules_dir, filename), "r") as f:
                try:
                    rule = json.load(f)
                    rule_name = rule['name']
                    print(f"Sinxronizasiya edilir: {rule_name}...")

                    # PAYLOAD: Problemləri həll edən əsas hissə
                    payload = {
                        "search": rule['search'],
                        "description": rule.get('description', 'SOC Alert'),
                        "cron_schedule": rule.get('cron_schedule', '*/1 * * * *'),
                        "is_scheduled": "1",
                        "disabled": "0",
                        "alert_type": "number of events",
                        "alert_comparator": "greater than",
                        "alert_threshold": "0",
                        "alert.track": "1",
                        "dispatch.earliest_time": rule.get('earliest_time', '-1h'),
                        "dispatch.latest_time": rule.get('latest_time', 'now'),
                        "actions": "script", # MÜTLƏQ: 'webhook' deyil, 'script' olmalıdır
                        "action.script.filename": "sdp_ticket.py",
                        "alert.suppress": "0",
                        "alert.digest_mode": "0"
                    }

                    # 1. Köhnəni sil
                    delete_url = f"{API_URL}/{rule_name}"
                    requests.delete(delete_url, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)

                    # 2. Yenisini yarat
                    res = requests.post(API_URL, data={"name": rule_name, **payload}, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)

                    if res.status_code in [200, 201]:
                        # 3. Paylaşımı GLOBAL et
                        acl_url = f"{delete_url}/acl"
                        requests.post(acl_url, data={"sharing": "app", "owner": "nobody"}, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)
                        print(f"+++ MÜKƏMMƏL: {rule_name} (Aktiv edildi)")
                    else:
                        print(f"!!! Yaratma Xetasi: {rule_name} - {res.text}")
                except Exception as e:
                    print(f"!!! Fayl xetasi {filename}: {str(e)}")

if __name__ == "__main__":
    sync_rules()
