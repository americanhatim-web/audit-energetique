import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
import datetime

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Audit Energetique Maroc",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better visualization
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
        background-color: #00cc66;
        color: white;
        font-weight: bold;
    }
    .report-box {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.title("⚡ Energy Audit AI")
    st.markdown("---")
    
    # Navigation Buttons
    page = st.radio(
        "Navigation",
        ["🏠 Home", "📄 Simple Audit", "🔍 Detailed Audit", "📚 History"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.info("💡 This app respects Moroccan Energy Norms (AMEE/ONEE).")
    st.caption("Powered by Google Gemini AI")

# ==========================================
# 3. GEMINI AI CONFIGURATION
# ==========================================
# We use st.secrets for security when deployed, fallback to input for local testing
def get_api_key():
    if "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    else:
        # Fallback for local testing if secrets not set
        return st.text_input("Enter Google API Key", type="password", key="api_key_input")

api_key = get_api_key()

if api_key:
    genai.configure(api_key=api_key)
    # Using gemini-1.5-flash for speed and cost efficiency (Free tier friendly)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.warning("Please enter your API Key to continue.")

# ==========================================
# 4. HELPER FUNCTIONS
# ==========================================

def save_report_to_history(report_data):
    """Saves the report to a local JSON file for history"""
    history_file = "history.json"
    history = []
    
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                history = json.load(f)
        except:
            history = []
    
    # Add new report with timestamp
    report_entry = {
        "id": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": report_data.get("type", "Unknown"),
        "summary": report_data.get("summary", "No summary"),
        "full_report": report_data.get("full_report", "")
    }
    
    history.insert(0, report_entry) # Add to top
    
    with open(history_file, "w") as f:
        json.dump(history, f, indent=4)

def load_history():
    """Loads history from JSON file"""
    history_file = "history.json"
    if os.path.exists(history_file):
        try:
            with open(history_file, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def delete_report(report_id):
    """Deletes a specific report from history"""
    history_file = "history.json"
    history = load_history()
    new_history = [item for item in history if item["id"] != report_id]
    
    with open(history_file, "w") as f:
        json.dump(new_history, f, indent=4)

def analyze_image_with_gemini(image, prompt, is_detailed=False, appliances_info=None):
    """Sends image and prompt to Gemini AI"""
    if not api_key:
        return "Error: API Key not provided."
    
    try:
        # Construct the full prompt based on Moroccan Norms
        full_prompt = f"""
        You are an expert Energy Auditor in Morocco. 
        Your goal is to analyze energy bills and consumption based on Moroccan Norms (AMEE, ONEE).
        Currency is Moroccan Dirham (MAD). Voltage is 220V/380V.
        
        TASK:
        {prompt}
        
        {"ADDITIONAL DATA PROVIDED BY USER (Appliances):" + appliances_info if is_detailed else ""}
        
        Please provide the response in structured Markdown format with clear headings.
        Include specific recommendations for energy efficiency in Morocco.
        """
        
        response = model.generate_content([full_prompt, image])
        return response.text
    except Exception as e:
        return f"Error during analysis: {str(e)}"

# ==========================================
# 5. PAGE: HOME
# ==========================================
if page == "🏠 Home":
    st.title("🏠 Welcome to Energy Audit Maroc")
    st.markdown("""
    ### What is an Energy Audit?
    An energy audit is a systematic process to understand how energy is used in a building or facility, 
    identifying opportunities to reduce consumption and costs.
    
    ### Why use this App?
    - **AI Powered:** Uses Google Gemini to analyze your electricity bills instantly.
    - **Moroccan Context:** Recommendations are tailored to Moroccan regulations (AMEE) and climate.
    - **Free & Fast:** Get a preliminary report in seconds.
    
    ### How it works:
    1. **Simple Audit:** Upload a photo of your electricity bill. The AI extracts data and gives general advice.
    2. **Detailed Audit:** Upload bill + List your appliances (AC, Fridge, etc.). The AI compares expected vs. actual consumption.
    3. **History:** Save and manage your past reports.
    
    ---
    *Note: This tool provides recommendations based on AI analysis. For official certification, please consult a certified auditor.*
    """)
    
    st.image("https://www.amee.ma/sites/default/files/2021-03/amee_logo.png", width=300, caption="Respecting AMEE Standards")

# ==========================================
# 6. PAGE: SIMPLE AUDIT
# ==========================================
elif page == "📄 Simple Audit":
    st.title("📄 Simple Energy Audit")
    st.markdown("Upload a photo of your electricity bill (ONEE or similar). The AI will analyze consumption and costs.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        uploaded_file = st.file_uploader("Choose Bill Image...", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption='Uploaded Bill', use_column_width=True)
    
    with col2:
        st.subheader("Analysis Result")
        if uploaded_file is not None:
            if st.button("🚀 Analyze Bill"):
                with st.spinner("AI is analyzing your bill based on Moroccan norms..."):
                    prompt = """
                    1. Extract the total consumption (kWh).
                    2. Extract the total amount (MAD).
                    3. Identify the billing period.
                    4. Analyze if the consumption is high for a standard household in Morocco.
                    5. Provide 3 specific recommendations to reduce this bill.
                    """
                    result = analyze_image_with_gemini(image, prompt)
                    
                    st.markdown("### 📊 Report")
                    st.markdown(result)
                    
                    # Save to History
                    if result:
                        report_data = {
                            "type": "Simple Audit",
                            "summary": "Simple Bill Analysis",
                            "full_report": result
                        }
                        save_report_to_history(report_data)
                        st.success("Report saved to History!")
        else:
            st.info("Please upload an image to start.")

# To be continued in Part 2...
# ==========================================
# 7. PAGE: DETAILED AUDIT
# ==========================================
elif page == "🔍 Detailed Audit":
    st.title("🔍 Detailed Energy Audit")
    st.markdown("""
    This mode combines your bill analysis with your specific appliance data.
    Please provide details about your major energy-consuming devices.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Upload Bill")
        uploaded_file = st.file_uploader("Choose Bill Image...", type=["jpg", "jpeg", "png"], key="detailed_bill")
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption='Uploaded Bill', use_column_width=True)
    
    with col2:
        st.subheader("2. Appliance Information")
        st.markdown("List your main appliances, power (Watts), and daily usage hours.")
        appliance_info = st.text_area(
            "Appliance List", 
            height=200, 
            placeholder="Example:\n- 2 Air Conditioners (12000 BTU), used 5 hours/day\n- 1 Water Heater (2000W), used 1 hour/day\n- 1 Refrigerator (Class A), 24 hours/day\n- 10 LED Lights (10W), 6 hours/day"
        )
    
    st.markdown("---")
    if st.button("🚀 Generate Detailed Report"):
        if uploaded_file is not None and appliance_info:
            with st.spinner("AI is comparing bill data with appliance usage..."):
                prompt = """
                1. Extract total consumption (kWh) and cost (MAD) from the uploaded bill.
                2. Analyze the provided appliance list.
                3. Estimate the theoretical consumption of these appliances.
                4. Compare the theoretical consumption with the actual bill consumption.
                5. Identify discrepancies (e.g., hidden consumption, old appliances, insulation issues).
                6. Provide a detailed action plan to optimize energy use according to Moroccan standards.
                """
                result = analyze_image_with_gemini(image, prompt, is_detailed=True, appliances_info=appliance_info)
                
                st.markdown("### 📊 Detailed Report")
                st.markdown(result)
                
                # Save to History
                if result:
                    report_data = {
                        "type": "Detailed Audit",
                        "summary": "Detailed Analysis with Appliances",
                        "full_report": result
                    }
                    save_report_to_history(report_data)
                    st.success("Detailed Report saved to History!")
        elif not uploaded_file:
            st.error("Please upload a bill image.")
        elif not appliance_info:
            st.error("Please enter appliance information.")

# ==========================================
# 8. PAGE: HISTORY
# ==========================================
elif page == "📚 History":
    st.title("📚 Audit History")
    st.markdown("View and manage your past generated reports.")
    
    history = load_history()
    
    if not history:
        st.info("No reports found in history yet.")
    else:
        # Display history in reverse chronological order
        for report in history:
            with st.expander(f"📄 {report['type']} - {report['date']}"):
                st.markdown(f"**Summary:** {report['summary']}")
                st.markdown("---")
                st.markdown(report['full_report'])
                
                # Delete Button
                col_del, _ = st.columns([1, 5])
                with col_del:
                    if st.button("🗑️ Delete", key=f"del_{report['id']}"):
                        delete_report(report['id'])
                        st.rerun() # Refresh page to show changes

# ==========================================
# 9. FOOTER
# ==========================================
st.markdown("---")
st.markdown("<center>© 2024 Energy Audit Maroc - Powered by Google Gemini</center>", unsafe_allow_html=True)
