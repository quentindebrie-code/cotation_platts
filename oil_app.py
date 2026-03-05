import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re
import os
import streamlit.components.v1 as components

# --- CONFIGURATION SYSTÈME ---
st.set_page_config(page_title="OIL INTELLIGENCE PRO", layout="wide", page_icon="⛽")

DB_FILE = "historique_platts.csv"
if not os.path.exists(DB_FILE):
    pd.DataFrame(columns=["Date", "SP95", "GO", "FOD", "EURUSD_Email"]).to_csv(DB_FILE, index=False)

# --- STYLE ---
st.markdown("""
    <style>
    .main { background-color: #050505; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #00ffc8; }
    .stMetric { background-color: #111111; border: 1px solid #333; padding: 15px; border-radius: 8px; }
    .demo-box { background-color: #001f3f; border-left: 5px solid #0074D9; padding: 20px; border-radius: 10px; margin-bottom: 25px; }
    .decision-box { padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; font-size: 1.5rem; border: 2px solid #333; }
    </style>
""", unsafe_allow_html=True)

# --- FONCTION DE NETTOYAGE ---
def reset_database():
    pd.DataFrame(columns=["Date", "SP95", "GO", "FOD", "EURUSD_Email"]).to_csv(DB_FILE, index=False)
    st.cache_data.clear()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    show_demo = st.checkbox("📖 Mode Démo / Aide", value=False)
    
    # BOUTON DE PURGE (SÉCURISÉ)
    if st.button("🗑️ Supprimer TOUTES les données", help="Efface l'historique Platts (y compris la démo)"):
        reset_database()
        st.warning("Base de données réinitialisée.")
        st.rerun()
    
    st.divider()
    st.header("📩 Importation Platts")
    email_input = st.text_area("Collez l'email ici :", height=100)
    if st.button("🚀 Archiver"):
        patterns = {"SP95": r"SP95\s+([\d\.,]+)", "GO": r"GO\s+([\d\.,]+)", "FOD": r"FOD\s+([\d\.,]+)", "EURUSD": r"([\d\.,]+)\s+€/\$"}
        data = {k: float(re.search(p, email_input).group(1).replace(',', '.')) if re.search(p, email_input) else 0.0 for k, p in patterns.items()}
        if data.get("GO", 0) > 0:
            new_row = pd.DataFrame([{"Date": datetime.now().strftime("%Y-%m-%d"), **data}])
            hist = pd.read_csv(DB_FILE)
            pd.concat([hist[hist['Date'] != new_row['Date'].iloc[0]], new_row]).to_csv(DB_FILE, index=False)
            st.rerun()

    st.divider()
    st.header("🎯 Flux Live")
    brent_input = st.number_input("Brent ($) du graphique :", value=0.0, step=0.01)

# --- DASHBOARD MAIN ---
st.title("🛡️ OIL INTELLIGENCE PRO")

# MODULE DE DÉMO
df_check = pd.read_csv(DB_FILE)
if show_demo or len(df_check) == 0:
    with st.container():
        st.markdown("""
        <div class="demo-box">
            <h3>Guide de démarrage & Test rapide</h3>
            <li><b>Utilisez le bouton ci-dessous pour injecter des données fictives. <b>Une fois terminé, utilisez le bouton "Supprimer" dans la barre latérale pour nettoyer votre historique.</b></li><br>
            <li><b>Le cours du Brent :</b> le graphique ci-dessous offre une vision en quasi-temps-réel (latence de 5 secondes) des variations du cours du Brent. Il est possible de zoomer dans le graphique, de changer la forme des courbes, ou encore de comparer différents cours.</li><br>    
            <li><b>La colonne latérale :</b> "Importation Platts" - Copiez-collez l'email de cotation Platts chaque matin dans l'outil.</li><br>
            <li><b>La colonne latérale :</b> "Flux Live" - Renseignez le cours du Brent afin que l'outil définisse s'il y a une opportunité ou un risque à l'achat.</li>                        
                    
        </div>
        """, unsafe_allow_html=True)
        if st.button("🧪 Générer 7 jours de démo"):
            demo_data = []
            for i in range(7, 0, -1):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                demo_data.append({"Date": date, "SP95": 820.0 + i, "GO": 840.0 + (i * 2), "FOD": 800.0, "EURUSD_Email": 1.0850})
            pd.DataFrame(demo_data).to_csv(DB_FILE, index=False)
            st.rerun()

# 1. RADAR LIVE (TRADINGVIEW)
components.html("""
<div style="height:500px; width:100%; border-radius:10px; overflow:hidden;">
    <div id="tv_chart" style="height:100%; width:100%;"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget({
      "autosize": true, "symbol": "TVC:UKOIL", "interval": "15", "theme": "dark", "style": "2", "locale": "fr", "container_id": "tv_chart", "details": true
    });
    </script>
</div>
""", height=510)

# 2. COURBE & MOTEUR DE DÉCISION
df_hist = pd.read_csv(DB_FILE)
if not df_hist.empty:
    st.divider()
    if brent_input > 0:
        # Seuil d'alerte dynamique (simple démo)
        if brent_input > 81.0:
            st.markdown("<div class='decision-box' style='background-color: #4b0000; color: #ff4b4b;'>⚠️ ALERTE HAUSSE : ACHETEZ MAINTENANT</div>", unsafe_allow_html=True)
        elif brent_input < 78.0:
            st.markdown("<div class='decision-box' style='background-color: #002b11; color: #00ffc8;'>✅ OPPORTUNITÉ : ATTENDEZ DEMAIN</div>", unsafe_allow_html=True)

    # GRAPHIQUE AVEC TOOLTIPS RÉACTIVÉS
    st.subheader("📈 Corrélation Historique (Détails au survol)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_hist['Date'], 
        y=df_hist['GO'], 
        name="Gasoil (€)", 
        line=dict(color='#00ffc8', width=4),
        mode='lines+markers',
        hovertemplate="<b>Date:</b> %{x}<br><b>Prix:</b> %{y:.2f}€<extra></extra>" # TOOLTIP CONFIGURÉ ICI
    ))
    
    fig.update_layout(
        template="plotly_dark", 
        height=350, 
        margin=dict(l=0,r=0,t=0,b=0),
        hovermode="x unified", # Tooltip synchronisé sur l'axe X
        xaxis=dict(showgrid=True, gridcolor='#222'),
        yaxis=dict(showgrid=True, gridcolor='#222')
    )
    st.plotly_chart(fig, use_container_width=True)