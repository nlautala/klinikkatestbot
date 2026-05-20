import streamlit as st
from openai import OpenAI

# Page Configurations
st.set_page_config(page_title="Instant Klinikka AI Assistant", page_icon="✨", layout="centered")

st.title("✨ Instant Esteettinen Klinikka")
st.subheader("Löydä sinulle sopiva hoito / Find the right treatment for you")
st.write("Tämä tekoälyavustaja auttaa sinua kartoittamaan ihosi tarpeita ja suosittelee sopivia hoitoja klinikkamme palveluista.")

# Securely retrieve the OpenAI API Key from Streamlit Secrets or user input
openai_api_key = st.secrets.get("OPENAI_API_KEY", None)
if not openai_api_key:
    openai_api_key = st.sidebar.text_input("Syötä OpenAI API-avain (API Key):", type="password")
    if not openai_api_key:
        st.info("Ole hyvä ja lisää OpenAI API-avaimesi jatkaaksesi.", icon="🗝️")
        st.stop()

# Initialize OpenAI Client
client = OpenAI(api_key=openai_api_key)

# System prompt feeding website context into the AI model
SYSTEM_PROMPT = """
You are an expert AI Assistant for 'Instant Esteettinen Klinikka', an aesthetic clinic located in Töölö, Helsinki (Museokatu 33 B 27). 
Your objective is to help clients identify the correct treatments based on their concerns, but ALWAYS remind them that a final assessment is done during a free consultation.
Respond in Finnish (or the language the user uses). Always remain professional, warm, empathetic, and safe.

Clinic Services and Guidelines:
1. Botuliinihoidot (Botox): Best for expression lines, wrinkles, preventive aging, forehead lines, frown lines (Sibelius), gummy smile, lip flip, and excessive sweating (liikahikoilu).
2. Täyteainehoidot (Fillers): Best for volume loss, shaping structural lines, and lip augmentation.
3. Mesoterapia: Skin rejuvenation from within using micro-injections (hyaluronic acid, vitamins). 
    - CELLBOOSTER® GLOW: For dry, dull, tired skin, and hyperpigmentation.
    - CELLBOOSTER® LIFT: Tightening, smoothing fine lines, improving tone.
    - CELLBOOSTER® SHAPE & Lipolyysi: Localized fat reduction (e.g., double chin / kaksoisleuka).
    - JALUPRO® Young Eye: Specifically for dark under-eye circles, puffiness, and fine wrinkles around eyes.
4. Biorevitalisaatio & Polynukleotidit (Rejuran) & Radiesse & Ultraformer/HIFU: For deep skin quality, tightening, and natural regeneration.

Safety / Contraindications:
If a user mentions pregnancy, breastfeeding, active skin infections/acne in the area, or severe bleeding disorders, politely inform them that cosmetic injection treatments might not be suitable right now and require a doctor's evaluation.

Call to Action:
Always encourage the customer to book a FREE consultation (Maksuton konsultaatio). It takes 20-30 mins, non-binding, and can be done either on-site in Helsinki or online via video call.
Contact info: Puh: 045 1713420, Sähköposti: info@instantklinikka.fi.
"""

# Initialize Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hei! Olen Instant Klinikan tekoälyavustaja. Kertoisitko hieman ihonhoitotavoitteistasi tai huolenaiheistasi (esim. juonteet, ihon kuivuus, huulien muotoilu)? Autan mielelläni löytämään oikean hoidon!"}
    ]

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User Input Handling
if user_input := st.chat_input("Kirjoita viestisi tähän..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Generate AI response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        # Prepare full payload including system context
        api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
            {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
        ]
        
        try:
            # Stream the response from GPT model
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=api_messages,
                stream=True,
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
            st.error(f"Virhe yhteydessä tekoälyyn: {e}")