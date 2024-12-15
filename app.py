from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import pandas as pd

app = Flask(__name__)

# Define URLs to scrape
URLS = {
    'Mytek': "https://www.mytek.tn/catalogsearch/result/?q=",
    'Tunisianet': "https://www.tunisianet.com.tn/recherche?controller=search&orderby=price&orderway=asc&s=",  # Updated for Tunisianet search
    'Tdiscount': "https://tdiscount.tn/recherche?controller=search&s="  # Updated for Tdiscount search
}

# Function to scrape prices from websites
def scrape_prices(product_name):
    headers = {'User-Agent': 'Mozilla/5.0'}
    results = []

    for site, url in URLS.items():
        try:
            # Make the request to the website with the updated search URL
            response = requests.get(url + product_name, headers=headers)
            if response.status_code != 200:
                print(f"Error: Unable to fetch data from {site} (Status code: {response.status_code})")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract product details (Customize these selectors for each site)
            if site == 'Mytek':
                prices = soup.find_all('span', class_='price')
                products = soup.find_all('a', class_='product-item-link')
            elif site == 'Tunisianet':
                products = soup.find_all('h2', class_='h3 product-title')
                prices = soup.find_all('span', class_='price')  # Verify the correct selector for price
            elif site == 'Tdiscount':
                prices = soup.find_all('span', class_='price')
                products = soup.find_all('h2', class_='h3 product-title')

            # Check if we found both products and prices
            if not products or not prices:
                print(f"No products or prices found on {site} for {product_name}")
                continue

            # Loop through products and filter based on matching product name
            for price, product in zip(prices[:5], products[:5]):  # Take top 5 products
                product_title = product.text.strip().lower()
                search_term = product_name.lower()

                # Only add product if it matches the search term
                if search_term in product_title:
                    results.append({'site': site, 'product': product.text.strip(), 'price': price.text.strip()})

        except Exception as e:
            print(f"Error scraping {site}: {e}")

    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        product_name = request.form.get('product')
        data = scrape_prices(product_name)
        df = pd.DataFrame(data)
        return render_template('results.html', tables=[df.to_html(classes='data')], titles=df.columns.values)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
