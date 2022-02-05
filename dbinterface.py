import jsonpickle 
from replit import db
import math

def get_from_list(prefix, identifier):
  objects = get_all_objects(prefix)
  if objects == None or objects.count == 0:
    return None
  for obj in objects:
    if str(obj.code) == str(identifier):
      return obj
  return None

def add_to_list(prefix, obj):
  print(jsonpickle.encode(obj))
  objects = get_all_objects(prefix)
  if len(objects) == 0:
    db[prefix + "_list_1"] = list([jsonpickle.encode(obj)])
    return
  list_num = math.floor(len(objects) / 50)
  list_prog = len(objects) % 50
  if list_prog == 0:
    db[prefix + "_list_" + str(list_num + 1)] = [jsonpickle.encode(obj)]
    return

  list_to_add = list(db[prefix + "_list_" + str(list_num + 1)])
  list_to_add.append(jsonpickle.encode(obj))
  db[prefix + "_list_" + str(list_num + 1)] = list_to_add


def replace_in_list(prefix, identifier, obj):
  objects = get_all_objects(prefix)
  objects_e = [jsonpickle.encode(obj) for obj in objects]

  if get_from_list(prefix, identifier) == None:
    print(prefix + identifier)
    return "No Identifier Found"
    
  object_to_replace = jsonpickle.encode(get_from_list(prefix, identifier))
  index = objects_e.index(object_to_replace)
  list_num = math.floor(index / 50)

  list_to_replace = list(db[prefix + "_list_" + str(list_num + 1)])
  list_to_replace[list_to_replace.index(object_to_replace)] = jsonpickle.encode(obj)
  db[prefix + "_list_" + str(list_num + 1)] = list_to_replace



def remove_from_list(prefix, obj_ambig):
  if isinstance(obj_ambig, int) or isinstance(obj_ambig, str):
    obj_found = get_from_list(prefix, obj_ambig)
  else:
    obj_found = obj_ambig

  objects = get_all_objects(prefix)
  objects_e = [jsonpickle.encode(obj) for obj in objects]

  if obj_found == None:
    return "No Identifier Found"

  object_to_remove = jsonpickle.encode(obj_found)
  if len(objects_e) == 0 or (not object_to_remove in objects_e):
    return "No Identifier Found"
  index = objects_e.index(object_to_remove)
  list_num = math.floor(index / 50)
  list_to_add = list(db[prefix + "_list_" + str(list_num + 1)])
  list_to_add.remove(object_to_remove)
  if len(list_to_add) == 0:
    del db[prefix + "_list_" + str(list_num + 1)]
    return "Removed " + prefix
  
  db[prefix + "_list_" + str(list_num + 1)] = list_to_add
  if list_num + 1 == len(db.prefix(prefix + "_list_")):
    return "Removed " + prefix
  for x in range(list_num + 1, len(list(db.prefix(prefix + "_list_")))):
    list1 = list(db[prefix + "_list_" + str(x)])
    list2 = list(db[prefix + "_list_" + str(x + 1)])
    list1.append(list2[0])
    list2.remove(list2[0])
    db[prefix + "_list_" + str(x)] = list1

    if len(list2) == 0:
      del db[prefix + "_list_" + str(x + 1)]
    else:
      db[prefix + "_list_" + str(x + 1)] = list2

  return "Removed " + prefix


def get_all_objects(prefix):
  list_keys_unordered = db.prefix(prefix + "_list_")
  if len(list_keys_unordered) == 0:
    print("no keys of type " + prefix)
    return []
  list_keys = [str(prefix + "_list_" + str(x + 1)) for x in range(len(list_keys_unordered))]
  lists = [list(db[listt]) for listt in list(list_keys)]
  list_objects = sum(list(lists), [])
  objs = [jsonpickle.decode(obj) for obj in list_objects]
  return objs

async def smart_get_user(user_id, bot):
  user = bot.get_user(user_id)
  print(user)
  if user == None:
    user = await bot.fetch_user(user_id)
  return user