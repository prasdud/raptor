from jinja2 import Environment, FileSystemLoader
import re

def latex_escape(text):
    """
    Escape special LaTeX characters in text.
    Handles quotes, underscores, and other special characters.
    ORDER MATTERS: Backslash must be escaped first!
    """
    if not isinstance(text, str):
        return text
    
    # CRITICAL: Escape backslash FIRST, before adding any other backslashes
    text = text.replace('\\', r'\textbackslash{}')
    
    # Now escape other special characters (order doesn't matter for these)
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '"': "''",  # Convert double quotes to LaTeX double quotes
        '"': "''",  # Closing smart quote
        '"': "''",  # Opening smart quote  
        ''': "'",   # Single smart quote
        ''': "'",   # Single smart quote
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    
    return text

def environment(**options):
    """
    Returns a configured Jinja2 environment.
    """
    options.setdefault("loader", FileSystemLoader("jinja_templates"))  # folder for Jinja2 templates
    env = Environment(**options)
    
    # Add custom LaTeX escape filter
    env.filters['latex_escape'] = latex_escape
    
    return env

