"""
@file main.py
@brief Entry point for the ZIGGWAY Intelligence Hub.
"""

import os
import sys
import time
import abc

# Path fix for Streamlit Cloud (detect root)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Dict, List, Optional, Tuple, NamedTuple, Any
from dataclasses import dataclass

import streamlit as st
import pandas as pd
import plotly.express as px

# Check python version
if sys.version_info < (3, 8):
    raise RuntimeError("System requires Python 3.8+.")

# Internal Modules
from pipeline.data_processor import DataIngestor, DataCleaner, MetricsEngine, generate_mock_data
from pipeline.ai_enricher import ReviewAnalyzer

# --- MACROS / CONSTANTS ----------------------------------------------------------------
PAGE_TITLE = "ZIGGWAY"
PAGE_ICON = None
LAYOUT_MODE = "wide"

COLOR_SIDEBAR_BG = "#0A0A0A"         

CSS_BUFFER = """
<style>
    /* Main Styles */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@300;400;500;600&display=swap');
    
    :root {
        --noir-bg: #050505;
        --carbon-grid: rgba(255,255,255,0.03);
        --platinum: #A0A0A0;
        --champagne: #D4AF37;
        --glass-border: rgba(255,255,255,0.08);
        --surface-black: rgba(10,10,10,0.7);
    }

    /* HIDE STREAMLIT CLOUD TOOLBAR */
    .stDeployButton, 
    [data-testid="stToolbar"],
    header[data-testid="stHeader"],
    footer,
    #MainMenu,
    [data-testid="stStatusWidget"],
    [data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* GLOBAL RESET */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--platinum);
        font-weight: 300;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
    }

    /* BACKGROUND: CARBON GRID */
    .stApp {
        background-color: var(--noir-bg);
        background-image: 
            linear-gradient(var(--carbon-grid) 1px, transparent 1px),
            linear-gradient(90deg, var(--carbon-grid) 1px, transparent 1px);
        background-size: 40px 40px;
    }

    /* --- SIDEBAR --- */
    [data-testid="stSidebar"] {
        background-color: #080808 !important;
        border-right: 1px solid #1A1A1A;
    }
    
    [data-testid="stSidebar"] h1 {
        font-family: 'Playfair Display', serif;
        font-weight: 600;
        letter-spacing: 0.5px;
        color: #FFF;
        text-transform: none; /* Classy Normal Case */
        font-size: 2rem;
        margin-bottom: 2rem;
        border-bottom: 1px solid var(--champagne);
        padding-bottom: 15px;
        font-style: italic;
    }
    
    /* NAV BUTTONS: REFINED */
    [data-testid="stSidebar"] [role="radiogroup"] label {
        border-radius: 4px !important;
        border: none;
        margin-bottom: 8px;
        background: transparent;
        transition: all 0.3s ease;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        letter-spacing: 0.5px;
        padding-left: 15px;
    }
    
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(255,255,255,0.02);
        color: #FFF;
        padding-left: 20px;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {
        background: linear-gradient(90deg, rgba(212, 175, 55, 0.1), transparent) !important;
        border-left: 2px solid var(--champagne);
        color: var(--champagne) !important;
        font-weight: 500;
        padding-left: 20px;
    }
    
    [data-testid="stSidebar"] [role="radiogroup"] label::before { display: none; }

    /* --- METRICS --- */
    [data-testid="stMetric"] {
        background: var(--surface-black);
        backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0 12px 40px rgba(0,0,0,0.6);
        min-height: 180px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative !important;
        overflow: hidden !important;
    }

    /* Active Indicator */
    [data-testid="stMetric"]::before {
        content: '';
        position: absolute;
        top: 24px;
        right: 24px;
        width: 4px;
        height: 4px;
        background: var(--champagne);
        border-radius: 50%;
        box-shadow: 0 0 10px var(--champagne);
        animation: activePulse 2s infinite ease-in-out;
    }

    /* Metric Decorator */
    [data-testid="stMetric"]::after {
        content: 'ZIGGWAY';
        position: absolute;
        bottom: 20px;
        right: 24px;
        font-family: 'Inter', sans-serif;
        font-size: 0.45rem;
        color: rgba(255,255,255,0.06);
        letter-spacing: 2px;
        pointer-events: none;
    }
    
    @keyframes activePulse {
        0% { opacity: 0.2; transform: scale(0.8); }
        50% { opacity: 1; transform: scale(1.2); }
        100% { opacity: 0.2; transform: scale(0.8); }
    }
    
    [data-testid="stMetric"]:hover {
        border-color: rgba(212, 175, 55, 0.5);
        transform: translateY(-6px);
        background: rgba(18,18,18,0.9);
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 0.85rem !important;
        color: #FFFFFF !important;
        margin-bottom: 0 !important;
    }
    
    [data-testid="stMetricValue"] {
        font-family: 'Inter', sans-serif;
        color: #FFFFFF;
        font-weight: 300;
        font-size: 2.1rem !important;
        letter-spacing: -0.5px;
        flex-grow: 1 !important;
        display: flex !important;
        align-items: center !important;
        margin: 5px 0 !important;
    }

    [data-testid="stMetricDelta"] {
        margin-top: auto !important;
        z-index: 2 !important;
        background: rgba(212, 175, 55, 0.08) !important;
        border: 1px solid rgba(212, 175, 55, 0.15) !important;
        padding: 4px 10px !important;
        border-radius: 4px !important; /* Sharp executive corners */
        font-family: 'Inter', sans-serif;
        font-size: 0.65rem !important;
        color: var(--champagne) !important;
        width: fit-content !important;
    }

    [data-testid="stMetricDelta"] svg { fill: var(--champagne) !important; }

    /* --- FORM ELEMENTS: LUXURY WHITE --- */
    [data-testid="stCheckbox"] label p {
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
    }
    
    /* --- EXPANDER --- */
    [data-testid="stExpander"] {
        background: linear-gradient(165deg, rgba(18, 18, 18, 0.6), rgba(8, 8, 8, 0.8)) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-left: 2px solid rgba(212, 175, 55, 0.3) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        overflow: hidden !important;
        transition: all 0.3s ease !important;
        margin: 10px 0 !important;
    }
    
    [data-testid="stExpander"]:hover {
        border-left-color: rgba(212, 175, 55, 0.6) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
    }
    
    [data-testid="stExpander"] summary {
        padding: 16px 20px !important;
    }
    
    [data-testid="stExpander"] p {
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: 0.5px !important;
    }
    
    [data-testid="stExpander"] svg {
        color: var(--champagne) !important;
    }

    [data-testid="stWidgetLabel"] p {
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
    }

    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    
    /* --- DIVIDER: SUBTLE GRADIENT LINE --- */
    [data-testid="stHorizontalRule"],
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1) 20%, rgba(255,255,255,0.1) 80%, transparent) !important;
        margin: 30px 0 !important;
    }
    
    /* --- HEADERS: SERIF AUTHORITY --- */
    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        color: #F0F0F0;
        font-weight: 400;
    }
    
    h1 { font-size: 2.5rem !important; margin-bottom: 0.5rem !important; }
    h2 { font-size: 1.5rem !important; border-left: none !important; color: var(--champagne); }
    h3 { font-size: 1.2rem !important; opacity: 0.9; }

    /* --- WIDGETS: ELEGANT CONTROLS --- */
    .stButton button {
        border-radius: 4px !important;
        border: 1px solid #444;
        color: #FFF;
        background: #111;
        font-family: 'Inter', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.75rem;
        transition: 0.4s ease;
    }
    
    .stButton button:hover {
        background: #FFF;
        color: #000;
        border-color: #FFF;
    }

    /* --- SEGMENTED CONTROL --- */
    /* Nuke default styles */
    [data-testid="stSegmentedControl"] {
        background: transparent !important;
        padding: 0 !important;
        border: none !important;
        gap: 6px !important;
    }

    [data-testid="stSegmentedControl"] > div > div {
        background: transparent !important;
        border: none !important;
    }

    /* Unselected State */
    [data-testid="stSegmentedControl"] button {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 4px !important; /* Tech-square corners */
        color: rgba(255,255,255,0.5) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.7rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.5px !important;
        padding: 6px 14px !important;
        height: 32px !important;
        min-height: 32px !important;
        transition: all 0.2s cubic-bezier(0.2, 0.8, 0.2, 1) !important;
    }

    /* Hover State (Levitation) */
    [data-testid="stSegmentedControl"] button:hover {
        background: rgba(255,255,255,0.08) !important;
        border-color: rgba(255,255,255,0.2) !important;
        transform: translateY(-2px);
        color: #FFF !important;
    }

    /* Active State */
    [data-testid="stSegmentedControl"] button[data-active="true"] {
        background: linear-gradient(180deg, #D4AF37 0%, #B8860B 100%) !important;
        border: 1px solid #FFD700 !important;
        color: #050505 !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.4) !important;
        transform: scale(1.05) !important;
        z-index: 5 !important;
    }
    
    /* Remove the weird focus ring Streamlit adds */
    [data-testid="stSegmentedControl"] button:focus {
        box-shadow: none !important;
        outline: none !important;
    }

    /* --- NUMBER INPUT --- */
    
    /* 1. Target the Deepest Input Element (NO INTERNAL BORDER) */
    div[data-testid="stNumberInput"] input {
        background-color: transparent !important;
        color: var(--champagne) !important;
        font-family: 'Courier New', monospace !important;
        font-weight: 700 !important;
        caret-color: var(--champagne) !important; /* Restore Cursor */
        box-shadow: none !important;
        text-align: center !important;
        padding: 0 !important;
        border: none !important; 
        outline: none !important;
        min-width: 50px !important; /* Ensure clickable area */
    }

    /* 2. Target the Wrapping Containers (GHOST MODE - NO GREY CARD) */
    div[data-testid="stNumberInput"] div[data-baseweb="input"],
    div[data-testid="stNumberInput"] div[data-baseweb="base-input"] {
        background-color: transparent !important; /* Removed Gray */
        border: none !important; /* Removed Border */
        color: white !important;
    }
    
    /* Ensure generic wrapper doesn't double-border */
    div[data-testid="stNumberInput"] > div > div {
        border: none !important;
        box-shadow: none !important;
    }

    /* 3. Handle Focus/Hover State (Pure Ghost - No Visual Change) */
    div[data-testid="stNumberInput"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stNumberInput"] div[data-baseweb="base-input"]:focus-within,
    div[data-testid="stNumberInput"]:hover div[data-baseweb="input"],
    div[data-testid="stNumberInput"]:hover div[data-baseweb="base-input"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* 4. Kill the +/- Buttons Background except on Hover */
    div[data-testid="stNumberInput"] button {
        background-color: #111 !important;
        border-left: 1px solid #333 !important;
        color: #888 !important;
    }
    
    div[data-testid="stNumberInput"] button:hover {
        background-color: var(--champagne) !important;
        color: #000 !important;
    }
    
    /* 5. Placeholder Text Color */
    div[data-testid="stNumberInput"] input::placeholder {
        color: rgba(255,255,255,0.2) !important;
    }

    /* --- BUTTON: NEURAL PULSE (ANIMATED) --- */
    @keyframes goldPulse {
        0%, 100% { box-shadow: 0 4px 20px rgba(212, 175, 55, 0.3); }
        50% { box-shadow: 0 4px 30px rgba(212, 175, 55, 0.5), 0 0 40px rgba(212, 175, 55, 0.2); }
    }
    
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FFD700 0%, #D4AF37 50%, #B8860B 100%) !important;
        color: #000000 !important;
        font-weight: 800 !important;
        text-shadow: 0 1px 2px rgba(255,255,255,0.3);
        border: none !important;
        border-radius: 8px !important;
        height: 44px !important;
        animation: goldPulse 3s ease-in-out infinite !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        letter-spacing: 1.5px !important;
        font-size: 0.85rem !important;
    }
    
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.02) !important;
        animation: none !important;
        box-shadow: 0 8px 35px rgba(212, 175, 55, 0.5) !important;
    }

    /* SECONDARY BUTTON (MAX): Dark Luxury */
    div.stButton > button:not([kind="primary"]) {
        background: linear-gradient(180deg, #1A1A1A 0%, #0D0D0D 100%) !important;
        color: rgba(255, 255, 255, 0.7) !important;
        font-weight: 600 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        height: 42px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        letter-spacing: 1px !important;
    }
    
    div.stButton > button:not([kind="primary"]):hover {
        background: linear-gradient(180deg, #252525 0%, #1A1A1A 100%) !important;
        border-color: var(--champagne) !important;
        color: var(--champagne) !important;
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.15) !important;
        transform: translateY(-1px);
    }

    /* CONTAINER STYLE */
    .neural-container {
        background: linear-gradient(165deg, rgba(18, 18, 18, 0.85), rgba(8, 8, 8, 0.95));
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-left: 3px solid rgba(212, 175, 55, 0.5);
        backdrop-filter: blur(25px);
        -webkit-backdrop-filter: blur(25px);
        border-radius: 16px;
        padding: 24px 30px !important;
        margin: 20px 0 30px 0;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.03);
        position: relative;
        overflow: hidden;
    }

    /* Subtle Gold Glow Effect */
    .neural-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100px;
        height: 100%;
        background: linear-gradient(90deg, rgba(212, 175, 55, 0.05), transparent);
        pointer-events: none;
    }

    /* Horizontal Alignment Fix for Streamlit Columns */
    div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }
    
    [data-testid="stFileUploader"] { margin-top: 20px; border: 1px dashed #333; padding: 20px; border-radius: 8px; }
    
    /* --- INPUTS & MULTISELECT --- */
    /* Universal Select/Input Background Fix */
    [data-testid="stMultiSelect"] [data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] [role="combobox"],
    [data-testid="stTextInput"] div[data-baseweb="base-input"] {
        background-color: #0A0A0A !important;
        background: #0A0A0A !important;
        border-color: #333 !important;
    }

    [data-testid="stTextInput"] input {
        background-color: transparent !important;
        color: #FFFFFF !important;
        padding: 12px 16px !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        border: none !important;
    }
    
    [data-testid="stTextInput"] > div {
        background-color: #0A0A0A !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
    }

    [data-testid="stTextInput"] > div:focus-within {
        border-color: var(--champagne) !important;
        box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.15) !important;
    }
    
    [data-testid="stTextInput"] input::placeholder {
        color: #555 !important;
    }
    
    /* Multiselect Specifics */
    [data-testid="stMultiSelect"] > div > div {
        background-color: #0A0A0A !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
    }
    
    [data-testid="stMultiSelect"] div[data-baseweb="select"] {
        background-color: #0A0A0A !important;
    }

    [data-testid="stMultiSelect"] [data-baseweb="value-container"] {
        background-color: transparent !important;
    }
    
    [data-testid="stMultiSelect"] > div > div:focus-within {
        border-color: var(--champagne) !important;
        box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.15) !important;
    }
    
    /* Multiselect Tags (Pills) */
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.2), rgba(212, 175, 55, 0.1)) !important;
        border: 1px solid rgba(212, 175, 55, 0.4) !important;
        border-radius: 6px !important;
        color: var(--champagne) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 12px !important;
        font-weight: 500 !important;
    }
    
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] svg {
        fill: var(--champagne) !important;
    }
    
    /* Multiselect Dropdown Menu */
    [data-baseweb="popover"] > div {
        background-color: #0A0A0A !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
    }
    
    [data-baseweb="menu"] {
        background-color: #0A0A0A !important;
    }
    
    [data-baseweb="menu"] li {
        background-color: transparent !important;
        color: #CCC !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    [data-baseweb="menu"] li:hover {
        background-color: rgba(212, 175, 55, 0.1) !important;
        color: #FFF !important;
    }
    
    /* --- ELEGANT EXPANDER (FIXED) --- */
    [data-testid="stExpander"] {
        background: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    
    [data-testid="stExpander"] details {
        background-color: #0A0A0A !important;
        border: none !important;
    }
    
    [data-testid="stExpander"] summary {
        padding: 16px 20px !important;
        font-family: 'Playfair Display', serif !important;
        font-size: 1rem !important;
        color: #FFFFFF !important;
        background-color: #0A0A0A !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stExpander"] summary:hover {
        background: rgba(212, 175, 55, 0.05) !important;
        color: var(--champagne) !important;
    }

    /* Target the SVG icon in summary */
    [data-testid="stExpander"] summary svg {
        fill: #FFFFFF !important;
    }
    
    [data-testid="stExpander"] > div > div {
        background-color: #0A0A0A !important;
        padding: 0 20px 20px 20px !important;
    }
    
    /* DATAFRAME */
    [data-testid="stDataFrame"] { border: 1px solid #222; border-radius: 8px; overflow: hidden; }
    
    /* ANIMATIONS */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Apply to Logic Layers */
    .stMetric, .stPlotlyChart, div[data-testid="stExpander"] {
        animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    
    /* Staggered text reveal */
    h1, h2, h3, h4 {
        animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    /* --- DOCUMENTATION CARDS --- */
    .doc-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 8px;
        transition: all 0.3s ease;
    }
    .doc-card:hover {
        background: rgba(255, 255, 255, 0.04);
        border-color: rgba(212, 175, 55, 0.2);
    }
    .doc-title {
        font-family: 'Playfair Display', serif;
        color: var(--champagne);
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 6px;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
    }
    .doc-item {
        font-family: 'Inter', sans-serif;
        font-size: 0.65rem; /* Ultra fine for sidebar */
        color: #888;
        margin-bottom: 2px;
        padding-left: 8px;
        border-left: 1px solid #333;
        line-height: 1.3;
    }
    .doc-item b {
        color: #AAA;
        font-weight: 500;
    }
    .doc-tag {
        font-size: 0.5rem;
        background: rgba(255,255,255,0.08);
        color: #666;
        padding: 1px 6px;
        border-radius: 3px;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        font-family: 'Inter', sans-serif;
        display: inline-block;
    }

    /* Target File Uploader Labels */
    [data-testid="stFileUploader"] label {
        font-family: 'Playfair Display', serif !important;
        font-size: 0.9rem !important;
        color: #FFFFFF !important;
        font-style: italic !important;
        margin-bottom: 10px !important;
    }

    /* --- FILE UPLOADER: NOIR EDITION (CLEAN & CENTERED) --- */
    [data-testid="stFileUploader"] {
        background-color: #0A0A0A !important;
        border: 1px dashed rgba(212, 175, 55, 0.2) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        overflow: hidden !important;
    }

    /* Target inner section padding and transparency */
    [data-testid="stFileUploader"] section {
        padding: 0 !important;
        background-color: transparent !important;
        color: transparent !important; /* Hide "Drag and drop" text node */
        font-size: 0 !important; /* Shrink original text space */
    }
    
    [data-testid="stFileUploader"] section > div {
        background-color: transparent !important;
    }

    /* Aggressively hide standard text elements */
    [data-testid="stFileUploader"] [data-testid="stIcon"],
    [data-testid="stFileUploader"] small, 
    [data-testid="stFileUploader"] span {
        display: none !important;
    }

    /* DRAG & DROP TEXT (Portuguese) */
    [data-testid="stFileUploader"] section::before {
        content: "Arraste e solte o arquivo aqui";
        display: block;
        font-family: 'Inter', sans-serif;
        color: #F0F0F0;
        font-weight: 500;
        font-size: 0.8rem !important; /* Explicit size needed */
        margin-bottom: 12px;
        text-align: center;
        visibility: visible !important;
    }

    /* BUTTON CONTAINER RELATIVE */
    [data-testid="stFileUploader"] button {
        position: relative !important;
        background-color: transparent !important;
        border: 1px solid var(--champagne) !important;
        border-radius: 6px !important;
        width: 100% !important;
        min-height: 48px !important;
        padding: 0 !important;
        margin: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        overflow: hidden !important;
        transition: all 0.3s ease !important;
        visibility: visible !important; /* Override parent hiding */
    }

    /* BUTTON HOVER */
    [data-testid="stFileUploader"] button:hover {
        background-color: var(--champagne) !important;
        border-color: var(--champagne) !important;
    }

    /* HIDE ORIGINAL TEXT (font-size hack) */
    [data-testid="stFileUploader"] button {
        color: transparent !important;
        font-size: 0 !important;
    }

    /* TEXT REPLACEMENT (Absolute Center) */
    [data-testid="stFileUploader"] button::after {
        content: "ESCOLHER ARQUIVO";
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: var(--champagne);
        font-size: 0.75rem !important;
        font-weight: 600;
        letter-spacing: 1px;
        font-family: 'Inter', sans-serif;
        text-transform: uppercase;
        white-space: nowrap;
        pointer-events: none;
    }

    /* HOVER TEXT COLOR */
    [data-testid="stFileUploader"] button:hover::after {
        color: #000 !important;
    }
    
    /* Hide internal span/divs of button just in case */
    [data-testid="stFileUploader"] button > div,
    [data-testid="stFileUploader"] button > span {
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* LIMIT TEXT */
    [data-testid="stFileUploader"] section::after {
        content: "LIMITE 10GB";
        display: block;
        font-size: 0.55rem !important;
        color: #444 !important;
        margin-top: 10px;
        text-align: center;
        letter-spacing: 0.8px;
        font-family: 'Inter', sans-serif;
        visibility: visible !important;
    }

    /* Motion apply */
    .doc-card { animation: fadeInUp 0.6s ease forwards; }

    /* --- SIDEBAR NAVIGATION (ZEN MINIMAL) --- */
    
    /* Hide the label "NAVEGAÇÃO" */
    section[data-testid="stSidebar"] [data-testid="stRadio"] > label {
        display: none !important;
    }

    /* Radio group container */
    section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
        background: transparent !important;
        gap: 16px !important; /* Spacier for elegance */
        padding: 5px 0 !important;
    }

    /* --- SIDEBAR NAV (Clean Minimal) --- */
    section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
        display: flex !important;
        align-items: center !important;
        padding: 10px 0 !important;
        background: transparent !important;
        border: none !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
    }

    /* HIDE the Streamlit radio visual component */
    section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    /* Minimal Dot Indicator */
    section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label::before {
        content: '';
        display: block;
        width: 4px;
        height: 4px;
        background: rgba(255, 255, 255, 0.15);
        border-radius: 50%;
        margin-right: 16px;
        transition: all 0.3s ease;
    }

    /* Active Dot - Subtle Gold Glow */
    section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked)::before {
        background: var(--champagne);
        box-shadow: 0 0 8px var(--champagne);
    }


    /* Text styling */
    section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label p {
        font-family: 'Inter', sans-serif !important;
        font-size: 0.82rem !important;
        font-weight: 300 !important;
        color: rgba(255, 255, 255, 0.3) !important;
        letter-spacing: 0.6px !important;
        margin: 0 !important;
        transition: all 0.3s ease !important;
    }

    /* Active text - Sharp Champagne */
    section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) p {
        color: var(--champagne) !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        transform: translateX(5px);
    }

    /* Hover effect */
    section[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover p {
        color: rgba(255, 255, 255, 0.6) !important;
    }

    /* --- CHECKBOX --- */
    [data-testid="stCheckbox"] {
        background: rgba(10, 10, 10, 0.4);
        border: 1px solid rgba(50, 50, 50, 1);
        border-left: 2px solid rgba(50, 50, 50, 1);
        border-radius: 8px;
        padding: 0 15px !important;
        height: 42px !important;
        display: flex !important;
        align-items: center !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        margin: 0 !important;       /* Removed margins for perfect alignment */
        cursor: pointer;
    }

    /* Hover Interaction */
    [data-testid="stCheckbox"]:hover {
        border-color: rgba(255, 255, 255, 0.2);
        border-left-color: var(--champagne);
        background: rgba(20, 20, 20, 0.8);
        transform: translateX(4px);
        box-shadow: -5px 5px 20px rgba(0,0,0,0.5);
    }

    /* ACTIVE STATE: Engaged */
    [data-testid="stCheckbox"]:has(input:checked) {
        background: linear-gradient(90deg, rgba(212, 175, 55, 0.1), transparent);
        border-color: var(--champagne);
        border-left-width: 4px;
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.1);
    }

    /* Typography */
    [data-testid="stCheckbox"] label p {
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        letter-spacing: 0.5px !important;
        color: rgba(255, 255, 255, 0.5) !important;
        transition: color 0.3s ease;
        font-weight: 400 !important;
    }

    /* Active Typography */
    [data-testid="stCheckbox"]:has(input:checked) label p {
        color: #FFF !important;
        font-weight: 600 !important;
        text-shadow: 0 0 12px rgba(212, 175, 55, 0.6);
    }

    /* Chrome/Input Override (The Box Itself) */
    [data-testid="stCheckbox"] div[role="checkbox"] {
        border-radius: 4px !important;
        background-color: rgba(0, 0, 0, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        transition: all 0.2s ease;
    }

    /* Checked Box State */
    [data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] {
        background-color: var(--champagne) !important;
        border-color: var(--champagne) !important;
        color: #000000 !important; /* The checkmark itself */
    }
    
    /* Ensure the text inside the active button is black */
    div[data-testid="stSegmentedControl"] > div > div[data-active="true"] p,
    div[data-testid="stSegmentedControl"] button[data-active="true"] p {
        color: #000000 !important;
        font-weight: 800 !important;
    }
    
    /* Hover effects for non-active items */
    div[data-testid="stSegmentedControl"] > div > div:not([data-active="true"]):hover {
        border-color: var(--champagne) !important;
        color: var(--champagne) !important;
    }
</style>
"""

