from jinja2 import Environment, FileSystemLoader

def environment(**options):
    """
    Returns a configured Jinja2 environment.
    """
    options.setdefault("loader", FileSystemLoader("jinja_templates"))  # folder for Jinja2 templates
    env = Environment(**options)
    # You can add custom filters or globals here if needed
    return env
