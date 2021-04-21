import re

sanitizeVarname = lambda vname: re.sub("[^a-zA-Z_0-9]+","",vname)
