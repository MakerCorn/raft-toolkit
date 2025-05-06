import streamlit as st
import pandas as pd
import json

# Set the page to wide mode
st.set_page_config(layout="wide")

# Load the data
#st.cache
def load_data():
    data_path = '../../output_data_1000-files/output_data_1000-ft.eval.jsonl'
    data = []
    with open(data_path, 'r') as file:
        for line in file:
            data.append(json.loads(line))
    return pd.DataFrame(data)

data = load_data()

# Streamlit UI components
st.title('Evaluation Data Browser')

# Displaying data in a table
st.dataframe(data, use_container_width=True)

# Search functionality
search_query = st.text_input('Enter a search term:')
if search_query:
    filtered_data = data[(data['question'].str.contains(search_query, case=False)) |
                         (data['gold_final_answer'].str.contains(search_query, case=False)) |
                         (data['context'].str.contains(search_query, case=False))]
    st.dataframe(filtered_data)

# Show summary statistics
st.write('Total entries:', data.shape[0])
