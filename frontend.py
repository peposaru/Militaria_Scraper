import streamlit as st
import time
from datetime import datetime, timedelta

def scraper_work(duration, start_time):
    st.session_state['running'] = True
    end_time = start_time + timedelta(minutes=duration)
    total_duration = (end_time - start_time).total_seconds()

    while time.time() < end_time.timestamp() and st.session_state['running']:
        elapsed_time = time.time() - start_time.timestamp()
        progress = elapsed_time / total_duration
        st.session_state['progress'] = progress
        time.sleep(1)  # Simulate some work

        # Update the progress bar on the UI
        st.progress(float(progress))
        # Yield control back to Streamlit between chunks of work
        st.experimental_rerun()

    st.session_state['running'] = False
    st.session_state['progress'] = 0  # Reset progress after completion

def run_scraper(duration):
    start_time = datetime.now()
    scraper_work(duration, start_time)

st.title('Militaria Scraper')
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'running' not in st.session_state:
    st.session_state.running = False

duration = st.slider('Run scraper for how many minutes?', min_value=1, max_value=60, value=5)
start_button = st.button('Start Scraping')
stop_button = st.button('Stop Scraping')

if start_button and not st.session_state.running:
    st.session_state.running = True
    run_scraper(duration)

if stop_button:
    st.session_state.running = False

# Display the progress bar
st.progress(float(st.session_state.progress))

if st.button('Download CSV'):
    st.write('Download not yet implemented.')
