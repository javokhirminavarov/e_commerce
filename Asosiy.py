import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.utils import *

st.set_page_config(layout="wide", page_title="iCommerce", page_icon="📈")

def main():
    st.title("Narxlarni taqqoshlash")
    st.markdown("""Elektron tijorat platformalaridagi tovarlar narxlari haqida ma'lumot olish.""")
    
    df_ex = pd.read_csv('ex.csv')
    df = pd.read_csv('uz.csv')
    max_ex = df_ex['Price_USD'].max()
    max_in = df['Price_USD'].max()
    # Summary statistics 
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Jami mahsulotlar soni", len(df_ex)+len(df) , border=True)
    with col2:
        st.metric("Manbalar soni (tashqi)", f"{df_ex['Source'].nunique()}", border=True)
    with col3:
        st.metric("Manbalar soni (ichki)", f"{df['Source'].nunique()}", border=True)
    with col4:
        st.metric("Maksimum narx", f"${max(max_ex, max_in):.2f}", border=True)
    

    st.subheader("TOP 3 tovar narxlari taqsimoti (tashqi)")
    selected_sources_e = st.pills("Manbani tanlash", options=df_ex['Source'].unique(), selection_mode='multi', default=df_ex['Source'].unique())
    product_types = df_ex['Product'].unique()

    # Create columns
    columns = st.columns(3)

    # Loop through products and generate KDE plots
    for i, product in enumerate(product_types[:3]):
        with columns[i]:
            product_data = df_ex[(df_ex['Product'] == product) & (df_ex['Source'].isin(selected_sources_e))]['Price_USD'].dropna()
            if not product_data.empty:  # Check if data exists
                fig = create_kde_plot(product_data, product)
                st.plotly_chart(fig, key=f"{product}_tashqi", config={'displayModeBar': False})
            else:
                st.warning(f"No data available for {product} from selected sources")
    
    st.subheader("TOP 3 tovar narxlari taqsimoti (ichki)")
    selected_sources_i = st.pills("Manbani tanlash", options=df['Source'].unique(), selection_mode='multi', default=df['Source'].unique(), key='ichki_pills')
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
    

    col5, col6 = st.columns(2)
    with col5:
        selected_products = st.pills("Tovarni tanlash", options=df_ex['Product'].unique(), selection_mode='multi', default=df_ex['Product'].unique(), key='tovar_pills_ex')
        source_counts_e = df_ex[df_ex['Product'].isin(selected_products)].groupby("Source")['Title'].count().reset_index()
        source_counts_e.columns = ['Manba', 'Soni']
        fig = px.bar(
            source_counts_e,
            x="Manba",
            y="Soni",
            title="Tashqi manba kesimida mahsulotlar soni"
            )
        st.plotly_chart(fig, key='tashqi_manba', config={'displayModeBar': False})
    
    with col6:
        selected_products_i = st.pills("Tovarni tanlash", options=df['Product'].unique(), selection_mode='multi', default=df['Product'].unique(), key='tovar_pills_in')
        source_counts_i = df[df['Product'].isin(selected_products_i)].groupby("Source")['Title'].count().reset_index()
        source_counts_i.columns = ['Manba', 'Soni']
        fig = px.bar(
            source_counts_i,
            x="Manba",
            y="Soni",
            title="Ichki manba kesimida mahsulotlar soni"
            )
        st.plotly_chart(fig, key='ichki_manba', config={'displayModeBar': False})
    
    df_all = pd.concat([df, df_ex])
    # Download button
    st.download_button(
        label="📥 CSVga yuklash",
        data=df_all.to_csv(index=False).encode('utf-8'),
        file_name="price_comparison.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()