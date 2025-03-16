import os
from glob import glob
import streamlit as st

WSP_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72.5 34.479" fill="#ff372f">
<path d="M86.144,27.894a14.183,14.183,0,0,0-3.3-9.317h5.43a15.607,15.607,0,0,1,2.885,9.317v.014a15.617,15.617,0,0,1-2.895,9.333h-5.43a14.176,14.176,0,0,0,3.312-9.333Z" transform="translate(-18.657 -18.577)" ></path>
<path d="M5.014,0H0L6.881,18.66H9.546l1.174-3.185Z" ></path>
<path d="M18.465,0H13.451l6.881,18.66H23l1.174-3.185Z"></path>
<path d="M56.762,34.479V0h-4.8V34.479Z" ></path>
<path d="M47.918,21.344a8.223,8.223,0,0,1,.646-2.768h4.388a4.028,4.028,0,0,0-.319,3.07,4.6,4.6,0,0,0,2.05,2.432,29.2,29.2,0,0,0,3.628,1.682,14.681,14.681,0,0,1,3.536,2.114,7.015,7.015,0,0,1,2.611,4.939c.019.243.027.487.027.731a8.234,8.234,0,0,1-.77,3.691H59.209a5.025,5.025,0,0,0,.73-2.73c-.158-2.35-3.029-3.636-5.43-4.705-.367-.17-.726-.322-1.071-.484a13.729,13.729,0,0,1-2.995-1.811,6.357,6.357,0,0,1-2.074-2.684,7.766,7.766,0,0,1-.47-3.141C47.9,21.568,47.908,21.456,47.918,21.344Z" transform="translate(-18.657 -18.577)"></path>
</svg>
"""


def setup_page(title, maintainer, ):
    """
    title: str: The title of the page
    maintainer: str: The email address of the person responsible for maintaining the page
    """
    col1, col2 = st.columns([30, 1])
    with col1:
        st.markdown("This tool should be considered untested. **It is the user's responsiblity to verify all results.** " +
                    'For maintenance contact: [{0}](mailto:{0})'.format(maintainer))
    with col2:
        if st.button(':material/home:'):
            st.switch_page('dashboard.py')

    st.title(title)
    add_red_line()


def add_red_line():
    st.markdown('<div style="height: 2px; background-color: red; margin: 0;"/>', unsafe_allow_html=True)


class MockUploadedFile(str):
    name: str
    # This is a mock of the UploadedFile class from streamlit. It is used to test the file upload functionality
    # (basically adds a name attribute to a string)

    def __new__(cls, content, name: str):
        ret = super().__new__(cls, content)
        ret.name = name
        return ret


def right_aligned_text(text):
    styled_text(text, text_align='right', height=80)


def styled_text(text, **kwargs):
    """Create styled text by providing html style arguments as keyword arguments (dashes replaced with underscores)"""
    style_args = '; '.join([f'{k.replace("_", "-")}: {v}' for k, v in kwargs.items()])
    st.markdown(f'<div style="{style_args}">{text}</div>', unsafe_allow_html=True)


def get_tools():
    """
    returns an iterable of the path to the tool script and its categoru
    """
    # Use the directory of this file to get a reference to pages, so it works in the tests
    for path in glob(os.path.join(os.path.dirname(__file__), 'tools', '*', '*.py'), recursive=True):
        # Ignore the __init__ files
        if not path.endswith('__.py'):
            # Use the folder names as the category titles
            category = os.path.basename(os.path.dirname(path))
            yield path, category
