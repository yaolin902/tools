import argparse
import requests
import re

parser = argparse.ArgumentParser(description="Search for sensitive files in the Wayback Machine")
parser.add_argument("-d", required=True, help="Target domain file (one domain per line)", dest="domain")
args = parser.parse_args()

# Target domain
if args.domain:
    with open(args.domain) as f:
        domains = [line.strip() for line in f]

for domain in domains:
    print(f"[+] Searching {domain}")

    # Step 1: Get all URLs from Wayback CDX API
    all_urls = requests.get(
        f"https://web.archive.org/cdx/search/cdx?url=*.{domain}/*&fl=original&collapse=urlkey&output=text"
    ).text.splitlines()

    # Step 2: Filter for sensitive file extensions
    extensions = ( r".*\.(sql|db|sqlite|mdb|accdb|dbf|frm|myd|myi|ibd|conf|config|cfg|ini|properties|" r"yml|yaml|json|toml|env|htaccess|htpasswd|bak|backup|old|orig|save|tmp|temp|~|swp|" r"swo|log|logs|out|err|debug|trace|pem|crt|cer|key|pub|p12|pfx|jks|keystore|csr|der|" r"php~|asp~|jsp~|inc|class|jar|war|pyc|pyo|zip|rar|7z|tar|tar\.gz|tgz|tar\.bz2|gz|" r"passwd|shadow|bashrc|bash_history|zsh_history|mysql_history|psql_history|gitignore|" r"git|svn|ds_store|ftpconfig|sftp-config|credentials|secrets|vault|php\.bak|aspx\.bak|" r"jsp\.bak|include|include\.php|class\.php|functions\.php|eml|msg|pst|ost|mbox|doc|" r"docx|xls|xlsx|pdf|txt|csv|md|readme|todo|notes)$" )

    sensitive_urls = [url for url in all_urls if re.match(extensions, url)]

    # Step 3: Check which return 400-series codes
    not_found = []
    for url in sensitive_urls:
        try:
            r = requests.head(url, timeout=5)
            if 400 <= r.status_code < 500:
                not_found.append(url)
        except requests.RequestException:
            continue

    # Step 4: Save results
    with open(f"./logs/{domain}_all_urls.txt", "w") as f:
        f.write("\n".join(all_urls))
    with open(f"./logs/{domain}_sensitive_urls.txt", "w") as f:
        f.write("\n".join(sensitive_urls))
    with open(f"./logs/{domain}_404_urls.txt", "w") as f:
        f.write("\n".join(not_found))
    print(f"[+] {domain}: Total URLs: {len(all_urls)}")
    print(f"[+] {domain}: Sensitive URLs: {len(sensitive_urls)}")
    print(f"[+] {domain}: Likely deleted (404s): {len(not_found)}")
