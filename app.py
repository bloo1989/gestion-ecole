import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# ===================== CONFIGURATION & SÉCURITÉ =====================
st.set_page_config(page_title="Scolarité Cloud", layout="wide", page_icon="☁️")

# URL de ta Google Sheet (METS TON LIEN ICI)
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1uYPNoVR2vICZxtVzhKj1L0INV1axd2rU0ZeG_zyji4k/edit?usp=sharing"

PASSWORD_ADMIN = "admin123"

def check_password():
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if not st.session_state["auth"]:
        st.title("🔐 Connexion Cloud")
        pwd = st.text_input("Mot de passe :", type="password")
        if st.button("Entrer"):
            if pwd == PASSWORD_ADMIN:
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Accès refusé.")
        return False
    return True

if check_password():
    # Connexion à Google Sheets
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Lecture des données
    try:
        df = conn.read(spreadsheet=GSHEET_URL)
    except:
        st.error("Erreur de connexion à Google Sheets. Vérifiez le lien et les droits d'accès.")
        st.stop()

    # ===================== BARRE LATÉRALE =====================
    st.sidebar.title("🎒 GESTION CLOUD")
    if st.sidebar.button("🚪 Déconnexion"):
        st.session_state["auth"] = False
        st.rerun()
    
    menu = st.sidebar.radio("Navigation", ["📊 Dashboard", "📝 Inscription", "💰 Paiement", "📋 Registre", "🧾 Reçu"])

    # ===================== FONCTION SAUVEGARDE =====================
    def save_data(dataframe):
        conn.update(spreadsheet=GSHEET_URL, data=dataframe)
        st.cache_data.clear()

    # ===================== 📊 DASHBOARD =====================
    if menu == "📊 Dashboard":
        st.header("Statistiques en Temps Réel")
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Inscrits", len(df))
            c2.metric("Encaissé", f"{df['paye'].sum():,} F")
            c3.metric("À percevoir", f"{df['reste'].sum():,} F", delta_color="inverse")
            st.divider()
            st.bar_chart(df['classe'].value_counts())
        else: st.info("Aucune donnée disponible.")

    # ===================== 📝 INSCRIPTION =====================
    elif menu == "📝 Inscription":
        st.header("Nouvel Élève")
        with st.form("form_inscr", clear_on_submit=True):
            col1, col2 = st.columns(2)
            n, p = col1.text_input("Nom"), col1.text_input("Prénom")
            cl = col1.selectbox("Classe", ["6è", "5è", "4è", "3è", "2nde", "1ère", "Tle"])
            t = col2.text_input("Téléphone")
            tot = col2.number_input("Total", value=50000, step=5000)
            pa = col2.number_input("Acompte", value=0, step=5000)
            
            if st.form_submit_button("Enregistrer sur le Cloud"):
                if n and p and t:
                    res = tot - pa
                    new_row = pd.DataFrame([{"id": len(df)+1, "date": datetime.now().strftime("%d/%m/%Y"), "nom": n.upper(), "prenom": p.title(), "classe": cl, "tel": t, "total": tot, "paye": pa, "reste": res, "statut": "SOLDE" if res<=0 else "RETARD"}])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success("Données synchronisées avec Google Sheets !")
                    st.balloons()

    # ===================== 💰 PAIEMENT =====================
    elif menu == "💰 Paiement":
        st.header("Mettre à jour un versement")
        if not df.empty:
            idx = st.selectbox("Élève", df.index, format_func=lambda x: f"{df.loc[x,'nom']} {df.loc[x,'prenom']}")
            st.warning(f"Reste : {df.loc[idx, 'reste']:,} F")
            montant = st.number_input("Montant versé", min_value=0, max_value=int(df.loc[idx, 'reste']), step=1000)
            
            if st.button("Confirmer et Sauvegarder"):
                df.at[idx, 'paye'] += montant
                df.at[idx, 'reste'] -= montant
                df.at[idx, 'statut'] = "SOLDE" if df.at[idx, 'reste'] <= 0 else "RETARD"
                save_data(df)
                st.success("Paiement validé !")
        else: st.warning("Registre vide.")

    # ===================== 📋 REGISTRE =====================
    elif menu == "📋 Registre":
        st.header("Liste des élèves")
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ===================== 🧾 REÇU =====================
    elif menu == "🧾 Reçu":
        st.header("Générer Reçu")
        if not df.empty:
            idx = st.selectbox("Sélectionner l'élève", df.index, format_func=lambda x: f"{df.loc[x,'nom']} {df.loc[x,'prenom']}")
            e = df.loc[idx]
            html = f"""<div style="border:5px solid #1e40af; padding:20px; text-align:center; font-family:sans-serif;">
                <h2>REÇU DE SCOLARITÉ</h2><hr>
                <p><b>{e['prenom']} {e['nom']}</b> ({e['classe']})</p>
                <p>Payé : <b>{e['paye']:,} FCFA</b> | Reste : <b>{e['reste']:,} FCFA</b></p>
            </div>"""
            st.components.v1.html(html, height=250)
            st.download_button("Télécharger", html, f"Recu_{e['nom']}.html")
