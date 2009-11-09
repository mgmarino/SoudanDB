#!/usr/bin/env python
from management.soudan_database import SoudanServer
import pkgutil
import inspect
def update_calculations_on_database():
    server = SoudanServer()
    
    function_list = []

    for loader,name,ispkg in pkgutil.iter_modules(['update']):
        if ispkg: continue
        load = pkgutil.find_loader('update.%s' % name)
        mod = load.load_module("update.%s" % name)
        for aname in mod.__dict__.keys():
            if inspect.isfunction(getattr(mod, aname)):
                function_list.append(getattr(mod, aname))

    for id in server.get_database():
        run_doc = server.get_run(id)
        if not run_doc: continue
        must_reinsert = False
        for function in function_list:
            (run_doc, temp_bool) = function(run_doc)
            must_reinsert = must_reinsert or temp_bool
        if must_reinsert:
            print "Updating run number: %s" % run_doc.id
            server.insert_rundoc(run_doc)

if __name__ == '__main__':
    update_calculations_on_database()
