import time
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re  #cleaning prices

app = Flask(__name__)

# URLs to scrape
URLS = {
    'Mytek': "https://www.mytek.tn/catalogsearch/result/?q=",
    'Tunisianet': "https://www.tunisianet.com.tn/recherche?controller=search&orderby=price&orderway=asc&s=",
    'Tdiscount': "https://tdiscount.tn/recherche?controller=search&s="
}

def solve_captcha(site_key, url):
    try:
        response = requests.post("http://2captcha.com/in.php", data={
            "key": "43065cddd4dd28ddb7491a0c0cf153a7",
            "method": "userrecaptcha",
            "googlekey": site_key,
            "pageurl": url,
            "json": 1
        })
        request_result = response.json()
        if request_result['status'] != 1:
            print("Error submitting CAPTCHA to 2Captcha:", request_result)
            return None

        captcha_id = request_result['request']

        print("Waiting for CAPTCHA solution...")
        for _ in range(30):  
            time.sleep(5)
            result_response = requests.get(f"http://2captcha.com/res.php?key={"43065cddd4dd28ddb7491a0c0cf153a7"}&action=get&id={captcha_id}&json=1")
            result = result_response.json()
            if result['status'] == 1:
                print("CAPTCHA solved successfully!")
                return result['request']
        print("CAPTCHA solution timed out.")
        return None

    except Exception as e:
        print(f"Error solving CAPTCHA: {e}")
        return None
    
#clean price
def clean_price(price_str):
    
    price = re.sub(r"[^\d.,]", "", price_str)  
    price = price.replace(',', '.') 
    try:
        return float(price)
    except ValueError:
        return None


def scrape_prices(product_name):
    headers = {'User-Agent': 'Mozilla/5.0'}
    results = []

    for site, url in URLS.items():
        try:
            response = requests.get(url + product_name, headers=headers)
            if response.status_code != 200:
                print(f"Error: Unable to fetch data from {site} (Status code: {response.status_code})")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            if site == 'Mytek':
                prices = soup.find_all('span', class_='price')
                products = soup.find_all('a', class_='product-item-link')
            elif site == 'Tunisianet':
                products = soup.find_all('h2', class_='h3 product-title')
                prices = soup.find_all('span', class_='price')
            elif site == 'Tdiscount':
                prices = soup.find_all('span', class_='price')
                products = soup.find_all('h2', class_='h3 product-title')

            if not products or not prices:
                print(f"No products or prices found on {site} for {product_name}")
                continue

            for price, product in zip(prices[:5], products[:5]):
                product_title = product.text.strip().lower()
                search_term = product_name.lower()
                if search_term in product_title:
                    price_clean = clean_price(price.text.strip())
                    if price_clean:  # Only add valid prices
                        results.append({
                            'site': site,
                            'product': product.text.strip(),
                            'price': price_clean
                        })

        except Exception as e:
            print(f"Error scraping {site}: {e}")

    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        product_name = request.form.get('product')
        data = scrape_prices(product_name)

        lowest_price_entry = min(data, key=lambda x: x['price'], default=None)

        df = pd.DataFrame(data)
        lowest_price_info = {
            "site": lowest_price_entry['site'],
            "product": lowest_price_entry['product'],
            "price": lowest_price_entry['price']
        } if lowest_price_entry else None

        return render_template('results.html', tables=[df.to_html(classes='data')], 
                               titles=df.columns.values, lowest_price=lowest_price_info)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
