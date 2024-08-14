from fasthtml_hf import setup_hf_backup
from fasthtml.common import *
from fasthtml import FastHTML
from starlette.testclient import TestClient
from typing import List
import lancedb
from lancedb.pydantic import LanceModel, Vector
from lancedb.embeddings import get_registry
import pandas as pd
import numpy as np
import re
import string
from dotenv import load_dotenv
import os
from starlette.responses import FileResponse

headers = (Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@400;700&display=swap"))

filter_entities = [
    "human",
    "Act of Congress in the United States",
    "government agency",
    "academic discipline",
    "United States federal agency",
    "position",
    "sovereign state",
    "aspect in a geographic region",
    "country",
    "business",
    "industry",
    "specialty",
    "concept",
    "independent agency of the United States government",
    "nonprofit organization",
    "public company",
    "organization",
    "U.S. state",
    "profession",
    "economic concept",
    "government program",
    "legal concept",
    "geographic region",
    "federal law enforcement agency of the United States",
    "field of study",
    "big city",
    "bilateral relation",
    "type of policy",
    "city in the United States",
    "occupation",
    "political ideology",
    "social movement",
    "legislation",
    "activity",
    "economic activity",
    "academic major",
    "statute",
    "class of disease",
    "enterprise",
    "United States federal executive department",
    "county seat",
    "national economy",
    "weapon functional class",
    "branch of science",
    "intergovernmental organization",
    "legal form",
    "area of law",
    "international organization",
    "type of technology",
    "symptom or sign",
    "form of government",
    "legal case",
    "United States Supreme Court decision",
    "chemical element",
    "think tank",
    "political movement",
    "financial regulatory agency",
    "type of management",
    "type of security",
    "republic",
    "research institute",
    "island country",
    "Mediterranean country",
    "term",
    "presidential term",
    "terrorist organization",
    "city",
    "political concept",
    "political party",
    "historical period",
    "United States executive order",
    "taxon",
    "failure mode",
    "OECD country",
    "political system",
    "process",
    "corporate title",
    "economics term",
    "intelligence agency",
    "type of organisation",
    "group of humans",
    "aspect of history",
    "events in a specific year or time period",
    "public office",
    "scientific journal",
    "field of work",
    "armed organization",
    "website",
    "lithophile",
    "open-access publisher",
    "crime",
    "federal republic",
    "bill",
    "type of chemical entity",
    "legislative branch agency",
    "ideology",
    "unitary state",
    "policy",
    "social networking service",
    "specialized agency of the United Nations",
    "treaty",
    "human activity",
    "advisory board",
    "technical sciences",
    "continent",
    "economic sector",
    "airline",
    "type of regulation and control",
    "very large online platform",
    "technology company",
    "manner of death",
    "federation",
    "form of state",
    "weapon model",
    "company",
    "tourist attraction",
    "secular state",
    "technique",
    "institution",
    "political buzzword",
    "constitutional republic",
    "publisher",
    "phrase",
    "type of process",
    "online community",
    "specialist law enforcement agency",
    "war",
    "organization established by the United Nations",
]

css = Style('''

    html {
        prefers-color-scheme: light;
        --pico-prefers-color-scheme: light;
    }

    :root {
        --pico-font-size: 90%;
        --pico-font-family: IBM Plex Serif, serif;
    }

    body {
        background-color: var(--primary-bg-color);
        color: var(--primary-text-color);
    }

    ul li {
        list-style: none;
        padding: 0;
    }

    ul {
        padding: 0;
    }

    H1 {
        text-align: center;
        color: var(--primary-text-color);
        margin-bottom: 30px;
    }

    Img {
        display: block;
        margin: 0 auto;
        max-width: 50%;
        height: auto;
    }

    Form {
        margin-bottom: 10px;
    }

    Figure {
        margin-bottom: 30px;
    }

    Figcaption {
        text-align: center;
        font-size: 0.80rem;
        color: #888;
        margin-top: 5px;
    }

    .tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
    }

    .tooltip .tooltiptext {
        font-size: 90%;
        visibility: hidden;
        width: 300px;
        background-color: var(--tooltip-bg-color, rgba(0, 0, 0, 0.8)); /* Fallback for dark background */
        color: var(--tooltip-text-color, #fff); /* Fallback for light text color */
        text-align: left;
        border-radius: 5px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        white-space: normal;
        word-wrap: break-word;
        opacity: 0;
        transition: opacity 0.05s;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); /* Add a subtle shadow for better readability */
    }

    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }

    @media (prefers-color-scheme: dark) {
        .tooltip .tooltiptext {
            background-color: rgba(255, 255, 255, 0.9); /* Light background for dark mode */
            color: #000; /* Dark text color for light background */
        }
    }

    @media (prefers-color-scheme: light) {
        .tooltip .tooltiptext {
            background-color: rgba(0, 0, 0, 0.8); /* Dark background for light mode */
            color: #fff; /* Light text color for dark background */
        }
    }

    .wikipedia-link {
        color: var(--link-color, inherit) !important;
        text-decoration: none !important;
    }

    .non-wikipedia-link {
        color: var(--secondary-text-color);
    }
    .indexnav-container {
        text-align: center;
    }

    .indexnav-container a {
        display: inline-block;
        margin: 0 5px;
        text-decoration: none;
    }

    .indexnav-container a:hover {
        text-decoration: underline;
    }

    .indexnav-container span {
        display: inline-block;
        width: 5px;  /* Adjust this width as needed */
    }

    .page-links-container {
        text-align: left; /* Align to left, or center if you prefer */
    }

    .unit {
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 10px;
    }

    .page-links-container a {
        display: inline-block;
        margin: 0 5px;
        text-decoration: none;
    }

    .page-links-container a:hover {
        text-decoration: underline;
    }

    .page-links-container span {
        display: inline-block;
        width: 5px;  /* Adjust the spacing as necessary */
    }

    .search_form {
        display: flex;
        width: 100%;
    }

    .search_type {
        width: 50%;
        display: inline-block;
        vertical-align: top;
        margin-left: 10px
    }

    .search {
        width: 50%;
        display: inline-block;
        vertical-align: top;
        margin-right: 5px;
    }
''')

app = FastHTML(hdrs=(picolink, css, headers))

def group_by_page(df):
    """
    Groups the DataFrame by 'title' and aggregates 'page' and 'summary' into lists.
    Additionally, merges the result with 'title_index' and 'instance_of' columns from
    the original DataFrame.
    """
    if isinstance(df['instance_of'].iloc[0], (list, np.ndarray)):
        df['instance_of'] = df['instance_of'].apply(tuple)
    aggregated_data = df.groupby('title', as_index=False).agg({
        'page': list,
        'summary': list
    })
    merge_columns = df[['title', 'title_index', 'instance_of', 'wikipedia_url']].drop_duplicates()
    result = pd.merge(aggregated_data, merge_columns, on='title', how='left')
    return result

def custom_sort_key(title):
    if title[0].isdigit():
        return (1, title.lower())  # Numbers come after letters
    else:
        return (0, title.lower())  # Letters come first

def alphabetical_limit(df, letter):
    """
    Filters dataframe by titles beginning with a letter from the alphabet or number.
    """
    if letter == "num":
        filtered_table = df[df['title'].str.match(r'^\d')]
    else:
        filtered_table = df[df['title'].str.lower().str.startswith(letter.lower())]
    return filtered_table.sort_values(by='title', key=lambda col: col.map(custom_sort_key))

def alphabetical_sort_table(df):
    """
    Sorts dataframe rows by title in alphabetical order.
    """
    return df.sort_values(by='title', key=lambda col: col.map(custom_sort_key))

def df_to_html(df, include_spacing):
    """
    Generate HTML section for dataframe of index items.
    """
    return Ul(*[
        Div(
            Br() if include_spacing and previous_page is not None and row['page'] != previous_page else None,
            Li(
                A(
                    f"{row['title']}",
                    href=row['wikipedia_url'],
                    target="_blank",
                    _class="wikipedia-link",
                    style="color: var(--link-color, inherit) !important; text-decoration: none"
                ) if row['wikipedia_url'] else Span(f"{row['title']}", _class="non-wikipedia-link"),
                Span(" ", style="display:inline-block; width:5px;"),
                *create_page_links(row['page'], row['summary'])
            )
        )
        for previous_page, (_, row) in zip([None] + df['page'].tolist(), df.iterrows())
    ])

# Connect to LanceDB and load data
db = lancedb.connect(".lancedb")
table = db.open_table("entities")
table.search('test', vector_column_name="title_vector")
lancepd = table.to_pandas()
grouped_lancepd = group_by_page(lancepd)
index_table = alphabetical_limit(grouped_lancepd, 'a')

# Map pages to sections in the document:
section_pages = lancepd.groupby('section')['page'].agg(['min', 'max']).reset_index()
section_pages = section_pages.sort_values('min')
section_page_dict = section_pages.set_index('section').T.to_dict()

@app.get("/assets/{fname:path}.{ext:static}")
async def serve_image(fname: str, ext: str):
    return FileResponse(f'assets/{fname}.{ext}')

@app.get("/")
def home():
    """
    Load entire index page for first time.
    """
    print("New session generating")
    return Title("Project 2025 Index"), Main(
            Div(
                H1('Project 2025 Index'),
                Figure(
                            Img(src="/assets/badge.jpg", alt="Project 2025 Badge"),
                            Figcaption(
                                'Image by ',
                                A('DonkeyHotey', href='https://www.flickr.com/photos/donkeyhotey/53792367625', target="_blank"),
                            ),
                        ),
                Div(P(A('Project 2025', href=f'https://www.project2025.org/', target="_blank"), f"""is a controversial plan developed by the Heritage Foundation think-tank that
                    outlines a policy framework for a future conservative US president.
                    The 900-page publication lacks an index, so we created one to provide researchers with another approach to navigating the contents of the document."""),
                    P("""The index includes some useful filters and summaries to aid researchers in exploring the large number of items within Project 2025. Hover over each page number to view a summary of how the item is discussed on the page, and click the page link to view the source document.
                    Explore specific groups of items by sorting, filtering and searching the index via the interactive forms. More information on each form can be accessed by hovering over the ⓘ symbols."""),
                    P(f"""This project was developed by the""",
                    A('Autonomy Institute', href=f'https://autonomy.work/', target="_blank"),f"""
                    501(c)(3) and is maintained on""",
                    A('Github', href=f'https://github.com/Autonomy-Data-Unit/project-2025-index', target="_blank"),
                    f"""where contributions are welcome.
                    """),),
                cls = "unit"
            ),
            Div(
                Form(
                    Div(
                        Span("Sort"),
                        Span("ⓘ", cls="tooltip")(
                            Span("Items can be sorted alphabetically, by page number, or by semantic similarity (vector). Sorting by semantic similarity arranges items with related subject matter closer together in the list.", cls="tooltiptext")
                        ),
                    ),
                    Select(
                        Option("None", value="none", selected=False),
                        Option("Alphabetical", value="alphabetical", selected=True),
                        Option("Page Number", value="page", selected=False),
                        Option("Vector", value="vector", selected=False),
                        name="sort_type",
                        id="sort_form",
                        hx_post="/sort", hx_target="#index-data", hx_swap="innerHTML", hx_swap_oob='true'
                    ),
                ),
                Form(
                    Div(
                        Span("Filter"),
                        Span("ⓘ", cls="tooltip")(
                            Span("Items in the index that share titles with Wikipedia pages can be filtered based on the 'instance of' metadata from those Wikipedia pages.", cls="tooltiptext")
                        ),
                    ),
                    Select(
                        Option("None", value="None", selected=True), *[Option(entity, value=entity, selected=False) for entity in filter_entities],
                        name="filter_type",
                        id="filter_form",
                        hx_post="/filter", hx_target="#index-data", hx_swap="innerHTML", hx_swap_oob='true'
                    ),
                ),
                Form(
                    Div(
                        Div(Span("Search"),  # Add text next to the search input
                        ),
                        Input(placeholder="Search the document", type= "search",name="query", id="searchbar", hx_swap_oob='true'),
                        cls="search"
                    ),
                    Div(
                        Div(
                        Span("Search Type"),  # Add text next to the select input
                        Span("ⓘ", cls="tooltip")(
                            Span("Searching by 'Title' will find items with titles closest to your query, while searching by 'Context' will locate summaries in the tooltips that are most relevant to your query.", cls="tooltiptext")
                        ),
                        ),
                        Select(
                            Option("Title", value="title_vector", selected=True),
                            Option("Context", value="summary_vector", selected=False),
                            name="search_type",
                            id="search_type_form",
                            hx_swap_oob='true'
                        ),
                        cls="search_type"
                    ),
                    id = "search_box",
                    cls = "search_form",
                    hx_post="/search", hx_target="#index-data", hx_swap="innerHTML"
                ),
            cls = "unit",
            ),
            Div(
            H2('Index'),
            Div(
                Hr(),
                H3(*(
                    (A(f"{letter if letter != 'num' else '#'}", id=f"{letter}", hx_post=f"/letter_sort?letter={letter}" if letter != "num" else f"/letter_sort?letter=num", hx_target="#index-data", hx_swap="innerHTML", hx_swap_oob='true'),
                     Span("", style="display:inline-block; width:5px;"))
                    for letter in [item for item in string.ascii_uppercase] + ['num']
                ), _class="indexnav-container"),
                Hr(),
                id="indexnav",
                name="indexnavigator", hx_swap="innerHTML", hx_swap_oob='true'
            ),
                Div(df_to_html(index_table, False), id='index-data'),
                cls = "unit",
            ),
            cls="container"
    )

def reset_search_input():
    """
    Rearch search bar input to placeholder.
    """
    return Input(placeholder="Search the document", type= "search",name="query", id="searchbar", hx_swap_oob='true')

def reset_search_type():
    """
    Rearch search type selector form.
    """
    return Select(
        Option("Title", value="title_vector", selected="title_vector"),
        Option("Context", value="summary_vector"),
        name="search_type",
        id="search_type_form",
        hx_swap_oob='true'
    )

def remove_nav():
    """
    Remove the index navigator from above the index items.
    """
    return Div(Hr(),id="indexnav",name="indexnavigator",hx_swap="innerHTML", hx_swap_oob='true')

@app.post("/sort")
def sort_table(sort_type:str):
    """
    Sort and render the index. Also updates other components.
    """
    if sort_type == 'alphabetical' or sort_type == 'none':
        new_table = alphabetical_limit(grouped_lancepd, 'a')
        table_html = df_to_html(new_table, False)
        return table_html,render_alphanav(), reset_search_input(), reset_search_type(), reset_filter()
    elif sort_type == 'page':
        data = table.to_pandas()
        data = data[(data['page'] >= 1) & (data['page'] <= 17)]
        data['summary'] = data['summary'].apply(lambda x: [x])
        data['page'] = data['page'].apply(lambda x: [x])
        new_table = data
        table_html = df_to_html(new_table, True)
        return table_html,render_pagenav(), reset_search_input(), reset_search_type(), reset_filter()
    elif sort_type == 'vector':
        new_table = alphabetical_sort_table(grouped_lancepd).sort_values(by='title_index')
        table_html = df_to_html(new_table, False)
        return table_html, remove_nav(), reset_search_input(), reset_search_type(), reset_filter()

def render_alphanav():
    """
    Render the index navigator for filtering items by letter of the alphabet.
    """
    return Div(
        Hr(),
        H3(*(
            (A(f"{letter if letter != 'num' else '#'}", id=f"{letter}", hx_post=f"/letter_sort?letter={letter}" if letter != "num" else f"/letter_sort?letter=num", hx_target="#index-data", hx_swap="innerHTML", hx_swap_oob='true'),
             Span("", style="display:inline-block; width:5px;"))
            for letter in [item for item in string.ascii_uppercase] + ['num']
        ), _class="indexnav-container"),
        Hr(),
        id="indexnav",
        name="indexnavigator", hx_swap="innerHTML", hx_swap_oob='true'
    )

def render_pagenav():
    """
    Render the index navigator for filtering items by page range.
    """
    return Div(
        Hr(),
        P(*(
            (A(f"{section_page_dict[item]['min']}-{section_page_dict[item]['max']}", hx_post=f"/page_sort?page={section_page_dict[item]['min']}-{section_page_dict[item]['max']}", hx_target="#index-data", hx_swap="innerHTML", hx_swap_oob='true'), Span(" ", style="display:inline-block; width:10px;"))
                        for i,item in enumerate(section_page_dict)
                    )),
        Hr(),
        id="indexnav",
        name="indexnavigator", hx_swap="innerHTML", hx_swap_oob='true'
    )

def create_page_links(pages: list, summaries: list):
    """
    For a single entity, converts a list of page numbers and list of summary strings
    into a list of page links (of type list)
    """
    page_summary_map = {page: summaries[i] for i, page in enumerate(pages)}
    sorted_pages = sorted(page_summary_map.keys())
    links = [
        Div(
            A(str(page), href=f'https://www.documentcloud.org/documents/24088042-project-2025s-mandate-for-leadership-the-conservative-promise#document/p{page+32}', target="_blank"),
            Div(page_summary_map[page], cls="tooltiptext"),
            cls="tooltip"
        )
        for page in sorted_pages
    ]
    return [
        element for link in links for element in (link, Span(", ", _class="page-links-container"))
    ][:-1]

def refresh_table():
    """
    Reload initial index table.
    """
    return df_to_html(index_table, False)

def reset_sort():
    """
    Reset the sort form elements to initial state.
    """
    return Select(
        Option("None", value="none", selected=True),
        Option("Alphabetical", value="alphabetical"),
        Option("Page Number", value="page"),
        Option("Vector", value="vector"),
        name="sort_type",
        id="sort_form",
        hx_post="/sort", hx_target="#index-data", hx_swap="innerHTML", hx_swap_oob='true'
    )

def reset_filter():
    """
    Reset the filter form element to initial state.
    """
    return Select(
        Option("None", value="None", selected=True), *[Option(entity, value=entity) for entity in filter_entities],
        name="filter_type",
        id="filter_form",
        hx_post="/filter", hx_target="#index-data", hx_swap="innerHTML", hx_swap_oob='true'
    )

@app.post("/letter_sort")
async def print_letter(request: Request, letter: str = None):
    """
    Get index items by letter of the alphabet.
    """
    letter = letter or request.query_params.get('letter')
    new_table = alphabetical_limit(grouped_lancepd, str(letter))
    return df_to_html(new_table, False)

@app.post("/page_sort")
async def print_page(request: Request, page: str= None):
    """
    Get index items by page range from the document.
    """
    page_range = page or request.query_params.get('page')
    p_min, p_max = page_range.split('-')[0],page_range.split('-')[1]
    data = lancepd
    subset = data.loc[(data['page'] >= int(p_min)) & (data['page'] <= int(p_max))].copy()
    subset['page'] = subset['page'].astype(object)  # Convert to object type first
    subset.loc[:, 'summary'] = subset['summary'].apply(lambda x: [x])
    subset.loc[:, 'page'] = subset['page'].apply(lambda x: [x])
    return df_to_html(subset, True)

@app.post("/search")
def vector_search(query:str, search_type:str):
    """
    Search LanceDB by string.
    """
    if not query:
        return render_alphanav(), refresh_table()
    if search_type == "title_vector":
        vector_column_name="title_vector"
    elif search_type == "summary_vector":
        vector_column_name="summary_vector"
    results = table.search(query, vector_column_name=vector_column_name).limit(50).to_pandas()
    if search_type == "title_vector":
        data = results.groupby('title', sort=False).agg({
            'page': list,
            'summary': list  # Create a list of summaries corresponding to each page
        }).reset_index()
        if isinstance(results['instance_of'].iloc[0], (list, np.ndarray)):
            results['instance_of'] = results['instance_of'].apply(tuple)
        merge_columns = results[['title', 'title_index', 'instance_of', 'wikipedia_url']].drop_duplicates()
        result = pd.merge(data, merge_columns, on='title', how='left')
    elif search_type == "summary_vector":
        data = results
        data['summary'] = data['summary'].apply(lambda x: [x])
        data['page'] = data['page'].apply(lambda x: [x])
        result = data
    return df_to_html(result, False), reset_filter(), reset_sort(), remove_nav()

@app.post("/filter")
def filter_table(filter_type: str):
    """
    Filter table by Wikidata instance_of item.
    """
    if filter_type == "None":
        new_table = alphabetical_sort_table(grouped_lancepd)
    else:
        new_table = alphabetical_sort_table(grouped_lancepd)[alphabetical_sort_table(grouped_lancepd)['instance_of'].apply(lambda x: filter_type in x)]
    return df_to_html(new_table, False), reset_sort(), reset_search_input(), reset_search_type(), remove_nav()

serve()
