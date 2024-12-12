import os
import streamlit as st
import snowflake.connector
from snowflake.snowpark import Session
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Function to load Snowflake credentials from environment variables
def load_snowflake_credentials():
    return {
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA")
    }

# Function to attempt Snowflake connection
def connect_to_snowflake(credentials):
    try:
        conn = snowflake.connector.connect(
            user=credentials["user"],
            password=credentials["password"],
            account=credentials["account"],
            warehouse=credentials["warehouse"],
            database=credentials["database"],
            schema=credentials["schema"]
        )
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_DATE;")
        cursor.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

# Load Snowflake credentials
credentials = load_snowflake_credentials()

# Try to connect to Snowflake on app load
connection_successful, error_message = connect_to_snowflake(credentials)

# Initialize session state variables for chat history, loading state, and user query
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'loading' not in st.session_state:
    st.session_state.loading = False

if 'user_query' not in st.session_state:
    st.session_state.user_query = ''  # Store the current input

# Display a warning for failed Snowflake connection, only for 10 seconds
if not connection_successful:
    with st.empty() as warning_placeholder:
        st.error(f"Failed to connect to Snowflake: {error_message}")
        st.warning("Please check your Snowflake credentials or environment settings.")
        time.sleep(10)  # Display the warning for 10 seconds
        warning_placeholder.empty()
else:
    # Proceed with the rest of the app logic
    session = Session.builder.configs(credentials).create()
    st.session_state.session = session

    st.title("AI HelpDocs")

    # Inject custom CSS for styling
    st.markdown(
        """
        <style>
        body {
            background-color: #121212;
            color: white;
        }
        .chat-container {
            max-width: 700px;
            margin: auto;
        }
        .message {
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
        }
        .user-message {
            background-color: #1E88E5;
            color: white;
            text-align: left;
            flex-grow: 1;
        }
        .bot-message {
            background-color: #424242;
            color: white;
            text-align: left;
            flex-grow: 1;
        }
        .icon {
            margin-right: 15px;
        }
        .message-box {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .input-container {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .text-input {
            flex-grow: 1;
        }
        div.stButton > button {
            background-color: #1E88E5; 
            color: white;             
            border-radius: 8px;       
            font-size: 16px;          
            font-weight: bold;        
            border: none;             
            cursor: pointer;         
            display: flex;           
            align-items: center;
            justify-content: center;
        }
        div.stButton > button img {
            margin-right: 8px; /* Add space between icon and button text */
        }
        div.stButton > button:hover {
            background-color: #1565C0; /* Darker background on hover */
        }
        .stHorizontalBlock{
            display: flex !important;
            flex-wrap: wrap;
            -webkit-box-flex: 1;
            flex-grow: 1;
            -webkit-box-align: stretch;
            align-items: end !important;
            gap: 1rem;
        }
        .stForm{
            border: none;
            padding: 0px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message['sender'] == 'user':
                st.markdown(
                    f"<div class='message-box'>"
                    f"<img src='https://img.icons8.com/color/48/000000/user.png' class='icon' width='30'/>"
                    f"<div class='message user-message'>{message['content']}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<div class='message-box'>"
                    f"<img src='https://img.icons8.com/fluency/48/000000/chatbot.png' class='icon' width='30'/>"
                    f"<div class='message bot-message'>{message['content']}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

    # Function to handle submission
    def submit():
        user_query = st.session_state.user_query.strip()  # Get the user query and strip whitespace

        # Check for empty input
        if not user_query:
            st.warning("Please enter a question to search.")
            return  # Exit without processing

        st.session_state.chat_history.append({"sender": "user", "content": user_query})
        st.session_state.loading = True

        # Display spinner below the input container
        with spinner_container:
            with st.spinner("Generating response..."):
                # Simulate query to Snowflake
                query = f"SELECT * FROM TABLE(DOCS_LLM('{user_query}'));"
                try:
                    response = session.sql(query).collect()
                    bot_response = response[0].RESPONSE if response else "Sorry, no record found."
                except Exception as e:
                    bot_response = f"Error: {str(e)}"

                # Simulate slight delay for better UX (optional)
                time.sleep(1)

        st.session_state.chat_history.append({"sender": "bot", "content": bot_response})
        st.session_state.user_query = ''  # Clear the input
        st.session_state.loading = False

    # Input box for user query inside a form, which is only submitted on pressing "Enter"
    with st.form(key='chat_form', clear_on_submit=False):
        # Create two columns: one for the text area and one for the submit button
        input_col, button_col = st.columns([9, 1])

        with input_col:
            st.text_area(
                "Type your question:",
                key='user_query',
                placeholder="Ask me anything...",
                height=100,
                label_visibility="collapsed"  # Hide the label for better styling
            )
        
        with button_col:
            submit_button = st.form_submit_button(
                label="Send",
                on_click=submit,
                use_container_width=True  # This ensures the button is stretched to container width
            )
            

    # Spinner container
    spinner_container = st.container()
    if st.session_state.loading:
        with spinner_container:
            with st.spinner("Generating response..."):
                time.sleep(1)  # Optional for UX feedback
