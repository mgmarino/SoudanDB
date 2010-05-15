from database_cuts import insert_cut_into_database
from ..management.soudan_database import get_current_db_module 
import pkgutil

def insert_cuts():
    def my_import(name):
        mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        return mod

    function_list = []

    # Which database are we using?
    # Grab all the modules from the update directory
    current_db_name = '%s.cuts' % get_current_db_module()
    update_module = my_import(current_db_name)
    imported_list = []
    for loader,name,ispkg in pkgutil.iter_modules([update_module.__path__[0]]):
        if ispkg: continue
        load = pkgutil.find_loader('%s.%s' % (current_db_name, name))
        mod = load.load_module("%s.%s" % (current_db_name,name))
        imported_list.append(mod)

    cut_list = []
    for mdl in imported_list:
        try:
            print "Trying to load: %s " % mdl
            cut_list.append(mdl.get_cut_class())
        except AttributeError:
            print "Module: %s does not have get_cut_class attribute, skipping." % mdl
            pass

    for cut in cut_list:
        insert_cut_into_database(cut)
