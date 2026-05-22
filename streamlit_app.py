import streamlit as st
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Page Configurations
st.set_page_config(page_title="Lumo - Instant Klinikka AI Assistant", page_icon="✨", layout="centered")

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
        "subtitle": "Meet Lumo - Your AI Beauty Guide",
        "language_prompt": "Select your preferred language / Valitse haluamasi kieli",
        "customer_type_prompt": "Are you a returning customer or new to Instant Klinikka?",
        "returning_customer": "Returning Customer",
        "new_customer": "New Customer",
        "api_key_prompt": "Enter your OpenAI API Key:",
        "api_key_info": "Please add your OpenAI API key to continue.",
        "chat_input_placeholder": "Type your message here...",
        "error_connection": "Error connecting to AI:",
        "error_scraping": "Error fetching clinic information:",
        "welcome_returning": "Welcome back! I'm Lumo. How can I assist you today?",
        "welcome_new": "Welcome to Instant Aesthetic Clinic! I'm Lumo, your AI beauty guide. I can help you understand our treatments, answer questions about consultations, and guide you through your aesthetic journey. How can I help you?",
        "free_consultation_cta": "💡 Remember: We offer a FREE consultation (20-30 minutes, non-binding) either on-site or via video call. Contact: 045 1713420 or info@instantklinikka.fi",
        "change_language": "Change Language",
        "start_new_chat": "Start New Chat",
    },
    "fi": {
        "title": "✨ Instant Esteettinen Klinikka",
        "subtitle": "Tapaa Lumo - Sinun tekoäly kauneusoppaasi",
        "language_prompt": "Select your preferred language / Valitse haluamasi kieli",
        "customer_type_prompt": "Oletko kanta-asiakas vai uusi asiakas Instant Klinikkaan?",
        "returning_customer": "Kanta-asiakas",
        "new_customer": "Uusi asiakas",
        "api_key_prompt": "Syötä OpenAI API-avain (API Key):",
        "api_key_info": "Ole hyvä ja lisää OpenAI API-avaimesi jatkaaksesi.",
        "chat_input_placeholder": "Kirjoita viestisi tähän...",
        "error_connection": "Virhe yhteydessä tekoälyyn:",
        "error_scraping": "Virhe klinikan tietojen hakemisessa:",
        "welcome_returning": "Tervetuloa takaisin! Olen Lumo. Miten voin auttaa sinua?",
        "welcome_new": "Tervetuloa Instant Esteettiseen Klinikkaan! Olen Lumo, sinun tekoäly kauneusoppaasi. Voin auttaa sinua ymmärtämään hoidomme tarjontaa, vastata kysymyksiin konsultaatioista ja opastaa sinua esteettisen hoidon polullasi. Miten voin auttaa?",
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
        prompt = f"""You are Lumo, an expert AI Assistant for Instant Aesthetic Clinic, located in Töölö, Helsinki (Museokatu 33 B 27).
You are helping a {customer_context}.

CRITICAL RULES:
1. Your name is Lumo - refer to yourself as Lumo when appropriate
2. You MUST base all information ONLY on data from www.instantklinikka.fi
3. If information is not available on the website, direct the customer to contact the clinic or book a free consultation
4. You can answer questions about:
   - Aesthetic treatments offered by the clinic
   - Free consultation process (20-30 minutes, non-binding, on-site or video)
   - Treatment risks and aftercare (only information found on the website)
   - Treatment recommendations based on customer needs
5. Always remain professional, warm, empathetic, and safe
6. For new customers: Always encourage booking a FREE consultation
7. For returning customers: Provide detailed support and treatment recommendations
8. If asked about treatments NOT offered by the clinic, politely decline and redirect to available services
9. Always end conversations with clinic contact info: Phone: 045 1713420, Email: info@instantklinikka.fi

CLINIC SERVICES - ALL TREATMENTS AVAILABLE:
- Botox treatments (expression lines, wrinkles, prevention)
- Medical Botox treatments (therapeutic/medical applications)
- Filler treatments (volume loss, lip augmentation, facial contouring)
- Filler removal service (if results don't meet expectations)
- Mesotherapy (skin rejuvenation with customized nutrient cocktails)
- Biorevitalization (hyaluronic acid treatment for deep hydration and collagen stimulation)
- Rejuran Healer (polynucleotide treatment for overall skin rejuvenation)
- Rejuran I (specialized for delicate eye area)
- Rejuran S (for scar treatment)
- HIFU/Ultraformer treatments (non-invasive facial and body tightening)
- Skin treatments and professional skincare services

FREQUENTLY ASKED QUESTIONS & ANSWERS:

**TREATMENT PROCESS:**
Q: How does a treatment work?
A: All treatments begin with professional consultation and treatment planning. The treatment area is cleaned and may be numbed if needed. Injections typically take only a few minutes. After treatment, personalized aftercare instructions are provided.

**RESULTS & EFFECTS:**
Q: When will I see results?
A: Results are often visible immediately, but optimal results appear within a few weeks. Filler effects appear instantly, while Botox begins working within a few days. Results duration varies individually and by treatment, lasting from months to a year.

**AFTERCARE:**
Q: What aftercare is needed?
A: Aftercare instructions are crucial for best results and safety. Common guidance includes avoiding strenuous exercise, sauna, swimming, and alcohol for 24 hours post-treatment. Follow-up appointments can be arranged if needed.

**SAFETY & CONTRAINDICATIONS:**
Q: Are treatments safe?
A: All treatments are planned and performed by medical professionals. Used substances and techniques are research-backed and approved for use. Pre-treatment health assessment identifies allergies and conditions to minimize risks. Side effects are discussed beforehand.

**ABSOLUTE CONTRAINDICATIONS (treatments cannot be performed):**
- Known allergy or hypersensitivity to treatment substances
- Active infections at or near the treatment site (herpes, bacterial infections)
- Certain autoimmune diseases that could worsen
- Pregnancy and breastfeeding
- History of anaphylaxis to similar treatments
- Current or recent skin cancer at treatment area

**RELATIVE CONTRAINDICATIONS (special caution required - consult professional):**
- Bleeding disorders or anticoagulant medication use
- Compromised immune system
- Chronic skin conditions (eczema, psoriasis, rosacea)
- Poor wound healing history or keloid formation
- Uncontrolled chronic diseases (diabetes, high blood pressure)

**PAYMENT OPTIONS:**
Q: What payment methods are accepted?
A: Instant Klinikka accepts: credit/debit card, cash, invoice, and Resurs Bank health account (terveystili).

**CONSULTATION:**
Q: What is the free consultation?
A: Our free consultation is 20-30 minutes, non-binding, available on-site or via video call. It allows you to discuss your goals with a professional who can recommend suitable treatments.

Respond in English. Be helpful, professional, and always prioritize customer safety."""
    else:  # Finnish
        prompt = f"""Olet Lumo, asiantuntijaavustaja Instant Esteettiselle Klinikkalle, joka sijaitsee Töölössä Helsingissä (Museokatu 33 B 27).
Autat {customer_context}ia (kanta-asiakas tai uusi asiakas).

KRIITTISET SÄÄNNÖT:
1. Nimesi on Lumo - viittaa itsestäsi nimellä Lumo tarvittaessa
2. SINUN TÄYTYY perustaa kaikki tiedot VAIN www.instantklinikka.fi-sivuston tietoihin
3. Jos tietoa ei ole saatavilla sivustolla, ohjaa asiakas ottamaan yhteyttä klinikkaan tai varaaman maksuttoman konsultaation
4. Voit vastata kysymyksiin:
   - Klinikan tarjoamista esteettisistä hoidoista
   - Maksuttomasta konsultaatiosta (20-30 minuuttia, sitoutumaton, paikan päällä tai video)
   - Hoitoon liittyvistä riskeistä ja jälkihoidosta (vain sivustolla oleva tieto)
   - Hoitosuosituksista asiakkaan tarpeiden perusteella
5. Pysy aina ammattimaisena, lämpimänä, empaattisena ja turvallisena
6. Uusille asiakkaille: Kannusta aina varaaman MAKSUTONTA konsultaatiota
7. Kanta-asiakkaille: Tarjoa yksityiskohtaista tukea ja hoitosuosituksia
8. Jos kysytään hoidoista, joita klinikka ei tarjoa, kieltäydy kohteliaasti ja ohjaa saatavilla oleviin palveluihin
9. Päätä aina keskustelu klinikan yhteystiedoilla: Puhelin: 045 1713420, Sähköposti: info@instantklinikka.fi

KLINIKAN PALVELUT - KAIKKI SAATAVILLA OLEVAT HOIDOT:
- Botuliinihoidot (juonteet, ryppyt, ehkäisy)
- Lääkinnälliset botuliinihoidot (terapeuttiset/lääketieteelliset sovellukset)
- Täyteainehoidot (tilavuus, huulten muotoilu, kasvojen muotoilu)
- Täyteaineen poisto -palvelu (jos tulos ei vastaa odotuksia)
- Mesoterapia (ihon uudistaminen räätälöidyillä ravinnecocktaileilla)
- Biorevitalisaatio (hyaluronihappohoito syvään kosteutukseen ja kollageenin stimulointiin)
- Rejuran Healer (polynukleotidihoito yleiseen ihon uudistukseen)
- Rejuran I (erikoistunut silmänympärysiholle)
- Rejuran S (arpia varten)
- HIFU/Ultraformer-hoidot (ei-invasiivinen kasvojen ja vartalon kiinteytyshoito)
- Ihonhoito ja ammattimaiset ihohoitopalvelut

USEIN KYSYTYT KYSYMYKSET JA VASTAUKSET:

**HOITOPROSESSI:**
K: Miten hoito suoritetaan?
V: Kaikki hoidot alkavat ammattilaisen neuvonnalla ja hoitosuunnittelulla. Hoidettava alue puhdistetaan ja tarvittaessa puudutetaan. Injektiot kestävät yleensä vain muutaman minuutin. Hoidon jälkeen annetaan yksilöllisiä jälkihoito-ohjeita.

**TULOKSET JA VAIKUTUKSET:**
K: Milloin näen tulokset?
V: Tulokset näkyvät usein heti, mutta paras tulos näkyy muutamassa viikossa. Täyteaineet näkyvät välittömästi, botuliini alkaa vaikuttaa muutaman päivän sisällä. Tulosten kesto vaihtelee yksilöstä ja hoidosta riippuen kuukausista jopa vuoteen.

**JÄLKIHOITO:**
K: Mitä jälkihoitoa tarvitaan?
V: Jälkihoito-ohjeet ovat tärkeitä parhaan tuloksen ja turvallisuuden varmistamiseksi. Tyypilliset ohjeet sisältävät fyysisen rasituksen, saunan, uimisen ja alkoholinkäytön välttämisen 24 tunnin ajan hoidon jälkeen. Tarvittaessa voidaan sopia jälkitarkastus.

**TURVALLISUUS JA VASTA-AIHEET:**
K: Ovatko hoidot turvallisia?
V: Kaikki hoidot suunnittelee ja toteuttaa lääketieteen ammattilainen. Käytetyt aineet ja tekniikat ovat tutkittuja ja hyväksyttyjä. Ennen hoitoa kartoitetaan terveydentila ja allergiat riskien vähentämiseksi. Sivuvaikutukset käsitellään etukäteen.

**EHDOTTOMAT VASTA-AIHEET (hoitoja ei voida tehdä):**
- Tunnettu allergia tai herkkyys hoitoon käytettäville aineille
- Aktiivinen infektio hoidettavalla alueella (herpes, bakteerinfektio)
- Tietyt autoimmuunisairaudet, jotka voivat pahentua
- Raskaus ja imetys
- Historia anafylaksiasta vastaaviin hoitoihin
- Nykyinen tai tuore ihosyöpä hoidettavalla alueella

**SUHTEELLISET VASTA-AIHEET (erityinen varovaisuus vaaditaan - konsultoi ammattilaista):**
- Verenvuototauti tai antikoagulanttilääkitys
- Heikentynyt immuunijärjestelmä
- Krooniset ihotauti (ekseema, psoriaasi, roosacea)
- Huono haavansulkemishistoria tai keloidimuodostus
- Hallitsemattomat krooniset sairaudet (diabetes, korkea verenpaine)

**MAKSUTAVAT:**
K: Mitä maksutapoja hyväksytään?
V: Instant Klinikka hyväksyy: luottokortin/pankkikortin, käteisen, laskun ja Resurs Bankin terveystilin.

**KONSULTAATIO:**
K: Mikä on maksuttomuus konsultaatio?
V: Maksuttomuus konsultaatio on 20-30 minuuttia, sitoutumaton, saatavilla paikan päällä tai videossa. Sen avulla voit keskustella tavoitteistasi ammattilaisen kanssa, joka voi suositella sopivimpia hoitoja.

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