# --- STRUCTS ---------------------------------------------------------------------------

class ProcessingResult(NamedTuple):
    """Immutable struct to hold processing outcomes."""
    full_df: Optional[pd.DataFrame]
    ltv_df: Optional[pd.DataFrame]
    churn_df: Optional[pd.DataFrame]
    status_code: int  # 0 = OK, 1 = ERROR

class PageContext(NamedTuple):
    """Context passed to render functions to avoid global state."""
    df: pd.DataFrame
    churn: pd.DataFrame
    ltv: pd.DataFrame
    analyzer: ReviewAnalyzer

# --- SYSTEM INITIALIZATION -------------------------------------------------------------

def init_system() -> None:
    """Initializes the page configuration and global styling."""
    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon=PAGE_ICON,
        layout=LAYOUT_MODE,
        initial_sidebar_state="expanded"
    )
    # Inject CSS Kernel
    st.markdown(CSS_BUFFER, unsafe_allow_html=True)
    
    # Initialize Singleton for AI Analyzer
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = ReviewAnalyzer()

@st.cache_data(show_spinner=False)
def data_ingestion_pipeline(uploaded_files: Dict[str, Any]) -> ProcessingResult:
    """
    Core data processing pipeline.
    Uses caching to avoid re-computation on every frame render.
    """
    ingestor = DataIngestor()
    
    # Load Data (files mapped explicitly to expected keys)
    raw_data = ingestor.load_data(uploaded_files if uploaded_files else None)
    
    # --- AUTO-MOCK FALLBACK FOR CLOUD DEMO ---
    if not raw_data:
        # If running on cloud/clean env with no upload, generate mock data automatically
        generate_mock_data()
        # Retry loading
        raw_data = ingestor.load_data(None)

    if not raw_data:
        return ProcessingResult(None, None, None, 1) # Return Error Code
        
    # Data Cleaning / Sanitization
    cleaner = DataCleaner()
    orders_df = cleaner.clean_orders(raw_data['orders'])
    reviews_df = cleaner.clean_reviews(raw_data['reviews'])
    payments_df = raw_data['payments']
    
    # Merge Steps (Join Operations)
    full_df = cleaner.merge_datasets(orders_df, payments_df, reviews_df)
    
    # Metric Calculation
    metrics = MetricsEngine()
    ltv_df = metrics.calculate_ltv(full_df)
    churn_df = metrics.calculate_churn_risk(orders_df)
    
    return ProcessingResult(full_df, ltv_df, churn_df, 0) # OK

