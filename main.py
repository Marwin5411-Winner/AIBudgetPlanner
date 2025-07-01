import streamlit as st
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import LLMChain # Not needed if using LCEL

#Tool imports


# --- Page Configuration ---
st.set_page_config(page_title="AI Budget Planner", layout="wide", initial_sidebar_state="expanded")
st.title("💸 AI Budget Planner")
st.caption("Plan your activities like eating out, movies, and travel within your budget scope using AI.")

# --- API Key Management ---
try:
    # Ensure st.secrets is available and the key exists
    if hasattr(st, 'secrets') and "GOOGLE_API_KEY" in st.secrets:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    else:
        GOOGLE_API_KEY = None
except Exception: 
    GOOGLE_API_KEY = None

if not GOOGLE_API_KEY:
    GOOGLE_API_KEY = st.sidebar.text_input(
        "Enter your Google API Key:",
        type="password",
        help="Get your API key from Google AI Studio. The app requires this key to function.",
        key="google_api_key_input_sidebar"
    )

# --- Langchain Setup ---
llm = None
budget_chain = None 

if GOOGLE_API_KEY:
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7,
            # convert_system_message_to_human=True # Useful for models not fully supporting system messages
        )

        
        # Prompt template
        prompt_template_text = """
You are a friendly, insightful, and practical AI budget planner.
The user has a total budget of {currency}{budget}.
The user is located in {location} (if provided).
The user wants to engage in the following activities: {activities}.

Please provide a suggested budget plan. Your response should be helpful, actionable, and encouraging.
Follow these steps in your response:
1.  Start with a brief, positive opening.
2.  Analyze the feasibility of the activities within the given budget. Be realistic.
3.  If all activities are feasible, suggest a potential allocation of funds for each activity.
4.  If not all activities are feasible with the current budget, explain clearly why. Suggest which activities to prioritize, or offer specific, lower-cost alternatives for some activities.
5.  Provide 2-3 general, actionable tips for managing this budget effectively and achieving these financial goals.
6.  Conclude with an encouraging remark and a reminder that this is a suggestion.

Present the plan in a clear, easy-to-read format. Use markdown for structure (e.g., headings, subheadings, bullet points, bold text for emphasis).

Example structure for your response:

### Budget Plan for {currency}{budget}

** Location: {location} (if applicable)**

**Activities:** {activities}

**1. Feasibility Analysis:**
*(Your analysis here)*

**2. Suggested Budget Allocation (if feasible):**
*   Activity 1: $X
*   Activity 2: $Y
*   *(etc.)*

**3. Prioritization/Alternatives (if needed):**
*(Your suggestions here)*

**4. Budget Management Tips:**
*   Tip 1...
*   Tip 2...

**5. Final Thoughts:**
*(Your encouraging closing remarks)*
---
Your detailed plan:
"""

        budget_prompt = PromptTemplate(
            input_variables=["budget", "activities", "location", "currency"],
            template=prompt_template_text
        )

        output_parser = StrOutputParser()

        budget_chain = budget_prompt | llm | output_parser

    except Exception as e:
        st.sidebar.error(f"Error initializing AI model: {e}")
        st.toast(f"Error initializing AI: {e}", icon="❌")

else:
    st.sidebar.warning("Please enter your Google API Key in the sidebar to enable the AI planner.")

# --- User Input Area ---
st.header("Step 1: Your Budget Details", divider="rainbow")
col1, col2 = st.columns([1, 2])

with col1:
    bi = st.number_input(
        "💰 Enter your total budget:",
        min_value=0.0,
        step=10.0,
        value=200.0,
        help="Specify your total available budget for the listed activities."
    )
    
    cs = st.selectbox(
        "💵 Select your currency:",
        options=["USD", "EUR", "GBP", "INR", "AUD", "CAD", "JPY", "CNY", "RUB", "BRL", "THB"],
        index=0,
        help="Choose the currency in which your budget is denominated."
    )
    
    li = st.text_input(
        "📍 Enter your location (optional):",
        placeholder="e.g., New York, USA",
        help="Specify your location to tailor the budget plan to local costs."
    )

with col2:
    example_activities = "Weekend trip to a nearby national park, 3 home-cooked fancy meals, visit a local museum, 2 online movie rentals"
    activities_input = st.text_area(
        "📝 List desired activities:",
        height=120,
        placeholder=f"e.g., {example_activities}",
        help="List all activities you want to budget for. Be as specific or general as you like."
    )

# --- Generate Plan Button ---
st.header("Step 2: Generate Your Plan", divider="rainbow")
if st.button("✨ Generate AI Budget Plan", type="primary", use_container_width=True, help="Click to get your personalized budget plan"):
    if not GOOGLE_API_KEY or not budget_chain:
        st.error("AI Model not initialized. Please ensure your Google API Key is correctly entered in the sidebar and is valid.")
        st.toast("API Key or AI Model issue.", icon="🔑")
    elif bi <= 0:
        st.warning("Please enter a budget amount greater than zero.")
        st.toast("Budget must be positive.", icon="⚠️")
    elif not activities_input.strip():
        st.warning("Please list some activities you'd like to plan for.")
        st.toast("Activities list is empty.", icon="⚠️")
    else:
        with st.spinner("🤖 AI is crafting your personalized budget plan... Please wait."):
            try:
                inputs = {"budget": bi, "activities": activities_input, "location": location_input, "currency": cs}
                
                ai_response = budget_chain.invoke(inputs)

                st.subheader("📊 Your AI-Generated Budget Plan")
                st.markdown(ai_response)
                st.toast("Budget plan generated successfully!", icon="🎉")

            except Exception as e:
                st.error(f"An error occurred while generating the plan: {e}")
                st.toast(f"Generation error: {e}", icon="❌")
                st.info("This might be due to API issues (e.g., quota, invalid key), network problems, or the model couldn't process the request. Please check your key, try simplifying your request, or try again later.")

# --- Footer ---
st.markdown("---")