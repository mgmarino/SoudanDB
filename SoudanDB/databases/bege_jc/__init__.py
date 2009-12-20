from SoudanDB.management import ServerSingleton, CurrentDBSingleton
from db import BeGeJCDB
ServerSingleton.set_server(BeGeJCDB)
CurrentDBSingleton.set_current_db_module(__name__)
