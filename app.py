import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import declarative_base, sessionmaker
import pandas as pd

# --- CONFIGURAZIONE DELLA PAGINA ---
st.set_page_config(page_title="Gestionale Clienti", page_icon="💼", layout="wide")
st.title("💼 Sistema Gestionale - Test Netsons")

# --- CONNESSIONE AL DATABASE ---
# Streamlit recupera in automatico la stringa dai "Secrets" impostati sulla piattaforma cloud
try:
    DATABASE_URL = st.secrets["database"]["url"]
except Exception:
    # Fallback locale se provi a lanciarlo sul computer senza configurare i segreti
    DATABASE_URL = "sqlite:///./test_locale.db"

# Inizializzazione del motore del database (pool_pre_ping previene disconnessioni improvvise)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELLO DATI (Tabella) ---
class Cliente(Base):
    __tablename__ = "clienti"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    azienda = Column(String(100), nullable=True)

# Crea automaticamente la tabella su Netsons all'avvio se non esiste
Base.metadata.create_all(bind=engine)

# --- INTERFACCIA GRAFICA (Streamlit Layout) ---

# Creiamo due colonne: a sinistra il modulo di inserimento, a destra la tabella riassuntiva
col_form, col_dati = st.columns([1, 2])

with col_form:
    st.subheader("➕ Inserisci Nuovo Cliente")
    
    # Utilizziamo uno Streamlit Form per raggruppare i campi di input
    with st.form("form_cliente", clear_on_submit=True):
        nome_input = st.text_input("Nome e Cognome *")
        email_input = st.text_input("Indirizzo Email *")
        azienda_input = st.text_input("Azienda / Società")
        
        submit_button = st.form_submit_button("Salva nel DB Netsons")
        
        if submit_button:
            if not nome_input or not email_input:
                st.error("I campi Nome ed Email sono obbligatori!")
            else:
                # Apertura sessione DB ed inserimento
                db = SessionLocal()
                try:
                    nuovo_cliente = Cliente(nome=nome_input, email=email_input, azienda=azienda_input)
                    db.add(nuovo_cliente)
                    db.commit()
                    st.success(f"Cliente '{nome_input}' salvato con successo! 🎉")
                except Exception as e:
                    db.rollback()
                    st.error(f"Errore durante il salvataggio: {e}")
                finally:
                    db.close()

with col_dati:
    st.subheader("📋 Elenco Clienti Registrati")
    
    # Recuperiamo i dati correnti per mostrarli nella tabella
    db = SessionLocal()
    try:
        # Eseguiamo una query classica e trasformiamo il risultato in un DataFrame Pandas
        query = db.query(Cliente).all()
        
        if query:
            dati_clienti = [
                {"ID": c.id, "Nome": c.nome, "Email": c.email, "Azienda": c.azienda} 
                for c in query
            ]
            df = pd.DataFrame(dati_clienti)
            
            # Mostra una tabella interattiva nativa di Streamlit (ordinabile e filtrabile dall'utente)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Un piccolo contatore dinamico
            st.metric(label="Totale Clienti", value=len(df))
        else:
            st.info("Nessun cliente presente nel database Netsons. Usa il modulo a sinistra per aggiungere il primo!")
            
    except Exception as e:
        st.error(f"Impossibile leggere i dati da Netsons: {e}")
    finally:
        db.close()

# --- PULSANTE DI DIAGNOSTICA IN FONDO ALLA PAGINA ---
st.divider()
if st.button("🔌 Verifica Stato Connessione"):
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        st.toast("Connessione attiva e funzionante con Netsons!", icon="✅")
    except Exception as e:
        st.error(f"Connessione fallita: {e}")
    finally:
        db.close()
