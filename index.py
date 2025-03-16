import os
import streamlit as st
from common import WSP_LOGO_SVG, get_tools

# The content of this page is applied to all other pages
st.set_page_config(page_title='Modelling Tools', layout='wide')
st.logo(WSP_LOGO_SVG)

# This gets rid of some of the unncessary whitespace at the top of the page
# https://github.com/streamlit/streamlit/issues/6336
st.markdown(
    """
        <style>
            .appview-container .main .block-container {{
                padding-top: {padding_top}rem;
                padding-bottom: {padding_bottom}rem;
                }}

        </style>""".format(padding_top=3, padding_bottom=1),
    unsafe_allow_html=True)

dashboard = st.Page('dashboard.py', title='Dashboard', default=True)

# Don't give a category name to this one
tools = {'': [dashboard]}

for path, category in get_tools():
    # Make the page
    page = st.Page(path)
    # Assign it to its category
    if category in tools:
        tools[category].append(page)
    else:
        tools[category] = [page]

pg = st.navigation(tools, position='hidden')
pg.run()
