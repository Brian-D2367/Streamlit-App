import os
import streamlit as st
import snowflake.connector
from snowflake.snowpark import Session
from dotenv import load_dotenv

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

# Initialize session state variables for chat history, loading state, and first response flag
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'loading' not in st.session_state:
    st.session_state.loading = False

if 'first_response' not in st.session_state:
    st.session_state.first_response = False

# Create Snowpark session if the connection was successful
if connection_successful:
    # Create and store Snowpark session
    session = Session.builder.configs(credentials).create()
    st.session_state.session = session

    # Chat-like UI
    st.title("AI HelpDocs Chat")

    st.markdown(
        """<style>
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
        </style>""",
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
    def submit(user_query):
        # Add user message to chat history
        st.session_state.chat_history.append({"sender": "user", "content": user_query})

        # Generate response (simulate query to Snowflake)
        with st.spinner("Generating response..."):
            try:
                # Query Snowflake for the response
                query = f"SELECT * FROM TABLE(DOCS_LLM('{user_query}'));"
                response = session.sql(query).collect()
                bot_response = response[0].RESPONSE if response else "Sorry, I couldn't find an answer."
            except Exception as e:
                bot_response = f"Error: {str(e)}"

            # Add the bot response to the chat history
            st.session_state.chat_history.append({"sender": "bot", "content": bot_response})

        # Set loading to False after the response is generated
        st.session_state.loading = False
        st.session_state.first_response = True  # Flag to indicate that the first response is done

    # Input box for user query with on_change handler
    user_query = st.text_input(
        "Type your question:",
        value=st.session_state.get("user_query", ""),  # Use session state to retain the input value
        placeholder="Ask me anything...",
        key="user_query",  # key for text_input to maintain state
    )

    # Disable the send button while loading
    send_button = st.button("Send", disabled=st.session_state.loading)

    # Handle submission on button click if user query exists and button is pressed
    if send_button and user_query:
        st.session_state.loading = True  # Enable loading state
        submit(user_query)  # Pass user query to submit function
        st.rerun()  # Trigger a re-render to clear the input field

    # Handle submission on text input change, but only when the user types and it's the first response
    if st.session_state.get("user_query", "") and not st.session_state.first_response and not st.session_state.loading:
        st.session_state.loading = True  # Enable loading state
        submit(user_query)  # Pass user query to submit function
        st.session_state.user_query = ""  # Clear user_query after the first response
        st.rerun()  # Trigger a re-render to clear the input field

else:
    st.error(f"Failed to connect to Snowflake: {error_message}")
    st.warning("Please check your Snowflake credentials or environment settings.")