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
    """
    Tries to get the 'meta description' or page text from a website.
    """
    try:
        # Add http:// if missing
        if not url.startswith('http'):
            url = 'http://' + url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1st priority: Get the Meta Description (usually sums up the company best)
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content')[:500]  # Limit to 500 chars
        
        # 2nd priority: Get the first paragraph of text
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if len(text) > 50:  # Avoid tiny footer texts
                return text[:500]
        
        return "No descriptive text found on the homepage."
    
    except Exception as e:
        return f"Error scraping: {str(e)[:100]}"

def generate_icebreakers(company_name, contact_name, industry, website_summary):
    """
    Calls OpenAI to write 3 hyper-personalized icebreaker sentences.
    """
    prompt = f"""
    You are a world-class sales copywriter and relationship builder.
    
    Company Name: {company_name}
    Contact First Name: {contact_name}
    Industry: {industry}
    Website Summary: {website_summary}
    
    Task: Write exactly 3 short, conversational, and highly personalized icebreaker sentences to start a cold email or LinkedIn DM to {contact_name}.
    
    Rules:
    1. Each sentence must reference a SPECIFIC detail from the website summary (do not be generic).
    2. Do not sell anything yet. Just show you did your research.
    3. Keep each under 15 words.
    4. Format the output as a Python list of strings.
    
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

        # Strip markdown code fences if the model added them (```json ... ```)
        cleaned = re.sub(r"^```(?:json)?|```$", "", raw_content, flags=re.MULTILINE).strip()

        icebreakers = json.loads(cleaned)
        return icebreakers
    except Exception as e:
        print(f"[generate_icebreakers] ERROR for {company_name}: {repr(e)}")
        print(f"[generate_icebreakers] raw_content was: {raw_content}")
        return [f"Error generating: {str(e)[:80]}", "Please check API key", "Or try again"]

# ---------- THE STREAMLIT UI ----------

st.set_page_config(page_title="AI Lead Converter", layout="wide")
st.title("🚀 AI Lead Converter (CSV to Personalized Icebreakers)")
st.markdown("Upload your leads CSV. Get back a file with custom icebreakers ready for GoHighLevel.")

with st.expander("📁 **CSV Format Requirements**", expanded=True):
    st.markdown("""
    Your CSV **MUST** have these exact column headers:
    - `Company Name`
    - `Contact First Name` 
    - `Industry`
    - `Website`
    """)

# File uploader
uploaded_file = st.file_uploader("Choose your Leads CSV file", type=['csv'])

if uploaded_file is not None:
    # Read the CSV
    df = pd.read_csv(uploaded_file)
    
    # Validation: Check if required columns exist
    required_cols = ['Company Name', 'Contact First Name', 'Industry', 'Website']
    if not all(col in df.columns for col in required_cols):
        st.error(f"❌ CSV missing required columns. Found: {list(df.columns)}. Please fix the headers.")
        st.stop()
    
    st.success(f"✅ CSV loaded successfully! {len(df)} leads found.")
    
    # Show a preview
    with st.expander("Preview your data"):
        st.dataframe(df.head(3))
    
    # The big "START" button
    if st.button("🔥 Generate Icebreakers for ALL Leads"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Create new columns for the icebreakers
        df['Icebreaker_1'] = ""
        df['Icebreaker_2'] = ""
        df['Icebreaker_3'] = ""
        df['Website_Scraped_Text'] = ""  # Optional: show what we scraped
        
        total_leads = len(df)
        
        for index, row in df.iterrows():
            status_text.text(f"Processing {row['Contact First Name']} from {row['Company Name']}... ({index+1}/{total_leads})")
            
            # Step 1: Scrape the website
            scraped_text = scrape_website_text(row['Website'])
            df.at[index, 'Website_Scraped_Text'] = scraped_text
            
            # Step 2: If scrape worked, generate icebreakers
            if "Error" not in scraped_text and len(scraped_text) > 20:
                icebreakers = generate_icebreakers(
                    row['Company Name'],
                    row['Contact First Name'],
                    row['Industry'],
                    scraped_text
                )
                
                # Step 3: Fill the DataFrame
                if len(icebreakers) == 3:
                    df.at[index, 'Icebreaker_1'] = icebreakers[0]
                    df.at[index, 'Icebreaker_2'] = icebreakers[1]
                    df.at[index, 'Icebreaker_3'] = icebreakers[2]
                else:
                    df.at[index, 'Icebreaker_1'] = "Failed to generate"
            else:
                df.at[index, 'Icebreaker_1'] = "Scrape failed - check URL"
            
            # Update progress
            progress_bar.progress((index + 1) / total_leads)
            time.sleep(0.5)  # Small delay to avoid hitting rate limits
        
        status_text.text("✅ Processing Complete!")
        
        # Display the results
        st.subheader("📊 Your Enhanced Lead List")
        st.dataframe(df)
        
        # Download button for the new CSV
        csv_output = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Enhanced CSV for GoHighLevel",
            data=csv_output,
            file_name="leads_with_icebreakers.csv",
            mime="text/csv"
        )
        
        st.balloons()
        st.success("🎉 Done! Upload this CSV to GoHighLevel and start your campaign.")