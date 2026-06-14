import requests
import yaml

l_current_url = "https://raw.githubusercontent.com/unitedstates/congress-legislators/refs/heads/main/legislators-current.yaml"
l_historical_url = "https://raw.githubusercontent.com/unitedstates/congress-legislators/refs/heads/main/legislators-historical.yaml"
e_url = "https://raw.githubusercontent.com/unitedstates/congress-legislators/refs/heads/main/executive.yaml"

def get_yaml(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        yaml_data = yaml.safe_load(response.text)
        print(yaml_data)
        return yaml_data
    except requests.exceptions.RequestException as e:
        print(f'Error getting the file {e}')
    except yaml.YAMLError as e:
        print(f'Error parsing the yaml {e}')
        
l_current_yaml = get_yaml(l_current_url)
l_historical_yaml = get_yaml(l_historical_url)
e_yaml = get_yaml(e_url)
l_yaml = l_historical_yaml + l_current_yaml 