import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re
import os
import streamlit.components.v1 as components

# --- CONFIGURATION SYSTÈME ---
st.set_page_config(page_title="OIL INTELLIGENCE PRO", layout="wide", page_icon="⛽")

# Emplacement du fichier
DB_FILE = "historique_platts.csv"

# --- STYLE PRO ---
st.markdown("""
    <style>
    .main { background-color: #050505; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #00ffc8; }
    .stMetric { background-color: #111111; border: 1px solid #333; padding: 15px; border-radius: 8px; }
    .decision-box { padding: 30px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 1.8rem; border: 2px solid #333; margin: 20px 0; }
    </style>
""", unsafe_allow_html=True)

# --- FONCTIONS DE DONNÉES (SÉCURISÉES) ---
def init_db():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["Date", "SP95", "GO", "FOD", "EURUSD_Email"])
        df.to_csv(DB_FILE, index=False)

def load_data():
    init_db()
    try:
        return pd.read_csv(DB_FILE)
    except:
        return pd.DataFrame(columns=["Date", "SP95", "GO", "FOD", "EURUSD_Email"])

# Initialisation immédiate
init_db()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    show_demo = st.checkbox("📖 Mode Aide", value=False)
    
    if st.button("🗑️ Réinitialiser"):
        df = pd.DataFrame(columns=["Date", "SP95", "GO", "FOD", "EURUSD_Email"])
        df.to_csv(DB_FILE, index=False)
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    st.header("📩 Importation Platts")
    email_input = st.text_area("Collez l'email ici :", height=150)
    
    if st.button("🚀 Archiver"):
        if email_input:
            patterns = {"SP95": r"SP95\s+([\d\.,\s]+)", "GO": r"GO\s+([\d\.,\s]+)", "FOD": r"FOD\s+([\d\.,\s]+)", "EURUSD_Email": r"([\d\.,]+)\s+€/\$"}
            extracted = {}
            for k, p in patterns.items():
                match = re.search(p, email_input)
                if match:
                    val = match.group(1).replace(',', '.').replace(' ', '')
                    extracted[k] = float(val)
            
            if extracted.get("GO"):
                hist = load_data()
                today = datetime.now().strftime("%Y-%m-%d")
                new_row = pd.DataFrame([{"Date": today, **extracted}])
                updated = pd.concat([hist[hist['Date'] != today], new_row]).sort_values("Date")
                updated.to_csv(DB_FILE, index=False)
                st.success("Archivé !")
                st.rerun()

    st.divider()
    brent_live = st.number_input("Brent ($) actuel :", value=0.0, step=0.1)

# --- DASHBOARD MAIN ---
st.title("🛡️ OIL INTELLIGENCE PRO")

# 1. GRAPHIQUE TRADINGVIEW (Isolé pour éviter le blocage)
st.subheader("📊 Marché en Direct (Brent)")
components.html("""
<div style="height:450px; width:100%; border-radius:12px; overflow:hidden; border: 1px solid #333;">
    <div id="tv_chart" style="height:100%; width:100%;"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget({
      "autosize": true, "symbol": "TVC:UKOIL", "interval": "15", "theme": "dark", 
      "style": "2", "locale": "fr", "container_id": "tv_chart", "details": true
    });
    </script>
</div>
""", height=460)

# 2. ANALYSE DES DONNÉES
df_hist = load_data()

if show_demo and st.button("🧪 Générer Démo 7j"):
    demo_data = []
    for i in range(7, 0, -1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        demo_data.append({"Date": date, "SP95": 810.0+i, "GO": 830.0+(i*1.5), "FOD": 790.0, "EURUSD_Email": 1.085})
    pd.DataFrame(demo_data).to_csv(DB_FILE, index=False)
    st.rerun()

if not df_hist.empty:
    st.divider()
    
    # DÉCISION
    if brent_live > 0:
        col_dec, col_met = st.columns([2, 1])
        with col_dec:
            if brent_live > 82.0:
                st.markdown("<div class='decision-box' style='background-color: #4b0000; color: #ff4b4b;'>⚠️ ALERTE HAUSSE</div>", unsafe_allow_html=True)
            elif brent_live < 79.0:
                st.markdown("<div class='decision-box' style='background-color: #002b11; color: #00ffc8;'>✅ OPPORTUNITÉ</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='decision-box' style='background-color: #111; color: #ccc;'>⚖️ MARCHÉ STABLE</div>", unsafe_allow_html=True)
        with col_met:
            last_val = df_hist['GO'].iloc[-1]
            st.metric("Dernier Platts GO", f"{last_val} €")

    # GRAPHIQUE HISTORIQUE
    st.subheader("📈 Corrélation Platts")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_hist['Date'], y=df_hist['GO'], name="GO (€)", line=dict(color='#00ffc8', width=3)))
    fig.update_layout(template="plotly_dark", height=350, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aucune donnée. Activez le 'Mode Aide' pour générer une démo.")
