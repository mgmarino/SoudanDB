#!/usr/local/bin/python
import hashlib
import os.path
import imp
import traceback
import sys
from database_views import insert_view_into_database

def load_module(code_path):
    try:
        try:
            code_dir = os.path.dirname(code_path)
            code_file = os.path.basename(code_path)

            fin = open(code_path, 'rb')

            return  imp.load_source(hashlib.md5(code_path).hexdigest(), code_path, fin)
        finally:
            try: fin.close()
            except: pass
    except ImportError, x:
        traceback.print_exc(file = sys.stderr)
        raise
    except:
        traceback.print_exc(file = sys.stderr)
        raise


if __name__ == '__main__':
    imported_list = []
    for name in sys.argv[1:]:
        imported_list.append(load_module(name))
    
    view_list = []
    for mdl in imported_list:
        try:
            print "Trying to load: %s " % mdl
            view_list.append(mdl.get_view_class())
        except AttributeError:
            print "Module: %s does not have get_view_class attribute, skipping." % mdl
            pass

    for view in view_list:
        insert_view_into_database(view)
