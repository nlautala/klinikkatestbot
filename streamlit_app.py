import streamlit as st
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Page Configurations
st.set_page_config(page_title="Instant Klinikka AI Assistant", page_icon="✨", layout="centered")

# ============================================================================
# LANGUAGE CONFIGURATION
# ============================================================================
LANGUAGES = {
    "English": "en",
    "Suomi": "fi"
}

TRANSLATIONS = {
    "en": {
        "title": "✨ Instant Aesthetic Clinic",
        "subtitle": "AI Assistant for Your Aesthetic Needs",
        "language_prompt": "Select your preferred language / Valitse haluamasi kieli",
        "customer_type_prompt": "Are you a returning customer or new to Instant Klinikka?",
        "returning_customer": "Returning Customer",
        "new_customer": "New Customer",
        "api_key_prompt": "Enter your OpenAI API Key:",
        "api_key_info": "Please add your OpenAI API key to continue.",
        "chat_input_placeholder": "Type your message here...",
        "error_connection": "Error connecting to AI:",
        "error_scraping": "Error fetching clinic information:",
        "welcome_returning": "Welcome back! How can I assist you today?",
        "welcome_new": "Welcome to Instant Aesthetic Clinic! I'm your AI assistant. I can help you understand our treatments, answer questions about consultations, and guide you through your aesthetic journey. How can I help you?",
        "free_consultation_cta": "💡 Remember: We offer a FREE consultation (20-30 minutes, non-binding) either on-site or via video call. Contact: 045 1713420 or info@instantklinikka.fi",
        "change_language": "Change Language",
        "start_new_chat": "Start New Chat",
    },
    "fi": {
        "title": "✨ Instant Esteettinen Klinikka",
        "subtitle": "Tekoälyavustaja ihonhoitotarpeillesi",
        "language_prompt": "Select your preferred language / Valitse haluamasi kieli",
        "customer_type_prompt": "Oletko kanta-asiakas vai uusi asiakas Instant Klinikkaan?",
        "returning_customer": "Kanta-asiakas",
        "new_customer": "Uusi asiakas",
        "api_key_prompt": "Syötä OpenAI API-avain (API Key):",
        "api_key_info": "Ole hyvä ja lisää OpenAI API-avaimesi jatkaaksesi.",
        "chat_input_placeholder": "Kirjoita viestisi tähän...",
        "error_connection": "Virhe yhteydessä tekoälyyn:",
        "error_scraping": "Virhe klinikan tietojen hakemisessa:",
        "welcome_returning": "Tervetuloa takaisin! Miten voin auttaa sinua?",
        "welcome_new": "Tervetuloa Instant Esteettiseen Klinikkaan! Olen tekoälyavustajasi. Voin auttaa sinua ymmärtämään hoidomme tarjontaa, vastata kysymyksiin konsultaatioista ja opastaa sinua esteettisen hoidon polullasi. Miten voin auttaa?",
        "free_consultation_cta": "💡 Muista: Tarjoamme MAKSUTONTA konsultaatiota (20-30 minuuttia, sitoutumaton) joko paikan päällä tai videoneuvottelun kautta. Ota yhteyttä: 045 1713420 tai info@instantklinikka.fi",
        "change_language": "Vaihda kieltä",
        "start_new_chat": "Aloita uusi keskustelu",
    }
}

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if "language" not in st.session_state:
    st.session_state.language = None
if "customer_type" not in st.session_state:
    st.session_state.customer_type = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "clinic_info" not in st.session_state:
    st.session_state.clinic_info = None
if "clinic_info_timestamp" not in st.session_state:
    st.session_state.clinic_info_timestamp = None

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_text(key):
    """Get translated text based on current language"""
    if st.session_state.language:
        lang_code = LANGUAGES[st.session_state.language]
        return TRANSLATIONS[lang_code].get(key, key)
    return key

