from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import streamlit as st
import pandas as pd

# Set up Selenium WebDriver (Ensure chromedriver is installed and PATH is set correctly)
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode to avoid opening a browser window
driver = webdriver.Chrome(options=options)

# List of tickers to retrieve data for
tickers = ['AEE', 'REZ', '1AE', '1MC', 'NRZ']

# Function to fetch announcements for a specific ticker
def fetch_announcements(ticker):
    url = f"https://www.asx.com.au/asx/1/company/{ticker}/announcements?count=20&market_sensitive=false"
    
    # Open the URL with Selenium
    driver.get(url)

    # Wait for the page to load fully
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # Get the cookies from Selenium
    cookies = driver.get_cookies()

    # Convert cookies to a format suitable for requests
    session_cookies = {cookie['name']: cookie['value'] for cookie in cookies}

    # Use Requests to fetch the data with the cookies obtained from Selenium
    response = requests.get(url, cookies=session_cookies)

    # Check if the request was successful
    if response.status_code == 200:
        return response.json().get('data', [])
    else:
        st.error(f"Failed to retrieve data for {ticker}: {response.status_code}")
        return []

# Fetch announcements for all tickers
all_announcements = {}
for ticker in tickers:
    all_announcements[ticker] = fetch_announcements(ticker)

# Close the Selenium WebDriver
driver.quit()

# Streamlit application
st.title('ASX Announcements Viewer')

# Multi-select to choose one or more tickers
selected_tickers = st.multiselect('Select one or more tickers:', tickers, default=tickers)

# Display the announcements for the selected tickers
if selected_tickers:
    combined_announcements = []
    for selected_ticker in selected_tickers:
        announcements = all_announcements[selected_ticker]
        for announcement in announcements:
            announcement['issuer_code'] = selected_ticker
        combined_announcements.extend(announcements)

    if combined_announcements:
        # Convert the combined data into a pandas DataFrame for easier display
        df = pd.DataFrame(combined_announcements)
        
        # Ensure 'document_release_date' is properly converted to datetime format
        try:
            df['document_release_date'] = pd.to_datetime(df['document_release_date'], errors='coerce')
            df = df.sort_values(by='document_release_date', ascending=False)
            df['document_release_date'] = df['document_release_date'].dt.strftime('%d %B %Y, %I:%M %p')
        except Exception as e:
            st.error(f"Error processing dates: {e}")
        
        # Rename columns for user-friendly headers
        df.rename(columns={
            'issuer_code': 'Ticker Symbol',
            'document_release_date': 'Release Date & Time',
            'header': 'Announcement Title',
            'market_sensitive': 'Market Sensitive',
            'number_of_pages': 'Number of Pages',
            'size': 'File Size',
            'url': 'Complete Announcement URL'
        }, inplace=True)

        # Display the DataFrame in Streamlit
        st.write(df[['Ticker Symbol', 'Release Date & Time', 'Announcement Title', 'Market Sensitive', 'Number of Pages', 'File Size', 'Complete Announcement URL']])
    else:
        st.write('No announcements available for the selected ticker(s).')

# Section to display tickers with "halt" or "pause" in the header
st.subheader('Tickers with Trading Halts or Pauses')

halt_pause_df_list = []

for ticker, announcements in all_announcements.items():
    ticker_df = pd.DataFrame(announcements)
    if not ticker_df.empty:
        # Ensure 'document_release_date' is properly converted to datetime format
        ticker_df['document_release_date'] = pd.to_datetime(ticker_df['document_release_date'], errors='coerce')
        halt_pause_df_list.append(
            ticker_df[ticker_df['header'].str.contains('halt|pause', case=False, na=False)]
        )

if halt_pause_df_list:
    halt_pause_df = pd.concat(halt_pause_df_list, ignore_index=True)
    halt_pause_df = halt_pause_df.sort_values(by='document_release_date', ascending=False)
    halt_pause_df['document_release_date'] = halt_pause_df['document_release_date'].dt.strftime('%d %B %Y, %I:%M %p')
    
    # Rename columns for user-friendly headers
    halt_pause_df.rename(columns={
        'document_release_date': 'Release Date & Time',
        'header': 'Announcement Title',
        'market_sensitive': 'Market Sensitive',
        'number_of_pages': 'Number of Pages',
        'size': 'File Size',
        'url': 'Complete Announcement URL',
        'issuer_code': 'Ticker Symbol'
    }, inplace=True)

    st.write(halt_pause_df[['Ticker Symbol', 'Release Date & Time', 'Announcement Title', 'Market Sensitive', 'Number of Pages', 'File Size', 'Complete Announcement URL']])
else:
    st.write('No trading halts or pauses found.')