# --- RENDERERS (V-TABLE PATTERN) -------------------------------------------------------

def render_dashboard(ctx: PageContext) -> None:
    """Renders the Strategic Dashboard view."""
    st.title("Visão Estratégica")
    st.markdown("<p style='color: #A0A0A0; font-family: Inter; font-size: 1.1rem; margin-top: -10px;'>Monitoramento executivo de performance e saúde financeira.</p>", unsafe_allow_html=True)


    
    # Calculate KPIs
    rev_total = ctx.df['payment_value'].sum() if 'payment_value' in ctx.df else 0.0
    avg_tkt = ctx.df['payment_value'].mean() if 'payment_value' in ctx.df else 0.0
    
    active_cust_count = 0
    if not ctx.churn.empty and 'is_active_30d' in ctx.churn.columns:
        active_cust_count = ctx.churn[ctx.churn['is_active_30d'] == True].shape[0]
    
    total_cust = ctx.df['customer_id'].nunique()
    ratio_active = (active_cust_count / max(1, total_cust)) * 100

    # Display Kernel
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Receita Total", f"R$ {rev_total:,.2f}", help="Soma total aprovada.")
    col_b.metric("Ticket Médio", f"R$ {avg_tkt:,.2f}")
    col_c.metric("Clientes Ativos (30d)", f"{active_cust_count}", delta=f"{ratio_active:.1f}% da base")
    
    st.divider()
    
    # Visualization Grid (Stacked)
    # Visualization Grid (Stacked)
    st.divider()
    
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    st.header("Desempenho Financeiro")
    if 'order_purchase_timestamp' in ctx.df.columns:
        # 1. Revenue Chart Logic
        # Group by week to smooth out noise if dataset is large, otherwise day
        daily_rev = ctx.df.groupby(ctx.df['order_purchase_timestamp'].dt.date)['payment_value'].sum().reset_index()
        
        fig = px.area(daily_rev, x='order_purchase_timestamp', y='payment_value', template="plotly_dark")
        fig.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter", size=11, color="#A0A0A0"),
            xaxis=dict(showgrid=False, title=None, showticklabels=True, tickfont=dict(color="#A0A0A0")),
            yaxis=dict(showgrid=True, gridcolor="#222", title=None, tickfont=dict(color="#A0A0A0"), tickprefix="R$ ")
        )
        fig.update_traces(line_color='#D4AF37', line_width=2, fillcolor='rgba(212, 175, 55, 0.1)')
        st.plotly_chart(fig, use_container_width=True)
            
    st.divider()

    st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
    st.header("Composição e Distribuição")
    if 'order_status' in ctx.df.columns:
        # 1. Prepare Data
        counts = ctx.df['order_status'].value_counts().reset_index()
        counts.columns = ['status', 'count']
        
        status_map = {
            'delivered': 'Entregue', 'shipped': 'Enviado', 'canceled': 'Cancelado',
            'unavailable': 'Indisponível', 'invoiced': 'Faturado', 'processing': 'Processando',
            'created': 'Criado', 'approved': 'Aprovado'
        }
        counts['status_pt'] = counts['status'].map(status_map).fillna(counts['status'])
        
        total = counts['count'].sum()
        counts['percent'] = counts['count'] / total
        counts = counts.sort_values(by='count', ascending=False)
        
        # Filter absolute zeros to keep it clean
        counts = counts[counts['count'] > 0]

        # 2. Layout (Executive Split)
        col_chart, col_specs = st.columns([1.2, 1])
        
        # Color Palette
        colors = ['#D4AF37', '#E5E4E2', '#E67E22', '#27AE60', '#2980B9', '#C0392B', '#16A085', '#F1C40F']
        
        with col_chart:
            fig = px.pie(
                counts, 
                names='status_pt', 
                values='count', 
                hole=0.82, 
                template="plotly_dark",
                color_discrete_sequence=colors
            )
            
            # Hide ALL labels on the chart to prevent "buggy" overlap
            fig.update_traces(
                textinfo='none', 
                hoverinfo='label+percent',
                marker=dict(line=dict(color='#050505', width=3))
            )
            
            # Calculate delivered percentage for the center text
            del_row = counts[counts['status'] == 'delivered']
            del_pct = (del_row['percent'].values[0] * 100) if not del_row.empty else 0
            
            fig.update_layout(
                showlegend=False,
                height=450, 
                margin=dict(l=0,r=0,t=0,b=0), 
                paper_bgcolor='rgba(0,0,0,0)',
                annotations=[dict(
                    text=f"<span style='font-family: Playfair Display; color: #D4AF37; font-size: 38px; font-weight: 700;'>{total:,}</span><br><br><span style='font-family: Inter; color: #A0A0A0; font-size: 11px; letter-spacing: 3px; font-weight: 600;'>ORDENS TOTAIS</span><br><br><span style='font-family: Inter; color: #D4AF37; font-size: 15px; font-weight: 600;'>{del_pct:.1f}% Entregue</span>", 
                    x=0.5, y=0.5, showarrow=False
                )]
            )
            st.plotly_chart(fig, use_container_width=True)


        with col_specs:
            st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
            st.markdown(f"<h4 style='font-family: Playfair Display; color: #FFF; margin-bottom: 30px; letter-spacing: 2px; text-transform: uppercase; font-size: 0.9rem; opacity: 0.8;'>Distribuição Secundária</h4>", unsafe_allow_html=True)
            
            # Skip delivered (index 0) and filter negligible data
            detail_list = counts.iloc[1:].copy()
            detail_list = detail_list[detail_list['percent'] > 0.001] 
            
            if detail_list.empty:
                st.markdown("<div style='color: #A0A0A0; font-family: Inter; font-size: 13px;'>Nenhuma anomalia de distribuição detectada.</div>", unsafe_allow_html=True)
            else:
                items_html = ""
                for i, (_, row) in enumerate(detail_list.iterrows()):
                    pct = row['percent'] * 100
                    delay = (i + 1) * 0.1 
                    
                    # VARIANCE FIX: Use the specific color from the palette for THIS rank
                    # Offset by 1 because we skip index 0
                    color_idx = (i + 1) % len(colors)
                    val_color = colors[color_idx]
                    
                    # NOTE: Indentation stripped to prevent st.markdown code block bug
                    items_html += f"""<div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05); opacity: 0; animation: fadeInUp 0.5s ease forwards; animation-delay: {delay:.1f}s;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <div style="width: 3px; height: 32px; background: {val_color}; border-radius: 2px;"></div>
        <div style="display: flex; flex-direction: column; gap: 2px;">
            <span style="font-family: 'Inter'; font-size: 14px; color: #EEE; font-weight: 500;">{row['status_pt']}</span>
            <span style="font-family: 'Inter'; font-size: 11px; color: #A0A0A0; letter-spacing: 0.5px;">{row['count']:,} ordens</span>
        </div>
    </div>
    <div style="text-align: right;">
        <div style="font-family: 'Playfair Display'; font-size: 18px; color: {val_color}; font-weight: 700;">{pct:.2f}%</div>
    </div>
</div>"""
                
                st.markdown(f"<div style='display: flex; flex-direction: column;'>{items_html}</div>", unsafe_allow_html=True)

