#!/usr/bin/env python
import hashlib
import os.path
import imp
import traceback
import sys
from database_cuts import insert_cut_into_database

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
