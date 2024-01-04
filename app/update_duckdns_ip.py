import requests


def update_duckdns_ip():
    duckdns_backend_url = 'https://www.duckdns.org/update?domains={chi-chi}&token={7614a19e-1ead-4bb9-9f8a-d1be756455cd}&verbose=true'
    # Replace {DUCKDNS_DOMAIN} and {TOKEN} with your actual DuckDNS domain and token

    response = requests.get(duckdns_backend_url)

    if response.status_code == 200:
        print("IP updated successfully on DuckDNS")
    else:
        print("Failed to update IP on DuckDNS")


if __name__ == "__main__":
    update_duckdns_ip()
