import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
r = requests.get('http://localhost/content', headers=headers)
r.raise_for_status()
soup = BeautifulSoup(r.text, 'html.parser')

select = soup.find('select', {'id': 'num'})
values = [ option['value'] for option in select.find_all('option') if option['value'] != '' ]

print(values)
names = []
for value in values:
    print(value)
    r = requests.get(f"http://localhost/user/?id={value}", headers=headers)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    container = soup.find('div', class_='user-list')
    items = container.select("ul > li")
    
    for li in items:
        first = li.select_one("div.name-details > div > span.first-name")
        last = li.select_one("div.name-details > div > span.last-name")
        print(first, last)
        first_name = first.text.strip() if first else ""
        last_name  = last.text.strip()  if last  else ""

        full_name = f"{first_name} {last_name}".strip()
        if full_name:
            names.append(full_name)

print(names)
with open('names.txt', 'w') as f:
    f.write('\n'.join(names))
