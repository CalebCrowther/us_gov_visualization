import plotly.graph_objects as go
import plotly
from datetime import date
import os
import pickle
from pathlib import Path
import sys
import colorsys
import random

today = str(date.today())

current_dir = os.getcwd()
pickle_file = 'saved_data_' + today + '.pkl'

pickle_filepath = Path(current_dir + '/' + pickle_file)
if pickle_filepath.is_file():
    with open(pickle_filepath, 'rb') as file:
        senate_df, house_df, court_df, exec_df = pickle.load(file)
else:
    print('Update the Pickle File by running parse_data.py before continuing')
    sys.exit()

# all_parties = set([])
# for index, row in by_date_df.iterrows():
#     for party in row['house parties']:
#         all_parties.add(party)
#     for party in row['senate parties']:
#         all_parties.add(party)
#     for party in row['court parties']:
#         all_parties.add(party)
#     all_parties.add(row['prez']['party'])
#     all_parties.add(row['vice prez']['party'])

# Get colors from cat_to_color onto the figure legend
def initialize_default_colors(cat_to_color, fig):
    for cat, color in cat_to_color.items():
        fig.add_trace(go.Scatter(
            x=[0],
            y=[0],
            fill="toself",
            mode = 'none',
            fillcolor = color,
            name=cat,
            showlegend=True,
        ))

