import streamlit as st
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
from googlesearch import search
import time
from io import BytesIO

# --- Streamlit UI ---
st.set_page_config(page_title="Company Contact Scraper", layout="centered")
st.title("📞 Company Contact Scraper")
st.write("Upload an Excel file with company names to fetch websites, emails, and phone numbers.")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

# --- Helper Functions ---
def get_company_website(company_name):
    query = f"{company_name} official site"
    try:
        for url in search(query, num=1, stop=1, pause=2):
            return url
    except Exception:
        return None

def extract_contacts(url):
    emails, phones = set(), set()
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text))
            phones = set(re.findall(r'\+?\d{1,4}?[ \s.-]?\(?\d{2,4}\)?[ \s.-]?\d{3,4}[ \s.-]?\d{3,4}', text))
    except Exception:
        pass
    return list(emails), list(phones)

# --- Main Logic ---
if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        company_column = df.columns[0]

        df['Website'] = ''
        df['Emails'] = ''
        df['Phones'] = ''

        progress = st.progress(0)
        status_text = st.empty()

        for i, company in enumerate(df[company_column]):
            status_text.text(f"🔍 Processing {i+1}/{len(df)}: {company}")
            website = get_company_website(company)
            df.at[i, 'Website'] = website if website else 'Not Found'
            if website:
                emails, phones = extract_contacts(website)
                df.at[i, 'Emails'] = ', '.join(emails)
                df.at[i, 'Phones'] = ', '.join(phones)
            progress.progress((i + 1) / len(df))
            time.sleep(1)  # Delay to prevent getting blocked

        status_text.text("✅ Scraping Complete!")
        st.write(df)

        # Downloadable Excel file
        @st.cache_data
        def convert_df(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            return output.getvalue()

        output_data = convert_df(df)
        st.download_button(
            label="📥 Download Results as Excel",
            data=output_data,
            file_name='Company_Contacts.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        st.error(f"⚠️ Error processing file: {e}")
