import os
import streamlit as st
import snowflake.connector
from snowflake.snowpark import Session
from dotenv import load_dotenv
import time
import pyperclip  # For clipboard copying

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

# Initialize session state variables for chat history and loading state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'loading' not in st.session_state:
    st.session_state.loading = False

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

    st.title("💬 AI HelpDocs")

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
            position: relative;
        }
        .icon {
            margin-right: 15px;
        }
        .message-box {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .copy-button {
            position: absolute;
            top: 5px;
            right: 10px;
            background-color: #1E88E5;
            color: white;
            border-radius: 5px;
            padding: 5px 10px;
            font-size: 12px;
            cursor: pointer;
        }
        .copy-button:hover {
            background-color: #1565C0;
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
        div.stButton > button:hover {
            background-color: #1565C0; /* Darker background on hover */
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
                # Display bot's response inside a container
                response_text = message['content']
                st.markdown(f"""
                    <div class="message-box">
                        <img src="https://img.icons8.com/fluency/48/000000/chatbot.png" class="icon" width="30"/>
                        <div class="message bot-message">
                            {response_text}
                            <button class="copy-button" onclick="navigator.clipboard.writeText('{response_text}').then(function() {{ alert('Text copied!'); }}).catch(function(err) {{ console.error('Copy failed', err); }});">Copy</button>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Copy response to clipboard when button is clicked (using pyperclip)
                if st.button('Copy Response', key=message['content']):
                    pyperclip.copy(response_text)
                    st.success("Text copied successfully!")

    # Chat input box using st.chat_input
    prompt = st.chat_input("Type your question here...")

    # Check if input is blank and display a warning if so
    if prompt == "":
        st.warning("Please enter a question before submitting.")
    
    # If user submits a prompt and it's not empty, add it to chat history and handle the response
    elif prompt:
        # Store the current prompt in the session state (display immediately)
        st.session_state.chat_history.append({"sender": "user", "content": prompt})

        # Indicate loading state
        st.session_state.loading = True

        # Display the user message immediately
        with chat_container:
            st.markdown(
                f"<div class='message-box'>"
                f"<img src='https://img.icons8.com/color/48/000000/user.png' class='icon' width='30'/>"
                f"<div class='message user-message'>{prompt}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

        # Display "Bot is typing..." message with a spinner
        typing_placeholder = st.empty()
        with typing_placeholder:
            # Display a spinner while the response is being fetched
            with st.spinner('We\'re getting response...'):
                # Simulate the delay of fetching data from Snowflake
                query = f"SELECT * FROM TABLE(DOCS_LLM('{prompt}'));"
                try:
                    # Query Snowflake for bot's response
                    response = session.sql(query).collect()
                    bot_response = response[0].RESPONSE if response else "Sorry, no record found."
                except Exception as e:
                    bot_response = f"Error: {str(e)}"

        # After fetching data, start typing the bot's response and clear the spinner
        typing_placeholder.empty()

        # Display the bot's response character by character
        bot_placeholder = st.empty()  # This placeholder will hold the bot response
        simulated_response = ""
        for char in bot_response:
            simulated_response += char
            bot_placeholder.markdown(f"<div class='message-box'>"
                                     f"<img src='https://img.icons8.com/fluency/48/000000/chatbot.png' class='icon' width='30'/>"
                                     f"<div class='message bot-message'>{simulated_response}</div>"
                                     f"</div>", unsafe_allow_html=True)
            time.sleep(0.01)  # Faster typing effect

        # Add the bot's final response to chat history
        st.session_state.chat_history.append({"sender": "bot", "content": bot_response})

        # Reset loading state
        st.session_state.loading = False
