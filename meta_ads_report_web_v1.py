import streamlit as st
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import pandas as pd
import time

# إعدادات Meta API
access_token = 'EAAOg2EgbGsgBOyaRnyGXZAR7AgrUXFZCRAR5MXmpZAOA7fNhZAMoeaRP3BvhbmDzjhv1L9eFIovmmcRRLg9gEt6ZAuRqprr1WZAME3I7ZBlREUeEU4fU8EoGlV4QVBtVSyrWhMdynNOl0oZBXZBbBIYIYaLr1UqQv03gBM6N7ZBe9zdlQ30mtTuV6aqkBsBwrOxNDNEwZDZD'
app_secret = '5f04c6be4ab4181e94aa1b00a361f180'
app_id = '1021275713247944'
FacebookAdsApi.init(app_id, app_secret, access_token)

# إعداد حسابات الإعلانات
ad_accounts = [
    {'id': 'act_496852558893864', 'name': 'Second Account 5864'},
    {'id': 'act_1226225747935657', 'name': 'Main Account 5657'},
    {'id': 'act_1570107520239729', 'name': 'Third Account 9729'},
    {'id': 'act_1360683711884654', 'name': 'Fourth Account 4654'}
]

# إعداد الاتصال بـ Google Sheets
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
spreadsheet = client.open("Meta Ads Report")
sheet = spreadsheet.worksheet("Sheet1")

# تهيئة البيانات للكتابة
headers = ['Ad Account', 'Campaign', 'Date', 'Cost', 'Imp.', 'Reach', 'Click', 'Link Click', 'Messages Started']

def fetch_data(mode):
    today = datetime.today()

    if mode == 'full':
        start_date = datetime(today.year, today.month, 1)
        end_date = today - timedelta(days=1)
    elif mode == 'last2':
        start_date = today - timedelta(days=2)
        end_date = today - timedelta(days=1)
    else:
        st.error("❌ Invalid mode")
        return

    all_days = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d')
                for i in range((end_date - start_date).days + 1)]

    rows = []
    for acc in ad_accounts:
        st.write(f"📊 Fetching for {acc['name']} ({len(all_days)} days)...")
        account = AdAccount(acc['id'])
        fields = [
            'date_start',
            'campaign_name',
            'spend',
            'impressions',
            'reach',
            'clicks',
            'actions'
        ]
        for date_str in all_days:
            params = {
                'time_range': {'since': date_str, 'until': date_str},
                'level': 'campaign',
                'time_increment': 1,
                'limit': 100
            }
            try:
                insights = account.get_insights(fields=fields, params=params)
                for camp in insights:
                    spend = float(camp.get('spend', 0))
                    if spend == 0:
                        continue
                    campaign_name = camp.get('campaign_name', 'N/A')
                    clicks = int(camp.get('clicks', 0))
                    impressions = int(camp.get('impressions', 0))
                    reach = int(camp.get('reach', 0))
                    link_clicks = 0
                    messages_started = 0
                    if 'actions' in camp:
                        for action in camp['actions']:
                            if action['action_type'] == 'link_click':
                                link_clicks = int(action['value'])
                            if action['action_type'] == 'onsite_conversion.messaging_conversation_started_7d':
                                messages_started = int(action['value'])
                    rows.append([
                        acc['name'],
                        campaign_name,
                        camp['date_start'],
                        spend,
                        impressions,
                        reach,
                        clicks,
                        link_clicks,
                        messages_started
                    ])
                    st.write(f"✔️ {acc['name']} | {campaign_name} | {camp['date_start']}")
            except Exception as e:
                st.warning(f"⚠️ Error for {acc['name']} on {date_str}: {e}")
        time.sleep(15)

    sheet.clear()
    sheet.append_row(headers)
    if rows:
        sheet.append_rows(rows)
        st.success(f"✅ Appended {len(rows)} rows.")
    else:
        st.info("🟡 No data to append.")

# واجهة Streamlit
st.title("📈 Meta Ads Report Updater")

if st.button("📅 تحديث كامل للشهر"):
    fetch_data("full")

if st.button("📆 تحديث آخر يومين"):
    fetch_data("last2")
