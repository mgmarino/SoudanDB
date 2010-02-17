from ..views import view_virgin_livetime

def update_rundoc(rundoc):
    """
    Returns whether or not the rundoc has been updated.
    """
    rundoc.livetime.run_milliseconds = 3600*1000
    rundoc.livetime.run_milliseconds_error = 1000
    return (rundoc, True)

def get_view():
    return view_virgin_livetime.get_view_class()
