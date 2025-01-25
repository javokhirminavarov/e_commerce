from io import BytesIO
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple
import numpy as np
from utils.utils import *

st.set_page_config(layout="wide")

def main():
    st.title("Ichki manbalardagi narxlarni taqqoshlash")
    
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
                            st.session_state['results'] = df
                            st.success(f"{len(df)} ta mashulot topildi!")

    # Show results if available
    if 'results' in st.session_state and not st.session_state['results'].empty:
        df = st.session_state['results']
        
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
        
        # Visualizations 
        tab1, tab2, tab3 = st.tabs(["Narx taqsimoti", "Narx manba kesimida", "To'liq jadval"])
        
        with tab1:
            source_types = df['Source'].unique()

            # Create columns
            columns = st.columns(3)

            # Iterate through columns      
            for i, source in enumerate(source_types[:3]):
                with columns[i]:
                    source_data = df[(df['Source'] == source)]['Price_USD'].dropna()
                    if not source_data.empty:
                        st.plotly_chart(source_vis(source_data, 'Price_USD', f"'{source}' saytidagi narx taqsimoti"), key=f"{source}_ichki", config={'displayModeBar': False})
                    else:
                        st.warning(f"No data available for {product} from selected sources")

        with tab2:
            fig = px.box(
                df,
                x="Source",
                y="Price_USD",
                title="Price Distribution by Source"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with tab3:
            st.dataframe(
                df[['Title', 'Price_USD', 'Currency', 'Source']]
                .sort_values('Price_USD'),
                use_container_width=True
            )
            
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


# st.link_button("Go to gallery", "https://streamlit.io/gallery")

# st.dataframe(
#     df,
#     column_config={
#         "website": st.column_config.LinkColumn()
#     }
# )
