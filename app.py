import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
import os
from dotenv import load_dotenv
import time
import json
import re

# Load your secret API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------- HELPER FUNCTIONS ----------

def scrape_website_text(url):
    try:
        if not url.startswith('http'):
            url = 'http://' + url

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content')[:500]

        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if len(text) > 50:
                return text[:500]

        return "No descriptive text found on the homepage."

    except Exception as e:
        return f"Error scraping: {str(e)[:100]}"

def generate_icebreakers(company_name, contact_name, industry, website_summary):
    prompt = f"""
    You are a world-class sales copywriter and relationship builder.

    Company Name: {company_name}
    Contact First Name: {contact_name}
    Industry: {industry}
    Website Summary: {website_summary}

    Task: Write exactly 3 short, conversational, and highly personalized icebreaker sentences to start a cold email or LinkedIn DM to {contact_name}.

    Rules:
    1. Each sentence must reference a SPECIFIC detail from the website summary.
    2. Do not sell anything yet. Just show you did your research.
    3. Keep each under 15 words.
    4. Format the output as a JSON array of strings.

    Output ONLY a JSON array of exactly 3 strings, nothing else. Example: ["...", "...", "..."]
    """

    raw_content = None
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        raw_content = response.choices[0].message.content.strip()
        print(f"[generate_icebreakers] raw response for {company_name}: {raw_content}")

        cleaned = re.sub(r"^```(?:json)?|```$", "", raw_content, flags=re.MULTILINE).strip()

        icebreakers = json.loads(cleaned)
        return icebreakers
    except Exception as e:
        print(f"[generate_icebreakers] ERROR for {company_name}: {repr(e)}")
        print(f"[generate_icebreakers] raw_content was: {raw_content}")
        return [f"Error generating: {str(e)[:80]}", "Please check API key", "Or try again"]

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="AI Lead Converter - Turn Cold Leads into Warm Conversations",
    page_icon="🚀",
    layout="wide"
)

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        font-size: 3rem;
        margin: 0;
    }
    .main-header p {
        color: #f0f0f0;
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
    }
    .feature-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #666;
        border-top: 1px solid #ddd;
        margin-top: 2rem;
        background: #fafafa;
        border-radius: 0 0 10px 10px;
    }
    .footer a {
        color: #667eea;
        text-decoration: none;
        font-weight: 500;
    }
    .footer a:hover {
        color: #764ba2;
        text-decoration: underline;
    }
    .footer p:last-child {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #eee;
        font-size: 0.85rem;
        color: #888;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 0.5rem 0;
    }
    .metric-card h3 {
        color: #667eea;
        font-size: 2rem;
        margin: 0;
    }
    .metric-card p {
        color: #666;
        margin: 0.5rem 0 0 0;
    }
    .success-box {
        background: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("""
<div class="main-header">
    <h1>🚀 AI Lead Converter</h1>
    <p>Turn Cold Leads into Warm Conversations in Seconds</p>
</div>
""", unsafe_allow_html=True)

# ---------- VALUE PROPOSITION ----------
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="metric-card">
        <h3>📊 8+ Hours</h3>
        <p>Saved per week on manual research</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="metric-card">
        <h3>🎯 3x</h3>
        <p>Higher response rate with personalized outreach</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="metric-card">
        <h3>⚡ 2 Minutes</h3>
        <p>To convert 100 leads from cold to warm</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ---------- HOW IT WORKS ----------
st.subheader("📖 How It Works")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("""
    <div class="feature-box">
        <h4>1️⃣ Upload</h4>
        <p>Upload your leads CSV with company names, contacts, and websites</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="feature-box">
        <h4>2️⃣ Scrape</h4>
        <p>AI scrapes each company website to understand their business</p>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="feature-box">
        <h4>3️⃣ Personalize</h4>
        <p>GPT-4 writes 3 unique icebreakers tailored to each lead</p>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown("""
    <div class="feature-box">
        <h4>4️⃣ Download</h4>
        <p>Export the enhanced CSV ready for any CRM (GoHighLevel, HubSpot, Salesforce, and more)</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ---------- FILE UPLOAD SECTION ----------
st.subheader("📁 Upload Your Leads")

with st.expander("📋 **CSV Format Requirements**", expanded=True):
    st.markdown("""
    Your CSV **MUST** have these exact column headers:
    
    | Column Name | Description | Example |
    |-------------|-------------|---------|
    | `Company Name` | Full company name | `OpenAI` |
    | `Contact First Name` | Contact's first name | `Sam` |
    | `Industry` | Industry they operate in | `AI Technology` |
    | `Website` | Company website URL | `openai.com` |

    **⚠️ You must also include an `Email` and/or `Phone` column** — most CRMs require at least one to create a contact.

    **✅ All other columns (Address, etc.) will be preserved!**
    """)

uploaded_file = st.file_uploader(
    "Choose your Leads CSV file",
    type=['csv'],
    help="Upload a CSV file with your leads. Maximum 200MB."
)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Show all columns
    with st.expander("📋 **Columns Detected in Your CSV**", expanded=False):
        st.write("**Original columns:**")
        for col in df.columns:
            st.write(f"- `{col}`")
        st.write("\n**New columns that will be added:**")
        st.write("- `Icebreaker_1`, `Icebreaker_2`, `Icebreaker_3`")
        st.write("- `Website_Scraped_Text`")
    
    # Validate required columns
    required_cols = ['Company Name', 'Contact First Name', 'Industry', 'Website']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
        st.info("Please update your CSV to include these columns.")
        st.stop()

    # Most CRMs require Email or Phone to create a contact - make sure at least one column exists
    contact_cols = [col for col in ['Email', 'Phone'] if col in df.columns]
    if not contact_cols:
        st.error("❌ Missing 'Email' and/or 'Phone' column. Most CRMs require at least one to create a contact.")
        st.info("Please add an 'Email' or 'Phone' column to your CSV.")
        st.stop()

    # Flag rows where every contact column is empty for that row
    missing_contact_mask = df[contact_cols].isna().all(axis=1) | (df[contact_cols].astype(str).apply(lambda col: col.str.strip()).eq("").all(axis=1))
    rows_missing_contact = int(missing_contact_mask.sum())
    if rows_missing_contact > 0:
        st.warning(f"⚠️ {rows_missing_contact} lead(s) have no Email or Phone and may fail to import into your CRM.")

    st.success(f"✅ CSV loaded successfully! {len(df)} leads found.")
    
    with st.expander("📊 Preview your data", expanded=True):
        st.dataframe(df)
    
    # The big "START" button
    if st.button("🔥 Generate Icebreakers for ALL Leads", type="primary"):
        progress_bar = st.progress(0, text="0%")
        status_text = st.empty()
        
        # Add new columns for icebreakers (keep ALL existing columns)
        df['Icebreaker_1'] = ""
        df['Icebreaker_2'] = ""
        df['Icebreaker_3'] = ""
        df['Website_Scraped_Text'] = ""
        
        total_leads = len(df)
        
        for index, row in df.iterrows():
            status_text.text(f"Processing {row['Contact First Name']} from {row['Company Name']}... ({index+1}/{total_leads} — {int((index / total_leads) * 100)}%)")
            
            scraped_text = scrape_website_text(row['Website'])
            df.at[index, 'Website_Scraped_Text'] = scraped_text
            
            if "Error" not in scraped_text and len(scraped_text) > 20:
                icebreakers = generate_icebreakers(
                    row['Company Name'],
                    row['Contact First Name'],
                    row['Industry'],
                    scraped_text
                )
                
                if len(icebreakers) == 3:
                    df.at[index, 'Icebreaker_1'] = icebreakers[0]
                    df.at[index, 'Icebreaker_2'] = icebreakers[1]
                    df.at[index, 'Icebreaker_3'] = icebreakers[2]
                else:
                    df.at[index, 'Icebreaker_1'] = "Failed to generate"
                    df.at[index, 'Icebreaker_2'] = "Failed to generate"
                    df.at[index, 'Icebreaker_3'] = "Failed to generate"
            else:
                df.at[index, 'Icebreaker_1'] = "Scrape failed - check URL"
                df.at[index, 'Icebreaker_2'] = "Scrape failed - check URL"
                df.at[index, 'Icebreaker_3'] = "Scrape failed - check URL"
            
            percent_complete = (index + 1) / total_leads
            progress_bar.progress(percent_complete, text=f"{int(percent_complete * 100)}%")
            time.sleep(0.5)

        status_text.text("✅ Processing Complete!")
        
        st.subheader("📊 Your Enhanced Lead List")
        st.dataframe(df)
        
        st.info(f"📋 Total columns: {len(df.columns)} (Original columns preserved + 4 new AI-generated columns)")
        
        csv_output = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Enhanced CSV for Your CRM",
            data=csv_output,
            file_name="leads_with_icebreakers.csv",
            mime="text/csv",
            type="primary"
        )

        st.balloons()
        st.success("🎉 Done! Upload this CSV to your CRM and start your campaign.")

# ---------- FOOTER ----------
st.markdown("""
<div class="footer">
    <p>🚀 Built by Zeeshan Elahi | Software Engineer | MERN Stack Developer | AI Automation Engineer</p>
    <p style="font-size: 0.9rem;">
        📧 <a href="mailto:zeeshanelahi104@gmail.com">zeeshanelahi104@gmail.com</a> | 
        🔗 <a href="https://www.linkedin.com/in/zeeshan-elahi-818zl942" target="_blank">LinkedIn</a> | 
        💼 <a href="https://github.com/zeeshanelahi104" target="_blank">GitHub</a> |
        🌐 <a href="https://zeeshan-elahi.vercel.app" target="_blank">Portfolio</a>
    </p>
    <p style="font-size: 0.8rem; color: #999;">
        Need a custom automation? I build AI-powered solutions for businesses like yours.
    </p>
</div>
""", unsafe_allow_html=True)