# Helper fucntion for add_color
def color_distance_hsv(c1, c2):

    # Turn hex strings into tuples
    c1 = tuple(int(c1.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    c2 = tuple(int(c2.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))

    hsv1 = colorsys.rgb_to_hsv(*c1)
    hsv2 = colorsys.rgb_to_hsv(*c2)
    
    # Weight Hue heavily since it alters human perception the most
    dh = min(abs(hsv1[0] - hsv2[0]), 1 - abs(hsv1[0] - hsv2[0]))
    ds = hsv1[1] - hsv2[1]
    dv = hsv1[2] - hsv2[2]
    
    return (dh ** 2) * 4 + (ds ** 2) + (dv ** 2)

# To add a new color if a new key appears that wasn't accounted for
def add_color(cat_to_color, fig, new_cat):

    current_colors = [value for key, value in cat_to_color.items()]

    r = lambda: random.randint(0,255)
    best_min = 0
    new_color = '#777777'
    for i in range(1000):
        new_option = '#%02X%02X%02X' % (r(),r(),r())
        min_distance = min([color_distance_hsv(new_option, current_color) for current_color in current_colors])
        if min_distance > best_min:
            best_min = min_distance
            new_color = new_option

    fig.add_trace(go.Scatter(
        x=[0],
        y=[0],
        fill="toself",
        mode = 'none',
        fillcolor = new_color,
        name=new_cat,
        showlegend=True,
    ))
    cat_to_color[new_cat] = new_color
    return cat_to_color

# Add a new rectangle to the plot
def add_rectangle(fig, x0, x1, y0, y1, label, category, cat_to_color):

    if category not in cat_to_color:
        cat_to_color = add_color(cat_to_color, fig, category)

    fig.add_trace(go.Scatter(
        x=[x0,x1,x1,x0,x0],
        y=[y0,y0,y1,y1,y0],
        fill="toself",
        fillcolor= cat_to_color[category],
        mode="none",
        name=label,
        showlegend=False,
        hovertemplate=label + "<extra></extra>"
    ))

formatted_group = {'house': 'House of Representatives', 'senate': 'Senate', 'court': 'Supreme Court'}

def add_timeline(group_name, y_offset, fig, cat_to_color, cat_type, df):
    for x in [1795, 1895, 1995]:
        fig.add_annotation(
            x=x,                             
            y=y_offset + 1.17,    
            text=formatted_group[group_name], 
            xanchor = 'left',
            showarrow=False,       
            arrowhead=2,    
            font=dict(size=14, color="black") 
        )

    for index, row in df.iterrows():
        parties = row[f'{group_name} by {cat_type}']
        total = row[f'{group_name} size']
        start = row['start float']
        end = row['end float']
        y_so_far = 0
        for party, count in sorted(parties.items()):
            y0 = y_so_far/total + y_offset
            y_so_far += count
            y1 = y_so_far/total + y_offset
            label = f"{party}<br>{row['start']} - {row['end']}"
            num_added = 0
            for rep in row[group_name]:
                if rep[cat_type] == party:
                    if group_name == 'court':
                        label += f"<br>{rep['first name']} {rep['last name']}"
                    else:
                        label += f"<br>{rep['first name']} {rep['last name']} ({rep['state']})"
                    num_added += 1
                    if num_added >= 5:
                        label += "<br>..."
                        break
            add_rectangle(fig, start, end, y0, y1, label, party, cat_to_color)

    fig.add_trace(
        go.Scatter(
            x=[min(list(df['start float'])), max(list(df['end float']))],
            y=[0.5 + y_offset, 0.5 + y_offset],
            mode='lines', 
            line=dict(dash='dot', width=1, color='black'),
            showlegend=False,
            hoverinfo="skip",
        )
    )

def add_execs_timeline(y_offset, fig, cat_to_color, cat_type, df):
    for x in [1795, 1895, 1995]:
        fig.add_annotation(
            x=x,                             
            y=y_offset + 1.17,    
            text="Presidency", 
            xanchor = 'left',
            showarrow=False,       
            arrowhead=2,    
            font=dict(size=14, color="black") 
        )
    for index, row in df.iterrows():
        prez = row['prez']
        vice_prez = row['vice prez']
        prez_party = prez[cat_type]
        vice_prez_party = vice_prez[cat_type]
        start = row['start float']
        end = row['end float']
        prez_label = f"President: {prez['first name']} {prez['last name']}<br>{row['start']} - {row['end']}<br>{prez_party}"
        vice_prez_label = f"Vice President: {vice_prez['first name']} {vice_prez['last name']}<br>{row['start']} - {row['end']}<br>{vice_prez_party}"
        add_rectangle(fig, start, end, y_offset+0.5, y_offset+1, prez_label, prez_party, cat_to_color)
        add_rectangle(fig, start, end, y_offset, y_offset+0.5, vice_prez_label, vice_prez_party, cat_to_color)

cat_to_color_dict = {
    'party':
        {
            'Democrat': '#1f77b4',
            'Republican': '#d62728',
            'Independent': "#646417",
            'Libertarian': '#f2c300',
            'Federalist': '#9467bd',
            'Democratic Republican': '#2ca02c',
            'Whig': '#ff7f0e',
            'Unionist': '#53cbf0',
            'Vacant': '#111111',
            'None/Unknown': '#777777',
            'Other Socialist/Labor': "#250a83",
            'Other Populist/Progressive': '#e425ce',
            'Other Single-Issue': "#733b3b",
        },
    'gender':
        {
            'Female': "#d445dc",
            'Male': "#1e32c7",
            'Vacant': '#111111',
        }
}

for attr in ['party', 'gender']:

    fig = go.Figure()
    
    cat_to_color = cat_to_color_dict[attr]
    initialize_default_colors(cat_to_color, fig)

    # Add house, senate, supreme court information:
    add_timeline('court', 0, fig, cat_to_color, attr, court_df)
    add_timeline('house', 1.5, fig, cat_to_color, attr, house_df)
    add_timeline('senate', 3, fig, cat_to_color, attr, senate_df)
    # Add presidency information
    add_execs_timeline(4.5, fig, cat_to_color, attr, exec_df)

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        yaxis=dict(
            showticklabels=False,
            range=[-0.2, 5.9],
            fixedrange=True,
        ),
        xaxis=dict(
            range=[1784, date.today().year+7],
            minallowed = 1784,
            maxallowed = date.today().year+7
        ),
    )

    fig.write_html(f"{attr}_plot.html")
