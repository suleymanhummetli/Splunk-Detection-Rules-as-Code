import os, json, requests, urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SPLUNK_HOST = os.environ.get('SPLUNK_HOST', '13.60.84.204')
SPLUNK_USER = os.environ.get('SPLUNK_USER', 'admin') # 'admin' daha stabil işləyir
SPLUNK_PASS = os.environ.get('SPLUNK_PASS')
API_URL = f"https://{SPLUNK_HOST}:8089/servicesNS/nobody/search/saved/searches"

def sync_rules():
    if not SPLUNK_PASS: return
    for filename in os.listdir("rules"):
        if filename.endswith(".json"):
            with open(os.path.join("rules", filename), "r") as f:
                rule = json.load(f)
                name = rule['name']
                print(f"Sinxronizasiya: {name}...")

                payload = {
                    "search": rule['search'],
                    "description": rule['description'],
                    "cron_schedule": rule['cron_schedule'],
                    "is_scheduled": "1",
                    "disabled": "0",
                    "alert_type": "number of events",
                    "alert_comparator": "greater than",
                    "alert_threshold": "0",
                    "alert.track": "1",
                    "dispatch.earliest_time": rule['earliest_time'],
                    "dispatch.latest_time": rule['latest_time'],
                    "alert.suppress": "0",
                    "alert.digest_mode": "0",
                    "actions": "script",
                    "action.script.filename": "sdp_ticket.py"
                }
                # Köhnəni sil və yenisini təmiz yarat
                requests.delete(f"{API_URL}/{name}", auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)
                res = requests.post(API_URL, data={"name": name, **payload}, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)
                
                if res.status_code in [200, 201]:
                    requests.post(f"{API_URL}/{name}/acl", data={"sharing": "app", "owner": "nobody"}, auth=(SPLUNK_USER, SPLUNK_PASS), verify=False)
                    print(f"+++ UĞURLU: {name}")

if __name__ == "__main__": sync_rules()
