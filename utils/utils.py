import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple
import re
from concurrent.futures import ThreadPoolExecutor
import time
import random
from scipy.stats import gaussian_kde
import plotly.graph_objects as go
import numpy as np

class PriceScraperMulti:
    def __init__(self):
        # Enhanced headers to better mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
        }
        # Currency conversion rates
        self.conversion_rates = {
            'EUR': 1.11459,
            'GBP': 1.31161,
            'JPY': 0.00926487,
            'KRW': 0.001,
            'CNY': 0.13988
        }
        # Session for maintaining cookies
        self.session = requests.Session()

    def get_random_delay(self):
        """Add random delay between requests to avoid rate limiting"""
        return random.uniform(1, 3)

    def clean_price(self, price_str: str) -> float:
        """Enhanced price cleaning function"""
        if not price_str:
            return None
        
        # Remove all non-digit characters except . and ,
        price_str = re.sub(r'[^\d.,]', '', price_str)
        
        # Handle different price formats
        try:
            if ',' in price_str and '.' in price_str:
                # Format: 1,234.56
                if price_str.find(',') < price_str.find('.'):
                    price_str = price_str.replace(',', '')
                # Format: 1.234,56
                else:
                    price_str = price_str.replace('.', '').replace(',', '.')
            elif ',' in price_str:
                # Check if comma is decimal separator
                if len(price_str.split(',')[1]) <= 2:
                    price_str = price_str.replace(',', '.')
                else:
                    price_str = price_str.replace(',', '')
            
            return float(price_str)
        except (ValueError, IndexError):
            return None

    def scrape_amazon(self, domain: str, product: str) -> pd.DataFrame:
        """Scrape product data from Amazon"""
        base_url = f"https://www.amazon.{domain}"
        search_url = f"{base_url}/s?k={product.replace(' ', '+')}&ref=nb_sb_noss"
        
        try:
            # Add random delay
            time.sleep(self.get_random_delay())
            
            # Fetch the search page
            response = self.session.get(search_url, headers=self.headers, timeout=15, verify=False)
            # if response.status_code != 200:
            #     st.warning(f"Failed to access Amazon {domain}. Status code: {response.status_code}")
            #     return pd.DataFrame()

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all product containers
            products = soup.find_all('div', {'data-component-type': 's-search-result'})
            # if not products:
            #     st.warning(f"No products found on Amazon {domain} for '{product}'.")
            #     return pd.DataFrame()

            items = []
            for product in products:
                try:
                    title = product.find('span', {'class': 'a-text-normal'}) or product.find('h2')
                    price = product.find('span', {'class': 'a-price-whole'}) or product.find('span', {'class': 'a-offscreen'})
                    
                    if title and price:
                        price_value = self.clean_price(price.text)
                        if price_value and price_value > 0:
                            currency = self.get_currency(domain)
                            items.append({
                                'Title': title.text.strip(),
                                'Price': price_value,
                                'Currency': currency,
                                'Source': f'Amazon {domain.upper()}',
                                'Price_USD': price_value * self.conversion_rates.get(currency, 1)
                            })
                except Exception:
                    continue  # Skip problematic items

            return pd.DataFrame(items)

        except requests.exceptions.SSLError as ssl_error:
            st.warning(f"SSL error while accessing Amazon {domain}: {str(ssl_error)}")
            return pd.DataFrame()
        except Exception as e:
            st.warning(f"Error scraping Amazon {domain}: {str(e)}")
            return pd.DataFrame()


    def scrape_ebay(self, product: str) -> pd.DataFrame:
        """Scrape product data from eBay with enhanced error handling"""
        try:
            # Add random delay
            time.sleep(self.get_random_delay())
            
            # Try different eBay URLs
            urls = [
                f"https://www.ebay.com/sch/i.html?_nkw={product.replace(' ', '+')}",
                f"https://www.ebay.com/sch/i.html?_nkw={product.replace(' ', '+')}&_sacat=0"
            ]
            
            items = []
            for url in urls:
                response = self.session.get(url, headers=self.headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try different selectors for product containers
                    products = (soup.find_all('div', {'class': 's-item__info'}) or
                              soup.find_all('div', {'class': 'srp-river-results'}))
                    
                    for product in products:
                        try:
                            # Try different possible selectors for title and price
                            title = (product.find('div', {'class': 's-item__title'}) or
                                   product.find('h3', {'class': 's-item__title'}))
                            
                            price = (product.find('span', {'class': 's-item__price'}) or
                                   product.find('span', {'class': 'POSITIVE'}))
                            
                            if title and price and 'Shop on eBay' not in title.text:
                                price_value = self.clean_price(price.text)
                                if price_value and price_value > 0:
                                    items.append({
                                        'Title': title.text.strip(),
                                        'Price': price_value,
                                        'Currency': 'USD',
                                        'Source': 'eBay',
                                        'Price_USD': price_value
                                    })
                        except Exception as e:
                            continue  # Skip problematic items
                            
                if items:  # If we found items, no need to try other URLs
                    break
                    
            return pd.DataFrame(items)

        except Exception as e:
            st.warning(f"Error scraping eBay: {str(e)}")
            return pd.DataFrame()

    def get_currency(self, domain: str) -> str:
        """Get currency based on domain"""
        currency_map = {
            'com': 'USD',
            'co.uk': 'GBP',
            'de': 'EUR',
            'fr': 'EUR',
            'co.jp': 'JPY',
            'it': 'EUR',
            'es': 'EUR'
        }
        return currency_map.get(domain, 'USD')

    def scrape_all(self, product: str) -> pd.DataFrame:
        """Scrape data from all sources"""
        amazon_domains = ['com', 'co.uk', 'de']
        results = []
        
        # First try eBay (often more reliable)
        ebay_df = self.scrape_ebay(product)
        if not ebay_df.empty:
            results.append(ebay_df)
            
        # Then try Amazon domains one by one
        for domain in amazon_domains:
            df = self.scrape_amazon(domain, product)
            if not df.empty:
                results.append(df)
                
        if not results:
            st.error("Natija topilmadi")
            return pd.DataFrame()
            
        # Combine all results
        df = pd.concat(results, ignore_index=True)
        
        # Remove duplicates and sort by price
        df = df.drop_duplicates(subset=['Title', 'Price_USD'], keep='first')
        df = df.sort_values('Price_USD')
        
        return df

# Define a function to create KDE plots
def create_kde_plot(data, product_name):
    if len(data) < 2:
        return st.warning("Not enough data points to create KDE plot.")
        

    kde = gaussian_kde(data)
    x_range = np.linspace(data.min(), data.max(), 100)  # Generate a range for the KDE
    kde_values = kde(x_range)*10000
    
    # Calculate the 10th percentile (quintile)
    low_density_cutoff = np.percentile(data, 10)

    # Create the plot
    fig = go.Figure()

    # Add the KDE line
    fig.add_trace(go.Scatter(
        x=x_range,
        y=kde_values,
        mode='lines',
        name='KDE',
        line=dict(width=2)
    ))

    # Highlight the low-density region (lowest 10%)
    segment_x = x_range[x_range <= low_density_cutoff]
    segment_y = kde_values[x_range <= low_density_cutoff]
    
    fig.add_trace(go.Scatter(
        x=np.concatenate([segment_x, segment_x[::-1]]),
        y=np.concatenate([segment_y, np.zeros_like(segment_y)]),
        fill='toself',
        fillcolor='rgba(81, 168, 249, 0.5)',
        mode='lines',
        line=dict(width=0),
        name='Low Density (Lowest 10%)'
    ))

    fig.update_layout(
        title=f"'{product_name.capitalize()}' tovari narx taqsimoti",
        xaxis_title="Narx",
        yaxis_title="Zichlik",
        showlegend=False,
        dragmode=False
    )

    return fig

# Define a function to visualise
def source_vis(df, x, title):
 
    fig = px.histogram(
        df, 
        x=x,
        title=title,
        nbins=30
    )
    fig.update_layout(
        xaxis_title='Narxi, AQSh dollari',
        yaxis_title='Soni',
        showlegend=False)

    return fig