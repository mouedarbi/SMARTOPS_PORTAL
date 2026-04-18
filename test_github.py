
import requests

def test_github_api():
    repo = "mouedarbi/SMARTOPS"
    url = f"https://api.github.com/repos/{repo}"
    print(f"Testing URL: {url}")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Stars: {data.get('stargazers_count')}")
            print(f"Forks: {data.get('forks_count')}")
        elif response.status_code == 404:
            print("Error: Repository not found (404). Check if it is public.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_github_api()
