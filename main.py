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


# load_dotenv()  # Load environment variables from .env file

# hf_token = os.getenv("HF_TOKEN")

headers = (Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:wght@400;700&display=swap"))


filter_entities = [
    "human",
    "Act of Congress in the United States",
    "government agency",
    # "Wikimedia disambiguation page",
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
    # "Wikimedia human name disambiguation page",
    "financial regulatory agency",
    "type of management",
    "type of security",
    "republic",
    "research institute",
    "island country",
    "Mediterranean country",
    "term",
    # "Wikimedia list article",
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

    html {prefers-color-scheme: light; --pico-prefers-color-scheme: light;}
    :root { --pico-font-size: 90%; --pico-font-family: IBM Plex Serif, serif;}

    body {
        background-color: var(--primary-bg-color);
        color: var(--primary-text-color);
    }

    ul li { list-style: none; padding: 0; }
    ul { padding: 0; }

    H1 {
        text-align: center;
        color: var(--primary-text-color);
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
        color: var(--link-color);
        text-decoration: none;
    }

    .non-wikipedia-link {
        color: var(--secondary-text-color);
    }
    .alphanav-container {
        text-align: center;
    }

    .alphanav-container a {
        display: inline-block;
        margin: 0 5px;
        text-decoration: none;
    }

    .alphanav-container a:hover {
        text-decoration: underline;
    }

    .alphanav-container span {
        display: inline-block;
        width: 5px;  /* Adjust this width as needed */
    }

    .page-links-container {
        text-align: left; /* Align to left, or center if you prefer */
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

''')

app = FastHTML(hdrs=(picolink, css, headers))


# Load data

def group_by_page(df):
    """
    Groups the DataFrame by 'title' and aggregates 'page' and 'summary' into lists.
    Additionally, merges the result with 'title_index' and 'instance_of' columns from
    the original DataFrame.
    """
    print("called group_by_page")
    # Efficiently convert 'instance_of' column to tuples if needed
    if isinstance(df['instance_of'].iloc[0], (list, np.ndarray)):
        df['instance_of'] = df['instance_of'].apply(tuple)
    # Group by 'title' while aggregating 'page' and 'summary' into lists
    aggregated_data = df.groupby('title', as_index=False).agg({
        'page': list,
        'summary': list
    })
    # Extract relevant columns for merging, ensuring no duplicates
    merge_columns = df[['title', 'title_index', 'instance_of', 'wikipedia_url']].drop_duplicates()
    # Merge the grouped data with the additional columns from the original DataFrame
    result = pd.merge(aggregated_data, merge_columns, on='title', how='left')
    return result

def custom_sort_key(title):
    # print("called custom_sort_key")

    # Check if the first character is a digit
    if title[0].isdigit():
        return (1, title.lower())  # Numbers come after letters
    else:
        return (0, title.lower())  # Letters come first

def alphabetical_limit(table, letter):
    print("called alphabetical_limit")
    if letter == "num":
        # Filter the DataFrame to only include titles that start with a number
        filtered_table = table[table['title'].str.match(r'^\d')]
    else:
        # Filter the DataFrame to only include titles that start with the specified letter
        filtered_table = table[table['title'].str.lower().str.startswith(letter.lower())]

    return filtered_table.sort_values(by='title', key=lambda col: col.map(custom_sort_key))

def alphabetical_sort_table(table):
    print("called alphabetical_sort_table")
    return table.sort_values(by='title', key=lambda col: col.map(custom_sort_key))

# load data
db = lancedb.connect("./.lancedb")
table = db.open_table("entities")

# run first search
table.search('test', vector_column_name="title_vector")

# initial state
search_by = "title_vector"
sort_by = "alphabetical"
previous_initial = None
filter_by = "none"
search_mode = False
previous_page = None
alphanav = True
pagenav = False

def render():
    global index_table
    return Ul(*[
        Div(
            create_letter_space(row['title'], row['page'][0]),
            Li(
                A(
                    f"{row['title']}",
                    href=row['wikipedia_url'],
                    target="_blank",
                    _class="wikipedia-link"
                ) if row['wikipedia_url'] else Span(f"{row['title']}", _class="non-wikipedia-link"),
                Span(" ", style="display:inline-block; width:5px;"),
                *create_page_links(row['page'], row['summary'])
            )
        )
        if (sort_by == "alphabetical" and filter_by == "none") or sort_by == "page" else Li(
            A(
                f"{row['title']}",
                href=row['wikipedia_url'],
                target="_blank",
                _class="wikipedia-link"
            ) if row['wikipedia_url'] else Span(f"{row['title']}", _class="non-wikipedia-link"),
            Span(" ", style="display:inline-block; width:5px;"),
            *create_page_links(row['page'], row['summary'])
        )
        for _, row in index_table.iterrows()
    ])

lancepd = table.to_pandas()
grouped_lancepd = group_by_page(lancepd)
index_table = alphabetical_limit(grouped_lancepd, 'a')

# build section map:
section_pages = lancepd.groupby('section')['page'].agg(['min', 'max']).reset_index()

# Sort by the 'min' column to order by the first page encountered
section_pages = section_pages.sort_values('min')

# Convert to ordered dictionary
section_page_dict = section_pages.set_index('section').T.to_dict()

@app.get("/assets/{fname:path}.{ext:static}")
async def serve_image(fname: str, ext: str):
    return FileResponse(f'assets/{fname}.{ext}')

@app.get("/")
def home():
    table_html = render()
    print("running home")
    return Title("Project 2025 Index", style="font-size: 2rem;"), Main(
            Div(
                H1('Project 2025 Index', style="margin-bottom: 30px;"),
                Figure(
                            Img(src="/assets/badge.jpg", alt="Project 2025 Badge",
                                style="display: block; margin: 0 auto; max-width: 50%; height: auto;"),
                            Figcaption(
                                'Image by ',
                                A('DonkeyHotey', href='https://www.flickr.com/photos/donkeyhotey/53792367625', target="_blank"),
                                style="text-align: center; font-size: 0.80rem; color: #888; margin-top: 5px;"
                            ),
                            style="margin-bottom: 30px;"
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
                    """),
                    style="margin-bottom: 10px; line-height: 1.5;"),
                style="padding: 20px; border-radius: 10px; margin-bottom: 10px;"
            ),
            Div(
                Form(
                    Div(
                        Span("Sort"),
                        Span("ⓘ", cls="tooltip")(
                            Span("Items can be sorted alphabetically, by page number, or by semantic similarity (vector). Sorting by semantic similarity arranges items with related subject matter closer together in the list.", cls="tooltiptext")
                        ),
                        style="margin-left: 5px;"
                    ),
                    reset_sort(),
                    style="margin-bottom: 10px;",
                ),
                Form(
                    Div(
                        Span("Filter"),
                        Span("ⓘ", cls="tooltip")(
                            Span("Items in the index that share titles with Wikipedia pages can be filtered based on the 'instance of' metadata from those Wikipedia pages.", cls="tooltiptext")
                        ),
                        style="margin-left: 5px;"
                    ),
                    reset_filter(),
                    style="margin-bottom: 10px;"
                ),
                # Div(
                reset_search(),
            # style="padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); margin-bottom: 10px;"
            style="padding: 20px; border-radius: 10px; margin-bottom: 10px;"

            ),
            Div(
            H2('Index'),
            # render_alphanav(),
            render_index_links(),
                Div(table_html, id='index-data'),
                # style="padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);"
                style="padding: 20px; border-radius: 10px;"

            ),
            cls="container"
    )

def render_index_links():
    global alphanav
    global pagenav
    if alphanav:
        return Div(
            Hr(),
            H3(*(
                (A(f"{letter if letter != 'num' else '#'}", id=f"{letter}", hx_post=f"/letter_sort?letter={letter}" if letter != "num" else f"/letter_sort?letter=num", hx_target="#index-data", hx_swap="innerHTML", hx_swap_oob='true'),
                 Span("", style="display:inline-block; width:5px;"))
                for letter in [item for item in string.ascii_uppercase] + ['num']
            ), _class="alphanav-container"),
            Hr(),
            id="alphanav",
            name="alphanavigator", hx_swap="innerHTML", hx_swap_oob='true'
        )
    elif pagenav:
        return Div(
            Hr(),
            P(*(
                (A(f"{section_page_dict[item]['min']}-{section_page_dict[item]['max']}", hx_post=f"/page_sort?page={section_page_dict[item]['min']}-{section_page_dict[item]['max']}", hx_target="#index-data", hx_swap="innerHTML", hx_swap_oob='true'), Span(" ", style="display:inline-block; width:10px;"))
                            for i,item in enumerate(section_page_dict)
                        )),
            Hr(),
            id="alphanav",
            name="alphanavigator",hx_swap="innerHTML", hx_swap_oob='true'
        )
    else:
        return Div(Hr(),id="alphanav",name="alphanavigator",hx_swap="innerHTML", hx_swap_oob='true')

# section_page_dict

# def render_alphanav():
#     print("called render_alphanav")

#     global alphanav
#     if alphanav:
#         return Div(
#             Hr(),
#             H3(*(
#                 (A(f"{letter if letter != 'num' else '#'}", id=f"{letter}", hx_post=f"/letter_sort?letter={letter}" if letter != "num" else f"/letter_sort?letter=num", hx_target="#index-data", hx_swap="innerHTML", hx_swap_oob='true'), Span(" ", style="display:inline-block; width:10px;"))
#                             for letter in [item for item in string.ascii_uppercase]+['num']
#                         )),
#             Hr(),
#             id="alphanav",
#             name="alphanavigator",hx_swap="innerHTML", hx_swap_oob='true'
#         )
#     else:
#         return Div(Hr(),id="alphanav",name="alphanavigator",hx_swap="innerHTML", hx_swap_oob='true')

def create_page_links(pages: list, summaries: list):
    """
    For a single entity, converts a list of page numbers and list of summary strings
    into a list of page links (of type list)
    """

    # Create a dictionary mapping unique pages to their corresponding summaries
    page_summary_map = {page: summaries[i] for i, page in enumerate(pages)}

    # Sort the pages
    sorted_pages = sorted(page_summary_map.keys())

    # Create the list of links with tooltips
    links = [
        Div(
            A(str(page), href=f'https://www.documentcloud.org/documents/24088042-project-2025s-mandate-for-leadership-the-conservative-promise#document/p{page+32}', target="_blank"),
            Div(page_summary_map[page], cls="tooltiptext"),
            cls="tooltip"
        )
        for page in sorted_pages
    ]

    # Add commas between links, except after the last one
    return [
        element for link in links for element in (link, Span(", ", _class="page-links-container"))
    ][:-1]

def create_letter_space(title, current_page=None):
    # print("called create_letter_space")

    global previous_initial
    global search_mode
    global sort_by
    global previous_page

    # If in search mode, don't add any spaces
    if search_mode:
        return None

    # Handle the sorting by page number
    if sort_by == "page":
        # Check if the page number has changed
        if previous_page is not None and current_page != previous_page:
            previous_page = current_page
            return Div(style="margin-top: 20px;")  # Add space for page change
        previous_page = current_page
        return None

    # Default behavior: handle alphabetical sorting
    current_initial = title[0].lower()

    # Skip adding space above the first group (usually 'A')
    if previous_initial is None:
        previous_initial = current_initial
        return None  # No space before the first letter group

    # Add a space if there's a transition from one letter to another
    if current_initial.isalpha() and previous_initial != current_initial:
        previous_initial = current_initial
        return Div(style="margin-top: 20px;")  # Add space after transitioning from one letter to another

    previous_initial = current_initial
    return None

def refresh_table():
    print("called refresh_table")

    global index_table
    global search_mode
    global previous_page
    global previous_initial  # Add this line

    # Reset search mode, previous page, and previous initial when refreshing the table
    search_mode = False
    previous_page = None
    previous_initial = None  # Reset previous_initial here

    index_table = alphabetical_limit(grouped_lancepd, 'a')
    return home()

def reset_sort():
    print("called reset_sort")

    global sort_by
    global filter_by
    global search_mode
    global alphanav
    global pagenav
    if filter_by=="none" and not search_mode:
        sort_by="alphabetical"
        alphanav = True
        pagenav = False
    else:
        sort_by="none"
    return Select(
        Option("None", value="none", selected=sort_by=="none"),
        Option("Alphabetical", value="alphabetical", selected=sort_by == "alphabetical"),
        Option("Page Number", value="page", selected=sort_by == "page"),
        Option("Vector", value="vector", selected=sort_by == "vector"),
        name="sort_type",
        id="sort_form",
        hx_post="/sort", hx_target="#index-data", hx_swap="innerHTML", hx_swap_oob='true'
    )

def reset_search():
    print("called reset_search")

    global search_mode
    global previous_page
    global previous_initial
    global search_by
    search_mode = False
    previous_page = None
    previous_initial = None  # Reset previous_initial here
    search_by = "title_vector"
    return Form(
        Div(
            Div(Span("Search"),  # Add text next to the search input
            style="margin-left: 5px;"
            ),
            Input(placeholder="Search the document", type= "search",name="query", id="search", hx_swap_oob='true'),
            style="width: 50%; display: inline-block; vertical-align: top; margin-right: 5px;",
        ),
        Div(
            Div(
            Span("Search Type"),  # Add text next to the select input
            Span("ⓘ", cls="tooltip")(
                Span("Searching by 'Title' will find items with titles closest to your query, while searching by 'Context' will locate summaries in the tooltips that are most relevant to your query.", cls="tooltiptext")
            ),
            style="margin-left: 5px;"
            ),
            Select(
                Option("Title", value="title_vector", selected=search_by == "title_vector"),
                Option("Context", value="summary_vector", selected=search_by == "summary_vector"),
                name="search_type",
                id="search_type_form",
                hx_swap_oob='true'
            ),

            style="width: 50%; display: inline-block; vertical-align: top; margin-left: 10px"
        ),
        style="display: flex; width: 100%; margin-bottom: 10px;",
        hx_post="/search", hx_target="#index-data", hx_swap="innerHTML", hx_swap_oob='true'
    )

def reset_filter():
    print("called reset_filter")
    global filter_by
    filter_by="none"
    return Select(
        Option("None", value="None", selected=filter_by=="none"), *[Option(entity, value=entity, selected=filter_by==entity) for entity in filter_entities],
        name="filter_type",
        id="filter_form",
        hx_post="/filter", hx_target="#index-data", hx_swap="innerHTML", hx_swap_oob='true'
    )

@app.post("/letter_sort")
async def print_letter(request: Request, letter: str = None):
    print("called print_letter")

    global index_table
    letter = letter or request.query_params.get('letter')
    index_table = alphabetical_limit(grouped_lancepd, str(letter))
    table_html = render()
    return table_html

@app.post("/page_sort")
async def print_page(request: Request, page: str= None):
    print("called print_page")

    global index_table
    page_range = page or request.query_params.get('page')
    p_min, p_max = page_range.split('-')[0],page_range.split('-')[1]
    print(p_min)
    print(p_max)
    data = table.to_pandas()
    data = data[(data['page'] >= int(p_min)) & (data['page'] <= int(p_max))]

    # data = data[(data['page'] >= p_min) & (data['page'] <= [p_max])]
    data['summary'] = data['summary'].apply(lambda x: [x])
    data['page'] = data['page'].apply(lambda x: [x])
    index_table = data
    table_html = render()
    return table_html



@app.post("/sort")
def sort_table(sort_type:str):
    print("called sort_table")

    global sort_by
    global filter_by
    global search_mode
    global previous_page
    global previous_initial  # Add this line
    global alphanav
    global pagenav
    global index_table

    # Reset search mode, previous page, and previous initial when sorting
    # search_mode = False
    # previous_page = None
    # previous_initial = None  # Reset previous_initial here
    search_mode = False
    previous_page = None
    previous_initial = None
    filter_by = "none"
    if sort_type == 'alphabetical':
        alphanav = True
        pagenav = False
        sort_by = 'alphabetical'
        index_table = alphabetical_limit(grouped_lancepd, 'a')
    elif sort_type == 'page':
        print("sort type equals page")
        alphanav = False
        pagenav = True
        data = table.to_pandas()
        data = data[(data['page'] >= 1) & (data['page'] <= 17)]
        data['summary'] = data['summary'].apply(lambda x: [x])
        data['page'] = data['page'].apply(lambda x: [x])
        index_table = data
        print(index_table)
        sort_by = 'page'
    elif sort_type == 'vector':
        alphanav =False
        pagenav = False
        index_table = alphabetical_sort_table(grouped_lancepd).sort_values(by='title_index')
        sort_by = 'vector'
    print("finished sort")
    return render(), render_index_links(), reset_filter(), reset_search()

@app.post("/search")
def vector_search(query:str, search_type:str):
    print("called vector_search")

    global filter_by
    global sort_by
    global search_mode
    global alphanav
    global pagenav
    global index_table

    print("searching")
    # Set search mode to True
    search_mode = True
    alphanav = False
    pagenav = False

    filter_by = "none"
    sort_by = "alphabetical"
    if not query:
        # Reset search mode if there's no query
        search_mode = False
        return render()

    global search_by
    search_by = search_type
    if search_by == "title_vector":
        vector_column_name="title_vector"
    elif search_by == "summary_vector":
        vector_column_name="summary_vector"

    results = table.search(query, vector_column_name=vector_column_name).limit(50).to_pandas()

    if search_by == "title_vector":
        data = results.groupby('title', sort=False).agg({
            'page': list,
            'summary': list  # Create a list of summaries corresponding to each page
        }).reset_index()
        # print(data)
        # print(data.columns)
        if isinstance(results['instance_of'].iloc[0], (list, np.ndarray)):
            results['instance_of'] = results['instance_of'].apply(tuple)
        merge_columns = results[['title', 'title_index', 'instance_of', 'wikipedia_url']].drop_duplicates()
        # Merge the grouped data with the additional columns from the original DataFrame
        result = pd.merge(data, merge_columns, on='title', how='left')
    elif search_by == "summary_vector":
        data = results
        data['summary'] = data['summary'].apply(lambda x: [x])
        data['page'] = data['page'].apply(lambda x: [x])
        result = data
        # print(data)
        # print(data.columns)
    index_table = result
    # print(index_table)
    return render(), reset_filter(), reset_sort(), render_index_links()

@app.post("/filter")
def filter_table(filter_type: str):
    print("called filter_table")
    global index_table
    global filter_by
    global sort_by
    global search_mode
    global previous_page
    global alphanav
    global pagenav

    # Reset search mode and previous page when filtering
    # search_mode = False
    # previous_page = None
    sort_by = "alphabetical"
    alphanav = False
    pagenav = False
    if filter_type == "None":
        # Reset to the full, alphabetically sorted list
        index_table = alphabetical_sort_table(grouped_lancepd)
        filter_by="none"
    else:
        # Filter the DataFrame based on the selected filter_type
        filtered_data = alphabetical_sort_table(grouped_lancepd)[alphabetical_sort_table(grouped_lancepd)['instance_of'].apply(lambda x: filter_type in x)]
        index_table = filtered_data
        filter_by=filter_type
    return render(), reset_sort(), reset_search(), render_index_links()

setup_hf_backup(app)
serve()