@st.cache_data(ttl=3600)
def fetch_clinic_info():
    """Scrape website information from instantklinikka.fi"""
    try:
        response = requests.get("https://www.instantklinikka.fi", timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extract text content
        text_content = soup.get_text(separator="\n", strip=True)
        
        # Extract links to services
        links = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            link_text = link.get_text(strip=True)
            if link_text and href.startswith(("http", "/")):
                links.append({"text": link_text, "url": href})
        
        return {
            "content": text_content[:5000],  # Limit to first 5000 chars
            "links": links,
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "content": "",
            "links": [],
            "error": str(e),
            "timestamp": datetime.now()
        }

def get_system_prompt():
    """Generate system prompt based on language and customer type"""
    lang_code = LANGUAGES[st.session_state.language]
    customer_context = "returning customer" if st.session_state.customer_type == "returning" else "new customer"
    
    if lang_code == "en":
        prompt = f"""You are an expert AI Assistant for Instant Aesthetic Clinic, located in Töölö, Helsinki (Museokatu 33 B 27).
You are helping a {customer_context}.

CRITICAL RULES:
1. You MUST base all information ONLY on data from www.instantklinikka.fi
2. If information is not available on the website, direct the customer to contact the clinic or book a free consultation
3. You can answer questions about:
   - Aesthetic treatments offered by the clinic
   - Free consultation process (20-30 minutes, non-binding, on-site or video)
   - Treatment risks and aftercare (only information found on the website)
   - Treatment recommendations based on customer needs
4. Always remain professional, warm, empathetic, and safe
5. For new customers: Always encourage booking a FREE consultation
6. For returning customers: Provide detailed support and treatment recommendations
7. If asked about treatments NOT offered by the clinic, politely decline and redirect to available services
8. Always end conversations with clinic contact info: Phone: 045 1713420, Email: info@instantklinikka.fi

CLINIC SERVICES TO REFERENCE:
- Botox treatments (expression lines, wrinkles, prevention)
- Fillers (volume loss, lip augmentation)
- Mesotherapy (skin rejuvenation)
- Biorevitalization & Rejuran
- HIFU/Ultraformer treatments

Respond in English. Be helpful, professional, and always prioritize customer safety."""
    else:  # Finnish
        prompt = f"""Olet asiantuntijaavustaja Instant Esteettiselle Klinikkalle, joka sijaitsee Töölössä Helsingissä (Museokatu 33 B 27).
Autat {customer_context}ia (kanta-asiakas tai uusi asiakas).

KRIITTISET SÄÄNNÖT:
1. SINUN TÄYTYY perustaa kaikki tiedot VAIN www.instantklinikka.fi-sivuston tietoihin
2. Jos tietoa ei ole saatavilla sivustolla, ohjaa asiakas ottamaan yhteyttä klinikkaan tai varaaman maksuttoman konsultaation
3. Voit vastata kysymyksiin:
   - Klinikan tarjoamista esteettisistä hoidoista
   - Maksuttomasta konsultaatiosta (20-30 minuuttia, sitoutumaton, paikan päällä tai video)
   - Hoitoon liittyvistä riskeistä ja jälkihoidosta (vain sivustolla oleva tieto)
   - Hoitosuosituksista asiakkaan tarpeiden perusteella
4. Pysy aina ammattimaisena, lämpimänä, empaattisena ja turvallisena
5. Uusille asiakkaille: Kannusta aina varaaman MAKSUTONTA konsultaatiota
6. Kanta-asiakkaille: Tarjoa yksityiskohtaista tukea ja hoitosuosituksia
7. Jos kysytään hoidoista, joita klinikka ei tarjoa, kieltäydy kohteliaasti ja ohjaa saatavilla oleviin palveluihin
8. Päätä aina keskustelu klinikan yhteystiedoilla: Puhelin: 045 1713420, Sähköposti: info@instantklinikka.fi

KLINIKAN PALVELUT:
- Botuliinihoidot (juonteet, ryppyt, ehkäisy)
- Täyteainehoidot (tilavuus, huulten muotoilu)
- Mesoterapia (ihon uudistaminen)
- Biorevitalisaatio & Rejuran
- HIFU/Ultraformer-hoidot

Vastaa suomeksi. Ole auttavainen, ammattimainen ja aseta asiakkaan turvallisuus etusijalle."""
    
    return prompt

# ============================================================================
# MAIN APPLICATION
# ============================================================================

# Language Selection
if not st.session_state.language:
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("English 🇬🇧", use_container_width=True, key="lang_en"):
            st.session_state.language = "English"
            st.rerun()
    with col2:
        if st.button("Suomi 🇫🇮", use_container_width=True, key="lang_fi"):
            st.session_state.language = "Suomi"
            st.rerun()
    st.stop()

# Display current language and allow change
col1, col2 = st.columns([3, 1])
with col1:
    st.title(get_text("title"))
    st.subheader(get_text("subtitle"))
with col2:
    if st.button(get_text("change_language"), key="change_lang_btn"):
        st.session_state.language = None
        st.session_state.customer_type = None
        st.session_state.messages = []
        st.rerun()

st.write("---")

# Customer Type Selection
if not st.session_state.customer_type:
    st.write(get_text("customer_type_prompt"))
    col1, col2 = st.columns(2)
    with col1:
        if st.button(get_text("new_customer"), use_container_width=True, key="new_cust"):
            st.session_state.customer_type = "new"
            st.rerun()
    with col2:
        if st.button(get_text("returning_customer"), use_container_width=True, key="returning_cust"):
            st.session_state.customer_type = "returning"
            st.rerun()
    st.stop()

# API Key Configuration
openai_api_key = st.secrets.get("OPENAI_API_KEY", None)
if not openai_api_key:
    openai_api_key = st.sidebar.text_input(get_text("api_key_prompt"), type="password")
    if not openai_api_key:
        st.info(get_text("api_key_info") + " 🗝️")
        st.stop()

# Initialize OpenAI Client
client = OpenAI(api_key=openai_api_key)

# Fetch clinic information
if st.session_state.clinic_info is None:
    st.session_state.clinic_info = fetch_clinic_info()

# Initialize chat with welcome message
if not st.session_state.messages:
    welcome_key = "welcome_new" if st.session_state.customer_type == "new" else "welcome_returning"
    welcome_message = get_text(welcome_key)
    st.session_state.messages.append({
        "role": "assistant",
        "content": welcome_message
    })

# Display Free Consultation CTA
st.info(get_text("free_consultation_cta"), icon="ℹ️")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User Input Handling
if user_input := st.chat_input(get_text("chat_input_placeholder")):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Generate AI response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        # Prepare full payload including system context and clinic info
        system_prompt = get_system_prompt()
        clinic_context = f"\n\nCLINIC WEBSITE INFORMATION:\n{st.session_state.clinic_info.get('content', '')}"
        
        api_messages = [
            {"role": "system", "content": system_prompt + clinic_context}
        ] + [
            {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
        ]
        
        try:
            # Stream the response from GPT model
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=api_messages,
                stream=True,
                temperature=0.7,
                max_tokens=1000,
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.write(full_response + "▌")
            
            response_placeholder.write(full_response)
            # Append assistant response to state
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            error_msg = f"{get_text('error_connection')} {e}"
            st.error(error_msg)

# Sidebar controls
st.sidebar.write("---")
if st.sidebar.button(get_text("start_new_chat"), key="new_chat_btn"):
    st.session_state.messages = []
    st.rerun()