def render_command_center(ctx: PageContext) -> None:
    """Renders the CX Command Center."""
    st.title("Experiência do Cliente")
    
    # 1. Metrics Header
    nps_proxy = "N/A"
    if 'review_score' in ctx.df.columns:
        promoters = len(ctx.df[ctx.df['review_score'] == 5])
        detractors = len(ctx.df[ctx.df['review_score'] <= 3])
        total = len(ctx.df)
        if total > 0:
            val = ((promoters - detractors) / total) * 100
            nps_proxy = f"{val:.0f}"
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NPS (Estimado)", nps_proxy)
    c2.metric("Reviews Totais", f"{len(ctx.df)}")
    
    # Pre-calculate counts for efficiency
    pending_count = len(ctx.df[ctx.df['review_comment_message'].str.len() > 5])
    c3.metric("Fila de Análise", f"{pending_count}")
    
    avg_score = ctx.df['review_score'].mean()
    c4.metric("Satisfação Média", f"{avg_score:.1f}/5.0")
    
    st.divider()
    
    # 2. Intelligent Triage
    st.subheader("Triagem Inteligente")

    st.markdown("<p style='color: #A0A0A0;'>Transforme feedback em estratégia. O sistema analisa automaticamente o sentimento e a urgência de cada avaliação, organizando as prioridades para que sua equipe atue com precisão e agilidade.</p>", unsafe_allow_html=True)
    
    # Logic Partition: Pre-calculate view based on filter state
    is_filtered = st.session_state.get('filt_cancel', False)
    
    # Construct base view
    if is_filtered:
        base_view = ctx.df[
            (ctx.df['order_status'] == 'canceled') & 
            (ctx.df['review_comment_message'].str.len() > 2)
        ].drop_duplicates(subset=['review_comment_message']).copy()
    else:
        base_view = ctx.df[ctx.df['review_comment_message'].str.len() > 2].drop_duplicates(subset=['review_comment_message']).copy()
    
    max_items = len(base_view)
    
    if max_items > 0:
        # 1. Main Control Row: Input | MAX | Filter (Balanced Ratios)
        col_input, col_max, col_filt = st.columns([3.5, 1.2, 1.8]) 
        
        if 'batch_qty_input' not in st.session_state:
            st.session_state.batch_qty_input = min(10, max_items)
            
        if st.session_state.batch_qty_input > max_items:
             st.session_state.batch_qty_input = max_items
             
        def set_max_value():
            st.session_state.batch_qty_input = max_items

        with col_input:
            batch_qty = st.number_input(
                "Qtd. Exata", min_value=1, max_value=max_items, 
                key='batch_qty_input', label_visibility="collapsed"
            )

        with col_max:
             st.button("MAX", on_click=set_max_value, use_container_width=True, help="Capacidade máxima")

        with col_filt:
             st.checkbox("Filtrar Cancelados", key='filt_cancel')
             
        # 2. Action Row: PROCESSAR (Bottom & Full Width)
        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
        do_process = st.button("PROCESSAR", type="primary", use_container_width=True)
    else:
        do_process = False
        batch_qty = 0
        st.warning("Sem dados para analisar.")
        st.checkbox("Filtrar Cancelados", key='filt_cancel')

    # 3. Neural Processing Block
    if do_process and batch_qty > 0:
        _perform_neural_analysis(base_view, batch_qty, ctx.analyzer)
    
    elif 'last_analysis' in st.session_state and not do_process:
        _render_last_analysis_table()
        
    st.divider()
    _render_explorer(ctx.df)

