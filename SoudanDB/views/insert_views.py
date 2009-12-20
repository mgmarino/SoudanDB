from database_views import insert_view_into_database
from SoudanDB.management.soudan_database import get_current_db_module 
import pkgutil

def insert_views():
    def my_import(name):
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod

    function_list = []
    # Which database are we using?
    # Grab all the modules from the update directory
    current_db_name = '%s.views' % get_current_db_module()
    update_module = my_import(current_db_name)
    imported_list = []
    for loader,name,ispkg in pkgutil.iter_modules(update_module.__path__):
        if ispkg: continue
        load = pkgutil.find_loader('%s.%s' % (current_db_name, name))
        mod = load.load_module("%s.%s" % (current_db_name,name))
        imported_list.append(mod)

    view_list = []
    for mdl in imported_list:
        try:
            view_list.append(mdl.get_view_class())
        except AttributeError:
            pass

    for view in view_list:
        insert_view_into_database(view)

