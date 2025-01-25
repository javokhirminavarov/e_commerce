from io import BytesIO
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple
import numpy as np
from utils.utils import *
from scipy.stats import gaussian_kde
import plotly.graph_objects as go
st.set_page_config(layout="wide")

def main():
    st.title("Narxlarni taqqoshlash")
    st.markdown("""
    Elektron tijorat platformalaridagi tovarlar narxlari haqida ma'lumot olish.
    """)
    
    # Show results if available
    if 'results' in st.session_state and not st.session_state['results'].empty:
        df = st.session_state['results']
        df = pd.read_csv('price_comparison_samsung.csv')
        # Summary statistics 
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Jami mahsulotlar soni", len(df), border=True)
        with col2:
            st.metric("O'rtacha narx", f"${df['Price_USD'].mean():.2f}", border=True)
        with col3:
            st.metric("Minimum narx", f"${df['Price_USD'].min():.2f}", border=True)
        with col4:
            st.metric("Maksimum narx", f"${df['Price_USD'].max():.2f}", border=True)
        

        st.subheader("TOP 3 tovar narxlari taqsimoti (tashqi)")
        selected_sources_e = st.pills("Manbani tanlash", options=df['Source'].unique(), selection_mode='multi', default=df['Source'].unique())
        df['Product'] = np.random.choice(['iPhone', 'Shoes', 'Airpods', 'Samsung tv', 'Mouse'], size=len(df))
        product_types = df['Product'].unique()

        # Create columns
        columns = st.columns(3)

        # Loop through products and generate KDE plots
        for i, product in enumerate(product_types[:3]):
            with columns[i]:
                product_data = df[(df['Product'] == product) & (df['Source'].isin(selected_sources_e))]['Price_USD'].dropna()
                if not product_data.empty:  # Check if data exists
                    fig = create_kde_plot(product_data, product)
                    st.plotly_chart(fig, key=f"{product}_tashqi", config={'displayModeBar': False})
                else:
                    st.warning(f"No data available for {product} from selected sources")
        

        st.subheader("TOP 3 tovar narxlari taqsimoti (ichki)")
        selected_sources_i = st.pills("Manbani tanlash", options=df['Source'].unique(), selection_mode='multi', default=df['Source'].unique(), key='ichki_pills')
        df['Product'] = np.random.choice(['iPhone', 'Shoes', 'Airpods', 'Samsung tv', 'Mouse'], size=len(df))
        product_types = df['Product'].unique()

        # Create columns
        columns = st.columns(3)

        # Loop through products and generate KDE plots
        for i, product in enumerate(product_types[:3]):
            with columns[i]:
                product_data = df[(df['Product'] == product) & (df['Source'].isin(selected_sources_i))]['Price_USD'].dropna()
                if not product_data.empty:  # Check if data exists
                    fig = create_kde_plot(product_data, product)
                    st.plotly_chart(fig, key=f"{product}_ichki", config={'displayModeBar': False})
                else:
                    st.warning(f"No data available for {product} from selected sources")

        st.subheader("Mahsulotlar soni manbalar kesimida")
        selected_products = st.pills("Tovarni tanlash", options=df['Product'].unique(), selection_mode='multi', default=df['Product'].unique(), key='tovar_pills')

        col5, col6 = st.columns(2)
        with col5:
            source_counts_e = df[df['Product'].isin(selected_products)].groupby("Source")['Title'].count().reset_index()
            source_counts_e.columns = ['Manba', 'Soni']
            fig = px.bar(
                source_counts_e,
                x="Manba",
                y="Soni",
                title="Tashqi manba kesimida mahsulotlar soni"
                )
            st.plotly_chart(fig, key='tashqi_manba', config={'displayModeBar': False})
        
        with col6:
            source_counts_i = df.groupby("Source")['Title'].count().reset_index()
            source_counts_i.columns = ['Manba', 'Soni']
            fig = px.bar(
                source_counts_i,
                x="Manba",
                y="Soni",
                title="Ichki manba kesimida mahsulotlar soni"
                )
            st.plotly_chart(fig, key='ichki_manba', config={'displayModeBar': False})
        

        # Download button
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        excel_data = buffer.getvalue()
        st.download_button(
            "📥 Excelga yuklash",
            excel_data,
            f"price_comparison_{product}.xlsx",
            "application/vnd.ms-excel",
            key='download-excel'
        )

if __name__ == "__main__":
    main()