def _perform_neural_analysis(df: pd.DataFrame, qty: int, analyzer: ReviewAnalyzer) -> None:
    """Helper: Executes the analysis loop."""
    with st.status("Processando...", expanded=True) as status:

        
        target = df.head(qty)
        # Convert to POD (Plain Old Data) for processing
        input_buffer = [{'text': r.review_comment_message, 'score': r.review_score} for r in target.itertuples()]
        
        st.write(f"Classificando {len(input_buffer)} avaliações...")
        p_bar = st.progress(0)
        
        results = []
        start_t = time.time()
        
        # Generator consumption loop
        total = len(input_buffer)
        for i, res in enumerate(analyzer.analyze_batch_with_progress(input_buffer, max_workers=8)):
            results.append(res)
            # Update GUI
            p_bar.progress((i + 1) / total)
            
        elapsed = time.time() - start_t
        status.update(label=f"Concluído em {elapsed:.1f}s!", state="complete", expanded=True)
        
        # Data Enrichment (Memory mapping)
        enriched = target.copy()
        enriched['Sentimento_IA'] = [r['sentiment'] for r in results]
        enriched['Categoria_IA'] = [r['category'] for r in results]
        enriched['Urgencia_IA'] = [r['urgency'] for r in results]
        enriched['Acao_Sugerida'] = [r['suggested_action'] for r in results]
        
        # Persist to Session State (Heap)
        st.session_state['last_analysis'] = enriched
        
        _render_last_analysis_table()

