import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re
import os
import streamlit.components.v1 as components

# --- CONFIGURATION SYSTÈME ---
st.set_page_config(page_title="OIL INTELLIGENCE PRO", layout="wide", page_icon="⛽")

# NOM DU FICHIER (Note : Sur Streamlit Cloud, ce fichier est éphémère)
DB_FILE = "historique_platts.csv"

# --- STYLE PRO ---
st.markdown("""
    <style>
    .main { background-color: #050505; }
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #00ffc8; }
    .stMetric { background-color: #111111; border: 1px solid #333; padding: 15px; border-radius: 8px; }
    .demo-box { background-color: #001f3f; border-left: 5px solid #0074D9; padding: 20px; border-radius: 10px; margin-bottom: 25px; }
    .decision-box { padding: 30px; border-radius: 12px; text-align: center; font-weight: bold; font-size: 1.8rem; border: 2px solid #333; margin: 20px 0; }
    </style>
""", unsafe_allow_html=True)

# --- FONCTIONS DE DONNÉES ---
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Date", "SP95", "GO", "FOD", "EURUSD_Email"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def reset_database():
    df = pd.DataFrame(columns=["Date", "SP95", "GO", "FOD", "EURUSD_Email"])
    save_data(df)
    st.cache_data.clear()

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Configuration")
    show_demo = st.checkbox("📖 Mode Démo / Aide", value=False)
    
    if st.button("🗑️ Réinitialiser la Base", help="Efface tout l'historique"):
        reset_database()
        st.warning("Base vidée.")
        st.rerun()
    
    st.divider()
    st.header("📩 Importation Platts")
    email_input = st.text_area("Collez l'email Platts ici :", height=150, placeholder="SP95 820.50 ... 1.0850 €/$")
    
    if st.button("🚀 Archiver la Cotation"):
        if email_input:
            try:
                patterns = {
                    "SP95": r"SP95\s+([\d\.,\s]+)", 
                    "GO": r"GO\s+([\d\.,\s]+)", 
                    "FOD": r"FOD\s+([\d\.,\s]+)", 
                    "EURUSD_Email": r"([\d\.,]+)\s+€/\$"
                }
                
                extracted = {}
                for k, p in patterns.items():
                    match = re.search(p, email_input)
                    if match:
                        val = match.group(1).replace(',', '.').replace(' ', '')
                        extracted[k] = float(val)
                    else:
                        extracted[k] = 0.0
                
                if extracted.get("GO", 0) > 0:
                    hist = load_data()
                    today = datetime.now().strftime("%Y-%m-%d")
                    new_row = pd.DataFrame([{"Date": today, **extracted}])
                    
                    # Mise à jour (écrase si date identique)
                    updated_hist = pd.concat([hist[hist['Date'] != today], new_row]).sort_values("Date")
                    save_data(updated_hist)
                    st.success("Données archivées avec succès !")
                    st.rerun()
                else:
                    st.error("Format d'email non reconnu. Vérifiez les valeurs GO.")
            except Exception as e:
                st.error(f"Erreur d'analyse : {e}")
        else:
            st.warning("Veuillez coller un texte.")

    st.divider()
    st.header("🎯 Flux Live")
    brent_live = st.number_input("Brent ($) actuel :", value=0.0, step=0.01, help="Saisissez la valeur lue sur le graphique TradingView")

# --- DASHBOARD MAIN ---
st.title("🛡️ OIL INTELLIGENCE PRO")

df_hist = load_data()

# MODULE DE DÉMO
if show_demo or df_hist.empty:
    with st.container():
        st.markdown("""
        <div class="demo-box">
            <h3>🚀 Guide Expert - Andrea</h3>
            <p>1. <b>Importation :</b> Copiez l'email Platts chaque matin dans la barre latérale.<br>
            2. <b>TradingView :</b> Observez la tendance en direct (UKOIL).<br>
            3. <b>Décision :</b> Renseignez le prix du Brent live pour obtenir le verdict d'achat.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🧪 Générer des données de test (7j)"):
            demo_data = []
            for i in range(10, 0, -1):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                demo_data.append({
                    "Date": date, 
                    "SP95": 810.0 + (i * 1.5), 
                    "GO": 830.0 + (i * 2.1), 
                    "FOD": 790.0, 
                    "EURUSD_Email": 1.0850 + (i * 0.001)
                })
            save_data(pd.DataFrame(demo_data))
            st.rerun()

# 1. GRAPHIQUE TRADINGVIEW LIVE
components.html("""
<div style="height:500px; width:100%; border-radius:12px; overflow:hidden; border: 1px solid #333;">
    <div id="tv_chart" style="height:100%; width:100%;"></div>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script type="text/javascript">
    new TradingView.widget({
      "autosize": true, "symbol": "TVC:UKOIL", "interval": "15", "theme": "dark", 
      "style": "2", "locale": "fr", "container_id": "tv_chart", "details": true, "hotlist": true
    });
    </script>
</div>
""", height=510)

# 2. MOTEUR DE DÉCISION & VISUALISATION
if not df_hist.empty:
    st.divider()
    
    # CALCULS DE DÉCISION
    if brent_live > 0:
        # Logique de décision (Simplifiée pour l'exemple)
        # On compare le Brent Live à la moyenne des derniers jours
        avg_go = df_hist['GO'].tail(3).mean()
        
        col_dec, col_met = st.columns([2, 1])
        
        with col_dec:
            if brent_live > 82.5:
                st.markdown("<div class='decision-box' style='background-color: #4b0000; color: #ff4b4b;'>⚠️ ALERTE HAUSSE : ACHETEZ MAINTENANT</div>", unsafe_allow_html=True)
            elif brent_live < 79.0:
                st.markdown("<div class='decision-box' style='background-color: #002b11; color: #00ffc8;'>✅ OPPORTUNITÉ : ATTENDEZ DEMAIN</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='decision-box' style='background-color: #111; color: #ccc;'>⚖️ MARCHÉ STABLE : ACHAT NEUTRE</div>", unsafe_allow_html=True)
        
        with col_met:
            st.metric("Dernier Platts GO", f"{df_hist['GO'].iloc[-1]} €", delta=f"{df_hist['GO'].iloc[-1] - df_hist['GO'].iloc[-2]:.2f}€")

    # GRAPHIQUE D'HISTORIQUE PLOTLY
    st.subheader("📈 Corrélation & Historique Platts")
    
    fig = go.Figure()
    
    # Trace Gasoil
    fig.add_trace(go.Scatter(
        x=df_hist['Date'], y=df_hist['GO'],
        name="Gasoil (€)", mode='lines+markers',
        line=dict(color='#00ffc8', width=3),
        hovertemplate="<b>Date:</b> %{x}<br><b>GO:</b> %{y}€<extra></extra>"
    ))
    
    # Trace SP95 (optionnelle)
    fig.add_trace(go.Scatter(
        x=df_hist['Date'], y=df_hist['SP95'],
        name="SP95 (€)", mode='lines',
        line=dict(color='#ff4b4b', width=1, dash='dot'),
        visible='legendonly'
    ))

    fig.update_layout(
        template="plotly_dark",
        height=400,
        hovermode="x unified",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='#222', title="Dates de cotation"),
        yaxis=dict(showgrid=True, gridcolor='#222', title="Prix (€/Tonne)"),
        margin=dict(l=10, r=10, t=10, b=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # TABLEAU DE DONNÉES
    with st.expander("📊 Voir le tableau de données brut"):
        st.dataframe(df_hist.sort_values("Date", ascending=False), use_container_width=True)
else:
    st.info("En attente de données. Utilisez la démo ou importez un email Platts.")
