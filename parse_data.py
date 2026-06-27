import requests
import os
import yaml
import pandas as pd
from tqdm import tqdm
from datetime import date, datetime, timedelta
from pathlib import Path
import pickle
import calendar
import sys

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# FOR DEBUGGING:
use_pickle = True

today = str(date.today())

current_dir = os.getcwd()
pickle_file = 'saved_data_' + today + '.pkl'

pickle_filepath = Path(current_dir + '/' + pickle_file)
if pickle_filepath.is_file() and use_pickle:
    with open(pickle_filepath, 'rb') as file:
        senate_df, house_df, court_df, exec_df, legislators, executives, judicials = pickle.load(file)
    
else:
    # Home page where the following urls come from:
    # https://github.com/unitedstates/congress-legislators/tree/main
    l_current_url = "https://raw.githubusercontent.com/unitedstates/congress-legislators/refs/heads/main/legislators-current.yaml"
    l_historical_url = "https://raw.githubusercontent.com/unitedstates/congress-legislators/refs/heads/main/legislators-historical.yaml"
    e_url = "https://raw.githubusercontent.com/unitedstates/congress-legislators/refs/heads/main/executive.yaml"

    states = [
            "AK", "AL", "AR", "AZ", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "IA", "ID", "IL", "IN", "KS", "KY", "LA", "MA", "MD",
            "ME", "MI", "MN", "MO", "MS", "MT", "NC", "ND", "NE", "NH",
            "NJ", "NM", "NV", "NY", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VA", "VT", "WA", "WI", "WV", "WY"
        ]

    def standardize_parties(terms):
        replacements = {
            # Formatting / naming standardization
            'Anti Jackson': 'Anti-Jacksonian',
            'Anti Jacksonian': 'Anti-Jacksonian',
            'Anti Mason': 'Anti-Masonic',
            'Anti Masonic': 'Anti-Masonic',
            'Anti-administration': 'Anti-Administration',
            'Pro-administration': 'Pro-Administration',
            'Democratic': 'Democrat',
            'Democratic-Republican': 'Democratic Republican',
            'Ind. Democrat': 'Independent Democrat',
            'Ind. Republican': 'Independent Republican',
            'Ind. Whig': 'Independent Whig',
            'Jackson': 'Jacksonian',
            'Jackson Republican': 'Jacksonian Republican',
            'National Greenbacker': 'Greenback',
            'no party': 'None/Unknown',
            'Unknown': 'None/Unknown',
            'UNKNOWN': 'None/Unknown',
            '': 'None/Unknown',

            # Faction -> party standardization
            'Silver': 'Republican',
            'Free Silver': 'Republican',

            'Union': 'Union Labor',

            'Crawford Republican': 'Democratic Republican',
            'Jacksonian Republican': 'Democratic Republican',
            'Adams Democrat': 'Democratic Republican',

            'Liberal Republican': 'Republican',
            'Progressive Republican': 'Republican',
            'Silver Republican': 'Republican',
            'American Labor': 'Republican',
            'Conservative Republican': 'Republican',
            'Republican-Conservative': 'Republican',

            'Anti-Lecompton Democrat': 'Democrat',
            'Democrat-Liberal': 'Democrat',
            'Liberty': 'Democrat',
            'Readjuster Democrat': 'Democrat',
            'Readjuster': 'Democrat',
            'States Rights': 'Democrat',

            'National Republican': 'Anti-Jacksonian',
            'Union Democrat': 'Jacksonian',

            'Independent Democrat': 'Independent',
            'Independent Republican': 'Independent',
            'Independent Whig': 'Independent',
            'Ind. Republican-Democrat': 'Independent',

            'Unconditional Unionist': 'Unionist',
            'Constitutional Unionist': 'Unionist',

            'Pro-Administration': 'Federalist',
            'Adams': 'Whig',
            'Anti-Jacksonian': 'Whig',
            'Jacksonian': 'Democrat',
            'Anti-Administration': 'Democratic Republican',
            'Law and Order': 'Whig',
            'Conservative': 'Union',

            # Grouping Small Parties
            'Populist': 'Other Populist/Progressive',
            'Progressive': 'Other Populist/Progressive',
            'Farmer-Labor': 'Other Populist/Progressive',
            'Greenback': 'Other Populist/Progressive',
            'Nullifier': 'Other Populist/Progressive',
            'Liberal': 'Other Populist/Progressive',

            'Anti-Masonic': 'Other Single-Issue',
            'Nullifier': 'Other Single-Issue',
            'Prohibitionist': 'Other Single-Issue',
            'American': 'Other Single-Issue',
            'Free Soil': 'Other Single-Issue',

            'Socialist': 'Other Socialist/Labor',
            'Union Labor': 'Other Socialist/Labor',
        }

        for term in terms:
            # Apply replacements repeatedly in case one replacement
            while term['party'] in replacements:
                term['party'] = replacements[term['party']]
            if term['party'] == 'Republican' and term['start'] < date(1840,1,1):
                term['party'] = 'Democratic Republican'

        return terms

    def standardize_start_date(terms):
        replacements = {
            date(1931, 12, 7): date(1931, 3, 3),
            date(1929, 4, 15): date(1929, 3, 3),
            date(1927, 12, 5): date(1927, 3, 3),
            date(1925, 12, 7): date(1925, 3, 3),
            date(1923, 12, 3): date(1923, 3, 3),
            date(1921, 4, 11): date(1921, 3, 3),
            date(1919, 5, 19): date(1919, 3, 3),
            date(1917, 4, 2): date(1917, 3, 3),
            date(1915, 12, 6): date(1915, 3, 3),
            date(1913, 4, 7): date(1913, 3, 3),
            date(1911, 4, 4): date(1911, 3, 3),
            date(1907, 12, 2): date(1907, 3, 3),
            date(1905, 12, 4): date(1905, 3, 3),
            date(1903, 11, 9): date(1903, 3, 3),
            date(1901, 12, 2): date(1901, 3, 3),
            date(1899, 12, 4): date(1899, 3, 3),
            date(1895, 12, 2): date(1895, 3, 3),
            date(1893, 8, 7): date(1893, 3, 3),
            date(1891, 12, 7): date(1891, 3, 3),
            date(1889, 12, 2): date(1889, 3, 3),
            date(1887, 12, 5): date(1887, 3, 3),
            date(1885, 12, 7): date(1885, 3, 3),
            date(1883, 12, 3): date(1883, 3, 3),
            date(1881, 12, 5): date(1881, 3, 3),
            date(1879, 4, 4): date(1879, 3, 3),
            date(1877, 10, 15): date(1877, 3, 3),
            date(1875, 12, 6): date(1875, 3, 3),
            date(1873, 12, 1): date(1873, 3, 3),
            date(1865, 12, 4): date(1865, 3, 3),
            date(1863, 12, 7): date(1863, 3, 3),
            date(1861, 7, 4): date(1861, 3, 3),
            date(1859, 12, 5): date(1859, 3, 3),
            date(1857, 12, 7): date(1857, 3, 3),
            date(1855, 12, 3): date(1855, 3, 3),
            date(1853, 12, 5): date(1853, 3, 3),
            date(1851, 12, 1): date(1851, 3, 3),
            date(1849, 12, 3): date(1849, 3, 3),
            date(1847, 12, 6): date(1847, 3, 3),
            date(1845, 12, 1): date(1845, 3, 3),
            date(1843, 12, 4): date(1843, 3, 3),
            date(1841, 5, 31): date(1841, 3, 3),
            date(1839, 12, 2): date(1839, 3, 3),
            date(1837, 9, 4): date(1837, 3, 3),
            date(1835, 12, 7): date(1835, 3, 3),
            date(1833, 12, 2): date(1833, 3, 3),
            date(1831, 12, 5): date(1831, 3, 3),
            date(1829, 12, 7): date(1829, 3, 3),
            date(1827, 12, 3): date(1827, 3, 3),
            date(1825, 12, 5): date(1825, 3, 3),
            date(1823, 12, 1): date(1823, 3, 3),
            date(1821, 12, 3): date(1821, 3, 3),
            date(1819, 12, 6): date(1819, 3, 3),
            date(1817, 12, 1): date(1817, 3, 3),
            date(1815, 12, 4): date(1815, 3, 3),
            date(1813, 5, 24): date(1813, 3, 3),
            date(1811, 11, 4): date(1811, 3, 3),
            date(1809, 5, 22): date(1809, 3, 3),
            date(1807, 10, 26): date(1807, 3, 3),
            date(1805, 12, 2): date(1805, 3, 3),
            date(1803, 10, 17): date(1803, 3, 3),
            date(1801, 12, 7): date(1801, 3, 3),
            date(1799, 12, 2): date(1799, 3, 3),
            date(1797, 5, 15): date(1797, 3, 3),
            date(1795, 12, 7): date(1795, 3, 3),
            date(1793, 12, 2): date(1793, 3, 3),
            date(1791, 10, 24): date(1791, 3, 3),
        }

        for term in terms:
            if term['start'] in replacements:
                term['start'] = replacements[term['start']]

        return terms
    
    def get_yaml(url):
        try:
            response = requests.get(url)
            response.raise_for_status()

            yaml_data = yaml.safe_load(response.text)
            return yaml_data
        except requests.exceptions.RequestException as e:
            print(f'Error getting the file {e}')
        except yaml.YAMLError as e:
            print(f'Error parsing the yaml {e}')
            
    print('Getting data...')

    l_current_yaml = get_yaml(l_current_url)
    l_historical_yaml = get_yaml(l_historical_url)
    l_yaml = l_historical_yaml + l_current_yaml 
    e_yaml = get_yaml(e_url)

    # Home page where the following urls come from:
    # https://github.com/EricWiener/supreme-court-cases
    j_url = r'https://raw.githubusercontent.com/EricWiener/supreme-court-cases/refs/heads/master/justices.js'

    response = requests.get(j_url)

    if response.status_code == 200:
        j_json = response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")

    judicials = []
    id_counter = 0
    for key, j in j_json.items():
        judicial = {
            'id': id_counter,
            'first name': j['name'].split(' ')[0],
            'last name': j['name'].split(' ')[-1],
            'gender': 'Male' if j['person']['gender'] == 'male' else 'Female',
        }

        start_date = datetime.strptime(j['start_date']['month']
                                        + str(j['start_date']['day']) 
                                        + str(j['start_date']['year']), '%b%d%Y').date()
        end_date = datetime.strptime(j['end_date']['month'] 
                                        + str(j['end_date']['day'])
                                        + str(j['end_date']['year']), '%b%d%Y').date() if j['end_date']['month'] != '' else date.today()
        switch_date = datetime.strptime('Jun' + '30'
                                        + str(j['role']['party_switch_year']), '%b%d%Y').date() if j['role']['party_switch_year'] != '' else date.fromisoformat('1700-01-01')
        
        if j['role']['party_switch_year'] == '' or switch_date <= start_date or switch_date >= end_date:    
            terms = [{
                'start': start_date,
                'end': end_date,
                'party': j['role']['start_affiliation']
                }
            ]
        else:
            terms = [{
                'start': start_date,
                'end': switch_date,
                'party': j['role']['start_affiliation']
                },
                {
                'start': switch_date + timedelta(days = 1),
                'end': end_date,
                'party': j['role']['end_affiliation']
                }
            ]

        terms = standardize_parties(terms)
        judicial['terms'] = terms
        judicials.append(judicial)
        id_counter += 1
    del j_json

    # -------------------------------------------------------------------------
    # Parse legislators and executives into structured lists
    # -------------------------------------------------------------------------

    legislators = []
    for l in l_yaml:
        legislator = {'id': l['id']['govtrack'],
                    'first name': l['name']['first'],
                    'last name': l['name']['last'],
                    'gender': 'Male' if l['bio']['gender'] == 'M' else 'Female',
                    }
        terms = [{
                    key: date.fromisoformat(value) if key in ['start', 'end'] else value
                    for key, value in term.items()
                    if key in ['type', 'start', 'state', 'end', 'party']
                }
                for term in l['terms']
            ]
        # Remove reps for territories who don't vote
        terms = [term for term in terms if term['state'] in states]
        # Add party: None/Unknown if there was no party in origianl data
        terms = [
            term if 'party' in term
            else term | {'party': 'None/Unknown'}
            for term in terms
        ]
        # Move start date from first day of opening session of congress to when they were sworn in
        terms = standardize_start_date(terms)
        terms = standardize_parties(terms)
        if len(terms) > 0:
            legislator['terms'] = terms
            legislators.append(legislator)
    del l_yaml

    executives = []
    for e in e_yaml:
        executive = {'id': e['id']['govtrack'],
                    'first name': e['name']['first'],
                    'last name': e['name']['last'],
                    'gender': 'Male' if e['bio']['gender'] == 'M' else 'Female'
                    }
        terms = [
            {
                key: date.fromisoformat(value) if key in ['start', 'end'] else value
                for key, value in term.items()
                if key in ['type', 'start', 'end', 'party']
            }
            for term in e['terms']
            ]
        terms = standardize_parties(terms)
        executive['terms'] = terms
        executives.append(executive)
    del e_yaml

    def float_date(d):
        return d.year + (d - date(d.year, 1, 1)).days / (365 + int(calendar.isleap(d.year)))

    def build_branch_df(raw_dates, columns):
        '''
        Given a list of transition dates relevant to one branch, return a
        dataframe whose rows span the resulting time buckets.  `columns` is a
        dict of {col_name: default_value} for branch-specific columns.
        '''
        transition_dates = sorted(set(d for d in raw_dates if d < date.today()))

        starts = []
        ends = []
        for i, d in enumerate(transition_dates):
            if (
                i == len(transition_dates) - 1
                or transition_dates[i + 1] > d + timedelta(days=20)
            ):
                starts.append(d)
                if i != len(transition_dates) - 1:
                    ends.append(transition_dates[i + 1])
                else:
                    ends.append(date.today())

        ends = [end - timedelta(days=1) if end != date.today() else end for end in ends]

        df_len = len(starts)
        df = pd.DataFrame({'start': starts, 'end': ends} |
                          {col: [default() if callable(default) else default
                                 for _ in range(df_len)]
                           for col, default in columns.items()})

        df['start float'] = df['start'].apply(float_date)
        df['end float'] = df['start float'].shift(-1)
        df.at[len(df) - 1, 'end float'] = float_date(date.today())

        return df

    def count_attr(dicts, attr):
        counts = {}
        for d in dicts:
            this_attr = d[attr]
            counts[this_attr] = counts.get(this_attr, 0) + 1
        return counts

    senate_dates = []
    for legislator in legislators:
        for term in legislator['terms']:
            if term['type'] == 'sen':
                senate_dates += [term['start'], term['end']]

    senate_df = build_branch_df(senate_dates, {'senate': list})

    for legislator in legislators:
        for term in legislator['terms']:
            if term['type'] != 'sen':
                continue
            mask = (
                (senate_df['start'] >= term['start']) &
                (senate_df['end'] <= term['end'])
            )
            to_add = {key: value for key, value in legislator.items() if key != 'terms'} | term
            senate_df.loc[mask, 'senate'] = senate_df.loc[mask, 'senate'].apply(lambda x: x + [to_add])

    senate_df['senate size'] = senate_df['senate'].apply(len)
    senate_df['senate by party'] = senate_df['senate'].apply(lambda x: count_attr(x, 'party'))
    senate_df['senate by gender'] = senate_df['senate'].apply(lambda x: count_attr(x, 'gender'))

    house_dates = []
    for legislator in legislators:
        for term in legislator['terms']:
            if term['type'] == 'rep':
                house_dates += [term['start'], term['end']]

    house_df = build_branch_df(house_dates, {'house': list})

    for legislator in legislators:
        for term in legislator['terms']:
            if term['type'] != 'rep':
                continue
            mask = (
                (house_df['start'] >= term['start']) &
                (house_df['end'] <= term['end'])
            )
            to_add = {key: value for key, value in legislator.items() if key != 'terms'} | term
            house_df.loc[mask, 'house'] = house_df.loc[mask, 'house'].apply(lambda x: x + [to_add])

    house_df['house size'] = house_df['house'].apply(len)
    house_df['house by party'] = house_df['house'].apply(lambda x: count_attr(x, 'party'))
    house_df['house by gender'] = house_df['house'].apply(lambda x: count_attr(x, 'gender'))

    court_dates = []
    for judicial in judicials:
        for term in judicial['terms']:
            court_dates += [term['start'], term['end']]

    court_df = build_branch_df(court_dates, {'court': list})

    for judicial in judicials:
        for term in judicial['terms']:
            mask = (
                (court_df['start'] >= term['start']) &
                (court_df['end'] <= term['end'])
            )
            to_add = {key: value for key, value in judicial.items() if key != 'terms'} | term
            court_df.loc[mask, 'court'] = court_df.loc[mask, 'court'].apply(lambda x: x + [to_add])

    # Fill vacant court periods
    for index, row in court_df.iterrows():
        if row['court'] == []:
            court_df.at[index, 'court'] = [{
                'id': 0,
                'first name': 'Vacant',
                'last name': '',
                'gender': 'Vacant',
                'start': row['start'],
                'end': row['end'],
                'party': 'Vacant'
            }]

    court_df['court size'] = court_df['court'].apply(len)
    court_df['court by party'] = court_df['court'].apply(lambda x: count_attr(x, 'party'))
    court_df['court by gender'] = court_df['court'].apply(lambda x: count_attr(x, 'gender'))

    exec_dates = []
    for executive in executives:
        for term in executive['terms']:
            exec_dates += [term['start'], term['end']]

    exec_df = build_branch_df(exec_dates, {'prez': '', 'vice prez': ''})

    for executive in executives:
        for term in executive['terms']:
            if term['type'] == 'prez':
                exec_type = 'prez'
            elif term['type'] == 'viceprez':
                exec_type = 'vice prez'
            else:
                raise ValueError(f"Unexpected exec_type: {term['type']}")
            mask = (
                (exec_df['start'] >= term['start']) &
                (exec_df['end'] <= term['end'])
            )
            to_add = {key: value for key, value in executive.items() if key != 'terms'} | term
            exec_df.loc[mask, exec_type] = [to_add] * mask.sum()

    # Fill vacant executive periods
    for index, row in exec_df.iterrows():
        for exec_type in ['prez', 'vice prez']:
            if row[exec_type] == '':
                exec_df.at[index, exec_type] = {
                    'id': 0,
                    'first name': 'Vacant',
                    'last name': '',
                    'gender': 'Vacant',
                    'type': exec_type,
                    'start': row['start'],
                    'end': row['end'],
                    'party': 'Vacant'
                }

    # -------------------------------------------------------------------------
    # Save to pickle
    # -------------------------------------------------------------------------

    files = [f for f in os.listdir('.') if os.path.isfile(os.path.join('.', f)) and f.startswith('saved_data_') and f.endswith('.pkl')]
    for file in files:
        os.remove(file)

    with open(pickle_filepath, 'wb') as file:
        pickle.dump((senate_df, house_df, court_df, exec_df), file)

