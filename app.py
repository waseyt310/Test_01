import streamlit as st
import pyodbc
from typing import List, Tuple, Any, Optional
import pandas as pd

# Set page configuration
st.set_page_config(
    page_title="SQL Data Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add header and description
st.title("SQL Server Data Explorer")
st.markdown("""
This application connects to a SQL Server database and allows you to explore the data.
Enter your SQL query below and view the results.
""")

def init_connection() -> Optional[pyodbc.Connection]:
    """
    Initialize the database connection using credentials from st.secrets.
    
    Returns:
        Optional[pyodbc.Connection]: Database connection object if successful, None otherwise
    """
    try:
        return pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={st.secrets['db_credentials']['server']};"
            f"DATABASE={st.secrets['db_credentials']['database']};"
            f"UID={st.secrets['db_credentials']['username']};"
            f"PWD={st.secrets['db_credentials']['password']}"
        )
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

# Initialize connection with caching to only run once
@st.cache_resource
def get_connection() -> Optional[pyodbc.Connection]:
    """
    Get cached database connection.
    
    Returns:
        Optional[pyodbc.Connection]: Cached database connection
    """
    return init_connection()

conn = get_connection()

# Perform query with caching to only rerun when the query changes or after 10 min
@st.cache_data(ttl=600)
def run_query(query: str) -> pd.DataFrame:
    """
    Execute SQL query and return results as a DataFrame using pyodbc cursor.
    
    Args:
        query (str): SQL query to execute
        
    Returns:
        pd.DataFrame: Query results as a DataFrame
    """
    try:
        if conn is None:
            st.error("Database connection is not established")
            return pd.DataFrame()
        
        # Use cursor directly instead of pandas.read_sql
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Get column names from cursor description
        columns = [column[0] for column in cursor.description] if cursor.description else []
        
        # Fetch all results
        rows = cursor.fetchall()
        
        # Close the cursor
        cursor.close()
        
        # If we have results, convert to DataFrame
        if rows and columns:
            # Convert pyodbc Row objects to list of lists
            data = [list(row) for row in rows]
            return pd.DataFrame(data, columns=columns)
        else:
            return pd.DataFrame()
            
    except pyodbc.Error as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error executing query: {e}")
        return pd.DataFrame()

# Create sidebar with options
with st.sidebar:
    st.header("Query Options")
    
    example_queries = {
        "Select a sample query": "",
        "List all tables": "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';",
        "List all columns from a table": "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'YourTableName';",
        "Count rows in a table": "SELECT COUNT(*) as row_count FROM YourTableName;",
        "Get data with limit": "SELECT TOP 10 * FROM YourTableName;"
    }
    
    selected_example = st.selectbox(
        "Example Queries",
        options=list(example_queries.keys())
    )
    
    # Advanced options
    st.subheader("Advanced Options")
    show_query_time = st.checkbox("Show query execution time", value=True)
    enable_download = st.checkbox("Enable CSV download", value=True)

# Create query input area
query = st.text_area(
    "Enter your SQL query",
    value=example_queries[selected_example] if selected_example else "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';",
    height=100
)

# Execute button
if st.button("Execute Query"):
    if conn is None:
        st.error("Database connection failed. Please check your credentials.")
    elif not query.strip():
        st.warning("Please enter a SQL query.")
    else:
        with st.spinner("Executing query..."):
            # Get query results
            df = run_query(query)
            
            if not df.empty:
                # Display number of rows returned
                st.success(f"Query returned {len(df)} rows.")
                
                # Display the results in a data table
                st.dataframe(df)
                
                # Enable download as CSV
                if enable_download:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download data as CSV",
                        data=csv,
                        file_name="query_results.csv",
                        mime="text/csv"
                    )
            else:
                st.info("Query returned no results or encountered an error.")

# Footer
st.markdown("---")
st.markdown("© 2025 SQL Data Explorer | Created with Streamlit")

