import streamlit as st
import snowflake.connector
from snowflake.snowpark import Session
from snowflake.snowpark import functions as F

# Input fields for Snowflake credentials
user = st.text_input("Snowflake Username")
password = st.text_input("Snowflake Password", type="password")
account = st.text_input("Snowflake Account (e.g., xy12345.us-east-1)")
warehouse = st.text_input("Warehouse")
database = st.text_input("Database")
schema = st.text_input("Schema")

# Button to connect to Snowflake and create a session
if st.button("Connect to Snowflake"):
    try:
        # Create the connection using Snowflake Connector (optional, for initial test)
        conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            warehouse=warehouse,
            database=database,
            schema=schema
        )
        st.success("Connection successful!")

        # Example query to fetch the current date
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_DATE;")
        result = cursor.fetchone()
        st.write(f"Current Date: {result[0]}")

        cursor.close()
        conn.close()

        # Create Snowpark Session
        connection_parameters = {
            "user": user,
            "password": password,
            "account": account,
            "warehouse": warehouse,
            "database": database,
            "schema": schema
        }

        # Create and store the Snowpark session in session state
        session = Session.builder.configs(connection_parameters).create()
        st.session_state.session = session  # Store session in session state
        st.success("Snowpark session created successfully!")

    except Exception as e:
        st.error(f"Error: {e}")

# Title and image
st.title("Ai HelpDocs")
st.image('https://img.freepik.com/free-vector/document-vector-colorful-design_341269-1262.jpg?t=st=1733818917~exp=1733822517~hmac=bfa00abe84ac2b735b5a77543a72b0095dfe8af67db18b6474b955b93e1487bd&w=740', width=400, caption='')

# Check if the session is available in session state
if 'session' in st.session_state:
    # Session is available, so we proceed to the user input for the question
    question = st.text_input('Question', 'How can we improve campaigns results and turn people into customers?')

    if st.button("Submit"):
        # Create Tabs
        tab1, tab2, tab3 = st.tabs(["1 - Documents Manuals (Only)", "2 - Internal Documents Logs (Only)", "3 - Combined Documents Insights"])

        with tab1:
            # Review Manuals and provide response/recommendation
            manuals_query = f"""
            SELECT * FROM TABLE(DOCS_LLM('{question}'));
            """
            
            manuals_response = st.session_state.session.sql(manuals_query).collect()

            st.subheader('Recommended actions from review of Documents:')
            st.write(manuals_response[0].FILE_NAME)
            st.write(manuals_response[0].RESPONSE)

            st.subheader('Document manual "chunks" and their relative scores:')
            st.write(manuals_response)

        with tab2:
            # Review Document logs
            logs_query = f"""
            SELECT * FROM TABLE(DOC_LOGS_LLM('{question}'));
            """

            logs_response = st.session_state.session.sql(logs_query).collect()

            st.subheader('Recommended actions from review of Document logs:')
            st.write(logs_response[0].RESPONSE)

            st.subheader('Insights gathered from these most relevant Document logs:')
            st.write(logs_response[0].RELEVANT_DOCS_LOGS)

        with tab3:
            # Combined insights from Documents and Logs
            combined_query = f"""
            SELECT * FROM TABLE(COMBINED_DOC_LLM('{question}'));
            """

            combined_response = st.session_state.session.sql(combined_query).collect()

            st.subheader('Combined Recommendations:')
            st.write(combined_response[0].RESPONSE)

else:
    # If no session is found, ask the user to connect to Snowflake
    st.warning("Please connect to Snowflake to create the session.")
