import streamlit as st
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import plotly.express as px 
import os
from fpdf import FPDF
import base64
from dotenv import load_dotenv
load_dotenv()

# Fonction pour se connecter à Supabase
def create_supabase_connection():
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=os.getenv("https://pqukveuzxrtoatjjvhyn.supabase.co"),
            password=os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBxdWt2ZXV6eHJ0b2F0amp2aHluIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzkxNzc4NDYsImV4cCI6MjA1NDc1Mzg0Nn0.hdIRmqYwYxh8Lu2UnPjNDdoEijtel7NfQFN_Y8s8v3A"),
            host=os.getenv("https://pqukveuzxrtoatjjvhyn.supabase.co"),
            port=5432
        )
        return conn  # Retourne la connexion si elle réussit
    except Exception as e:
        st.error(f"Erreur de connexion à Supabase : {e}")
        return None

# Classe pour créer un PDF
class FacturePDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Entreprise DIEUDONNE", ln=True, align="C")
        self.cell(0, 10, "Adresse : ANCIEN SOBRAGA, LIBREVILLE", ln=True, align="C")
        self.cell(0, 10, "Téléphone : +241 74 67 70 71", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def add_facture_details(self, data):
        self.set_font("Arial", "", 10)
        col_width = 40
        row_height = 10
        for row in data:
            for item in row:
                self.cell(col_width, row_height, str(item), border=1)
            self.ln(row_height)

# Fonction pour générer un PDF
def generate_pdf(facture_data, filename, client_name):
    pdf = FacturePDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Client : {client_name}", ln=True, align="L")
    pdf.ln(10)
    pdf.add_facture_details(facture_data)
    pdf.output(filename)

# Fonction pour encoder le fichier PDF en base64 (pour le téléchargement)
def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{os.path.basename(bin_file)}">{file_label}</a>'
    return href

# Initialisation de l'état de session
if "produits" not in st.session_state:
    st.session_state.produits = []
if "total" not in st.session_state:
    st.session_state.total = 0
if "ajout_produit_visible" not in st.session_state:
    st.session_state.ajout_produit_visible = False
if "page" not in st.session_state:
    st.session_state.page = 1

# Interface Streamlit
st.title("Gestion de Factures et Analyse des Données")

# Menu structuré avec onglets
selected_option = st.sidebar.selectbox(
    "Menu",
    ["Créer une Facture", "Historique des Factures", "Analyse des Données"],
    format_func=lambda x: f"∶ {x} ∶"
)

if selected_option == "Créer une Facture":
    st.header("∶ Créer une Facture ∶")
    col_client, col_produits = st.columns([1, 2])
    with col_client:
        type_facture = st.selectbox("∶ Type de Facture ∶", ["Proforma", "Définitive"])
        client_name = st.text_input("∶ Nom du Client ∶")

    with col_produits:
        if st.button("∶ Ajouter un Produit ∶", key="add_product"):
            st.session_state.ajout_produit_visible = True

        if st.session_state.ajout_produit_visible:
            with st.form(key="form_ajout_produit"):
                produit = {}
                produit["nom"] = st.text_input("∶ Nom du Produit ∶", key="nom_produit")
                produit["quantite"] = st.number_input("∶ Quantité ∶", min_value=1, value=1, key="quantite")
                produit["prix_unitaire"] = st.number_input("∶ Prix Unitaire (FCFA) ∶", min_value=0.0, value=0.0, key="prix_unitaire")
                submitted = st.form_submit_button("∶ Valider Produit ∶")
                if submitted:
                    if produit["nom"] and produit["prix_unitaire"] > 0:
                        produit["montant"] = produit["quantite"] * produit["prix_unitaire"]
                        st.session_state.total += produit["montant"]
                        st.session_state.produits.append(produit)
                        st.session_state.ajout_produit_visible = False
                    else:
                        st.warning("∶ Veuillez remplir tous les champs correctement ∶")

    if st.session_state.produits:
        col_details, col_actions = st.columns([2, 1])
        with col_details:
            st.write("∶ Détails des Produits ∶")
            df_produits = pd.DataFrame(st.session_state.produits)
            st.table(df_produits[["nom", "quantite", "prix_unitaire", "montant"]])

            tva = st.session_state.total * 0.18  # 18%
            css = st.session_state.total * 0.01  # 1%
            total_ttc = st.session_state.total + tva + css
            st.write(f"∶ Total HT ∶ {st.session_state.total:.2f} FCFA")
            st.write(f"∶ TVA (18%) ∶ {tva:.2f} FCFA")
            st.write(f"∶ CSS (1%) ∶ {css:.2f} FCFA")
            st.write(f"∶ Total TTC ∶ {total_ttc:.2f} FCFA")

        with col_actions:
            if st.button("∶ Enregistrer Facture ∶", key="enregistrer"):
                if not client_name or not st.session_state.produits:
                    st.warning("∶ Veuillez remplir tous les champs nécessaires ∶")
                else:
                    produits_str = str(st.session_state.produits)
                    tva = st.session_state.total * 0.18  # 18%
                    css = st.session_state.total * 0.01  # 1%
                    total_ttc = st.session_state.total + tva + css

                    conn = create_supabase_connection()
                    if conn is None:
                        st.stop()

                    cursor = conn.cursor()
                    try:
                        cursor.execute("""
                            INSERT INTO Factures (type, client_name, produits, total, tva, css, montant_ttc)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (type_facture, client_name, produits_str, st.session_state.total, tva, css, total_ttc))

                        for produit in st.session_state.produits:
                            cursor.execute("""
                                INSERT INTO Ventes (date, produit, montant)
                                VALUES (%s, %s, %s)
                            """, (pd.Timestamp.now().date(), produit["nom"], produit["montant"]))

                        conn.commit()
                        st.success(f"∶ Facture {type_facture} enregistrée avec succès ! ∶")
                    except Exception as e:
                        st.error(f"Erreur lors de l'enregistrement : {e}")
                    finally:
                        cursor.close()
                        conn.close()

            if st.button("∶ Générer PDF ∶", key="pdf"):
                if not client_name:
                    st.warning("∶ Veuillez entrer le nom du client ∶")
                elif not st.session_state.produits:
                    st.warning("∶ Veuillez ajouter au moins un produit ∶")
                else:
                    tva = st.session_state.total * 0.18  # 18%
                    css = st.session_state.total * 0.01  # 1%
                    total_ttc = st.session_state.total + tva + css

                    facture_data = [["Description", "Quantité", "Prix Unitaire (FCFA)", "Montant (FCFA)"]]
                    for produit in st.session_state.produits:
                        facture_data.append([produit["nom"], produit["quantite"], f"{produit['prix_unitaire']:.2f}", f"{produit['montant']:.2f}"])
                    facture_data.append(["", "", "Total HT", f"{st.session_state.total:.2f} FCFA"])
                    facture_data.append(["", "", "TVA (18%)", f"{tva:.2f} FCFA"])
                    facture_data.append(["", "", "CSS (1%)", f"{css:.2f} FCFA"])
                    facture_data.append(["", "", "Total TTC", f"{total_ttc:.2f} FCFA"])

                    filename = f"facture_{type_facture.lower()}.pdf"
                    generate_pdf(facture_data, filename, client_name)
                    st.success(f"∶ Facture {type_facture} générée avec succès ! ∶")
                    st.markdown(get_binary_file_downloader_html(filename, f"∶ Facture {type_facture} ∶"), unsafe_allow_html=True)

            if st.button("∶ Nouvelle Facture ∶", key="nouvelle_facture"):
                st.session_state.produits = []
                st.session_state.total = 0
                st.info("∶ Les données de la facture ont été réinitialisées. Vous pouvez créer une nouvelle facture. ∶")

elif selected_option == "Historique des Factures":
    st.header("∶ Historique des Factures ∶")

    conn = create_supabase_connection()
    if conn is None:
        st.stop()

    cursor = conn.cursor()
    cursor.execute("SELECT id, type, client_name, total, tva, css, montant_ttc FROM Factures")
    factures = cursor.fetchall()

    if factures:
        items_per_page = 10
        start_idx = (st.session_state.page - 1) * items_per_page
        end_idx = st.session_state.page * items_per_page
        paginated_factures = factures[start_idx:end_idx]

        formatted_factures = []
        for facture in paginated_factures:
            formatted_facture = list(facture[:3])  # ID, Type, Client
            formatted_facture.extend([f"{facture[3]:.2f}", f"{facture[4]:.2f}", f"{facture[5]:.2f}", f"{facture[6]:.2f}"])
            formatted_factures.append(formatted_facture)

        df_factures = pd.DataFrame(formatted_factures, columns=["ID", "Type", "Client", "Total HT (FCFA)", "TVA (FCFA)", "CSS (FCFA)", "Montant TTC (FCFA)"])
        st.table(df_factures)

        total_pages = (len(factures) + items_per_page - 1) // items_per_page
        col_prev, col_next = st.columns([1, 1])
        with col_prev:
            if st.button("∶ Previous ∶") and st.session_state.page > 1:
                st.session_state.page -= 1
        with col_next:
            if st.button("∶ Next ∶") and st.session_state.page < total_pages:
                st.session_state.page += 1
        st.write(f"∶ Page {st.session_state.page} sur {total_pages} ∶")

        facture_id = st.number_input("∶ Rechercher une facture par ID ∶", min_value=1, value=1)
        if st.button("∶ Chercher Facture ∶"):
            cursor.execute("SELECT * FROM Factures WHERE id=%s", (facture_id,))
            facture = cursor.fetchone()
            if facture:
                produits = eval(facture[3]) if facture[3] else []
                total_ht = f"{facture[4]:.2f}" if facture[4] is not None else "0.00"
                tva = f"{facture[5]:.2f}" if facture[5] is not None else "0.00"
                css = f"{facture[6]:.2f}" if facture[6] is not None else "0.00"
                montant_ttc = f"{facture[7]:.2f}" if facture[7] is not None else "0.00"
                st.write(f"∶ Facture trouvée ∶ Type={facture[1]}, Client={facture[2]}")
                st.write(f"∶ Total HT ∶ {total_ht} FCFA")
                st.write(f"∶ TVA (18%) ∶ {tva} FCFA")
                st.write(f"∶ CSS (1%) ∶ {css} FCFA")
                st.write(f"∶ Montant TTC ∶ {montant_ttc} FCFA")
                st.table(pd.DataFrame(produits))
            else:
                st.warning("∶ Aucune facture correspondante ∶")

    else:
        st.info("∶ Aucune facture enregistrée ∶")

    cursor.close()
    conn.close()

elif selected_option == "Analyse des Données":
    st.header("∶ Analyse des Données ∶")

    conn = create_supabase_connection()
    if conn is None:
        st.stop()

    cursor = conn.cursor()
    cursor.execute("SELECT date, produit, montant FROM Ventes")
    ventes_data = cursor.fetchall()

    if ventes_data:
        df_ventes = pd.DataFrame(ventes_data, columns=["Date", "Produit", "Montant (FCFA)"])
        df_ventes["Date"] = pd.to_datetime(df_ventes["Date"])

        col_graph1, col_graph2 = st.columns([1, 1])
        with col_graph1:
            grouped_by_produit = df_ventes.groupby("Produit", as_index=False).agg({"Montant (FCFA)": "sum"})
            fig = px.bar(
                grouped_by_produit,
                x="Produit",
                y="Montant (FCFA)",
                title="∶ Répartition des ventes par produit ∶",
                labels={"Montant (FCFA)": "∶ Montant Total (FCFA) ∶"}
            )
            fig.update_layout(xaxis={'categoryorder': 'total descending'})
            st.plotly_chart(fig)

        with col_graph2:
            df_ventes["Date"] = df_ventes["Date"].dt.strftime("%Y-%m-%d")
            fig2 = px.line(
                df_ventes,
                x="Date",
                y="Montant (FCFA)",
                color="Produit",
                title="∶ Évolution des ventes par produit ∶"
            )
            st.plotly_chart(fig2)

    else:
        st.info("∶ Aucune donnée de vente disponible ∶")

    cursor.close()
    conn.close()