import streamlit as st

def apply_industrial_style():
    st.markdown("""
        <style>
        /* --- INDUSTRIAL THEME --- */
        
        /* Hide Streamlit Elements for Kiosk Mode */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Global Font Sizes & Spacing */
        .stApp {
            background-color: #f0f2f6;
        }
        
        h1, h2, h3 {
            color: #2c3e50;
            font-weight: 800 !important;
            text-transform: uppercase;
        }
        
        /* Inputs: Giant Labels and Text */
        .stSelectbox label, .stTextInput label, .stNumberInput label {
            font-size: 1.5rem !important;
            font-weight: bold;
            color: #34495e;
        }
        
        .stSelectbox div[data-baseweb="select"] > div, 
        .stTextInput input, 
        .stNumberInput input {
            font-size: 1.2rem !important;
            min-height: 50px;
        }
        
        /* Giant Buttons */
        .stButton > button {
            width: 100%;
            height: 80px;
            font-size: 1.8rem !important;
            font-weight: 900 !important;
            border-radius: 10px;
            border: 2px solid #000;
            box-shadow: 4px 4px 0px #000;
            transition: all 0.1s;
        }
        
        .stButton > button:active {
            transform: translate(2px, 2px);
            box-shadow: 2px 2px 0px #000;
        }

        /* Primary Action Button (Green) */
        div[data-testid="stButton"] > button:first-child {
            background-color: #2ecc71;
            color: white;
        }
        
        /* Alerts */
        .stAlert {
            font-size: 1.2rem;
            font-weight: bold;
        }
        
        /* Metrics/Info Cards */
        div[data-testid="stMetricValue"] {
            font-size: 2.5rem !important;
        }
        
        </style>
    """, unsafe_allow_html=True)
