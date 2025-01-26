import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple
import numpy as np
from utils.utils import *

st.set_page_config(layout="wide")

def main():
    st.title("Tashqi manbalardagi narxlarni taqqoshlash")
    
    # Sidebar inputs
    with st.sidebar:
        st.header("Qidiruv parameterlari")
        product = st.text_input("Mahsulot nomi", placeholder="masalan, samsung tv, nike shoes")
        excluded_words = st.text_input("Keraksiz so'zlar", placeholder="masalan, case, cover")
        
        col1, col2 = st.columns(2)
        with col1:
            min_price = st.number_input("Min narx ($)", 0.0)
        with col2:
            max_price = st.number_input("Max narx ($)", 10000.0)
        
        # Variable to store search results
        search_results = None
        
        if st.button("🔍 Qidirish", use_container_width=True):
            if not product:
                st.error("Mahsulot nomini kiriting")
            else:
                with st.spinner("Qidiruv amalga oshirilmoqda..."):
                    scraper = PriceScraperMulti()
                    df = scraper.scrape_all(product)
                    
                    if not df.empty:
                        # Filter data
                        if excluded_words:
                            exclude_pattern = '|'.join(word.strip().lower() for word in excluded_words.split(','))
                            df = df[~df['Title'].str.lower().str.contains(exclude_pattern, na=False)]
                        
                        df = df[(df['Price_USD'] >= min_price) & (df['Price_USD'] <= max_price)]
                        
                        if df.empty:
                            st.error("Ma'lumot topilmadi. Qidiruv parametrlarini o'zgartiring")
                        else:
                            search_results = df
                            st.success(f"{len(df)} ta mashulot topildi!")

    # Show results if available
    if search_results is not None and not search_results.empty:
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Jami mahsulotlar soni", len(search_results), border=True)
        with col2:
            st.metric("O'rtacha narx", f"${search_results['Price_USD'].mean():.2f}", border=True)
        with col3:
            st.metric("Minimum narx", f"${search_results['Price_USD'].min():.2f}", border=True)
        with col4:
            st.metric("Maksimum narx", f"${search_results['Price_USD'].max():.2f}", border=True)
        
        # Visualizations 
        tab1, tab2, tab3 = st.tabs(["Narx taqsimoti", "Narx manba kesimida", "To'liq jadval"])
        
        with tab1:
            source_types = df['Source'].unique()

            # Create columns
            columns = st.columns(2)

            # Iterate through columns      
            for i, source in enumerate(source_types[:2]):
                with columns[i]:
                    source_data = df[(df['Source'] == source)]['Price_USD'].dropna()
                    if not source_data.empty:
                        st.plotly_chart(source_vis(source_data, 'Price_USD', f"'{source}' saytidagi narx taqsimoti"), key=f"{source}_tashqi", config={'displayModeBar': False})
                    else:
                        st.warning(f"No data available for {product} from selected sources")

        with tab2:
            fig = px.box(
                df,
                x="Source",
                y="Price_USD",
                title="Manba kesimida narx taqsimoti"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with tab3:
            df['Price_USD'] = df['Price_USD'].round(1)
            st.dataframe(
                df[['Title', 'Price_USD', 'Currency', 'Source']]
                .sort_values('Price_USD'),
                use_container_width=True
            )
            
        # Download button
        st.download_button(
            label="📥 CSVga yuklash",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name="price_comparison.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()