def _render_last_analysis_table() -> None:
    """Helper: Displays the results table."""
    if 'last_analysis' not in st.session_state: return
    
    st.subheader("Resultados da Análise")
    df = st.session_state['last_analysis']
    
    st.dataframe(
        df[['review_score', 'review_comment_message', 'Sentimento_IA', 'Categoria_IA', 'Urgencia_IA', 'Acao_Sugerida']],
        use_container_width=True,
        column_config={
            "review_score": st.column_config.NumberColumn("Nota", format="%d"),
            "review_comment_message": "Comentário",
            "Sentimento_IA": "Sentimento",
            "Urgencia_IA": "Urgência",
            "Acao_Sugerida": "Ação Tática"
        }
    )

def _render_explorer(full_df: pd.DataFrame) -> None:
    """Helper: Renders the Case Explorer section."""
    st.subheader("Explorador de Dados")
    
    with st.expander("Filtros Avançados", expanded=False):
        f1, f2, f3 = st.columns(3)
        term = f1.text_input("Buscar em comentários:", placeholder="Ex: atraso...")
        scores = f2.multiselect("Filtrar por Nota:", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5])
        
        stats = full_df["order_status"].unique().tolist() if "order_status" in full_df.columns else ["delivered"]
        states = f3.multiselect("Status:", stats, default=stats[:1] if stats else [])
        
    # Filtering Pipeline
    view = full_df.copy()
    if term and "review_comment_message" in view.columns:
        view = view[view["review_comment_message"].astype(str).str.contains(term, case=False, na=False)]
    if scores and "review_score" in view.columns:
        view = view[view["review_score"].isin(scores)]
    if states and "order_status" in view.columns:
        view = view[view["order_status"].isin(states)]
        
    st.dataframe(
        view[["order_id", "order_status", "review_score", "review_comment_title", "review_comment_message", "order_purchase_timestamp"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "order_id": "ID", "order_status": "Status", 
            "review_score": st.column_config.NumberColumn("Nota", format="%d"),
            "order_purchase_timestamp": st.column_config.DatetimeColumn("Data", format="D/M/Y H:mm")
        }
    )


# --- MAIN ENTRY POINT ------------------------------------------------------------------

def main() -> None:
    """
    Main Execution Loop.
    Structure: Init -> Sidebar/Load -> Process -> Render.
    """
    init_system()
    
    # 1. Sidebar UI
    uploaded_files = {}
    with st.sidebar:
        st.title("ZIGGWAY")
        st.markdown("[GitHub Profile](https://github.com/juan-barross/)")
        st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)
        nav_mode = st.radio(
            "NAVEGAÇÃO", 
            ["Visão Estratégica", "Experiência do Cliente"], 
            label_visibility="collapsed"
        )
        
        st.divider()
        
        st.markdown("""
        <div style="
            background: linear-gradient(145deg, rgba(20, 20, 20, 0.95) 0%, rgba(30, 30, 30, 0.8) 100%);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 18px 20px;
            border-radius: 8px;
            margin-bottom: 24px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            position: relative;
            overflow: hidden;
        ">
            <div style="
                position: absolute;
                top: 0;
                right: 0;
                width: 60px;
                height: 60px;
                background: radial-gradient(circle, rgba(212, 175, 55, 0.1) 0%, transparent 70%);
                pointer-events: none;
            "></div>
            <p style="
                color: #FFFFFF; 
                font-family: 'Playfair Display', serif; 
                font-size: 0.95rem; 
                font-weight: 600; 
                letter-spacing: 0.5px;
                margin: 0 0 8px 0;
                display: flex;
                align-items: center;
                gap: 8px;
            ">
                Ambiente de Demonstração
            </p>
            <p style="
                color: #B0B0B0; 
                font-family: 'Inter', sans-serif; 
                font-size: 0.82rem; 
                margin: 0; 
                line-height: 1.5;
                font-weight: 300;
            ">
                O sistema utiliza dados de exemplo. Para analisar sua própria operação, carregue seus arquivos de Pedidos, Avaliações e Pagamentos abaixo.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("Carregar Dados", expanded=False):
            st.markdown("""
<div style="margin-bottom: 20px;">
<div class="doc-card">
<div class="doc-title">Orders <span class="doc-tag">olist_orders_dataset.csv</span></div>
<div class="doc-item"><b>order_id</b> : ID único</div>
<div class="doc-item"><b>customer_id</b> : ID do cliente</div>
<div class="doc-item"><b>order_status</b> : Status</div>
<div class="doc-item"><b>purchase_timestamp</b> : Data da compra</div>
</div>

<div class="doc-card">
<div class="doc-title">Reviews <span class="doc-tag">olist_order_reviews_dataset.csv</span></div>
<div class="doc-item"><b>order_id</b> : Chave estrangeira</div>
<div class="doc-item"><b>review_score</b> : Nota (1-5)</div>
<div class="doc-item"><b>comment_message</b> : Texto da review</div>
</div>

<div class="doc-card">
<div class="doc-title">Payments <span class="doc-tag">olist_order_payments_dataset.csv</span></div>
<div class="doc-item"><b>order_id</b> : Chave estrangeira</div>
<div class="doc-item"><b>payment_value</b> : Valor pago</div>
</div>
</div>
""", unsafe_allow_html=True)
            
            st.divider()
            
            # --- ORDERS ---
            st.markdown("""
<div style="background: transparent; border-left: 3px solid #D4AF37; padding: 10px 12px; border-radius: 6px; margin-bottom: 8px;">
    <div style="color: #F0F0F0; font-weight: 600; font-size: 0.85rem; margin-bottom: 4px;">Pedidos</div>
    <div style="color: #777; font-size: 0.65rem; line-height: 1.4;">
        Colunas: <code style="background:transparent; color:#AAA;">order_id</code>, <code style="background:transparent; color:#AAA;">customer_id</code>, <code style="background:transparent; color:#AAA;">order_status</code>, <code style="background:transparent; color:#AAA;">order_purchase_timestamp</code>
    </div>
</div>
""", unsafe_allow_html=True)
            f_ord = st.file_uploader("Carregar Pedidos", type=['csv', 'xlsx', 'parquet', 'json'], key="uploader_orders", label_visibility="collapsed")
            
            # --- PAYMENTS ---
            st.markdown("""
<div style="background: transparent; border-left: 3px solid #D4AF37; padding: 10px 12px; border-radius: 6px; margin-bottom: 8px;">
    <div style="color: #F0F0F0; font-weight: 600; font-size: 0.85rem; margin-bottom: 4px;">Pagamentos</div>
    <div style="color: #777; font-size: 0.65rem; line-height: 1.4;">
        Colunas: <code style="background:transparent; color:#AAA;">order_id</code>, <code style="background:transparent; color:#AAA;">payment_value</code>
    </div>
</div>
""", unsafe_allow_html=True)
            f_pay = st.file_uploader("Carregar Pagamentos", type=['csv', 'xlsx', 'parquet', 'json'], key="uploader_payments", label_visibility="collapsed")
            
            # --- REVIEWS ---
            st.markdown("""
<div style="background: transparent; border-left: 3px solid #D4AF37; padding: 10px 12px; border-radius: 6px; margin-bottom: 8px;">
    <div style="color: #F0F0F0; font-weight: 600; font-size: 0.85rem; margin-bottom: 4px;">Avaliações</div>
    <div style="color: #777; font-size: 0.65rem; line-height: 1.4;">
        Colunas: <code style="background:transparent; color:#AAA;">order_id</code>, <code style="background:transparent; color:#AAA;">review_score</code>, <code style="background:transparent; color:#AAA;">review_comment_message</code>
    </div>
</div>
""", unsafe_allow_html=True)
            f_rev = st.file_uploader("Carregar Avaliações", type=['csv', 'xlsx', 'parquet', 'json'], key="uploader_reviews", label_visibility="collapsed")
            
            if f_ord: uploaded_files["orders"] = f_ord
            if f_pay: uploaded_files["payments"] = f_pay
            if f_rev: uploaded_files["reviews"] = f_rev
            
            st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)

    # 2. Data Processing (Fail Fast)
    result = data_ingestion_pipeline(uploaded_files)
    
    if result.status_code != 0:
        st.error("FATAL: Dados insuficientes. Carregue os arquivos ou gere o mock dataset.")
        return # STOP EXECUTION

    # 3. Create Context
    ctx = PageContext(
        df=result.full_df, 
        ltv=result.ltv_df, 
        churn=result.churn_df,
        analyzer=st.session_state.analyzer
    )

    # 4. Dispatch Render
    if nav_mode == "Visão Estratégica":
        render_dashboard(ctx)
    elif nav_mode == "Experiência do Cliente":
        render_command_center(ctx)

if __name__ == "__main__":
    main()
# Updated
