from SoudanDB.management import ServerSingleton, CurrentDBSingleton
from db import PPCTwoDB
ServerSingleton.set_server(PPCTwoDB)
CurrentDBSingleton.set_current_db_module(__name__)
