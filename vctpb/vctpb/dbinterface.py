import jsonpickle 
import math
from datetime import datetime
from pytz import timezone
from savefiles import save_file, get_file, delete_file, get_prefix

def get_date():
  central = timezone('US/Central')
  return datetime.now(central)


def get_from_list(prefix, identifier):
  if prefix == "None":
    return None
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
    save_file(prefix + "_list_1", [jsonpickle.encode(obj)])
    return
  list_num = math.floor(len(objects) / 50)
  list_prog = len(objects) % 50
  if list_prog == 0:
    save_file(prefix + "_list_" + str(list_num + 1), [jsonpickle.encode(obj)])
    return
  list_to_add = get_file(prefix + "_list_" + str(list_num + 1))
  list_to_add.append(jsonpickle.encode(obj))
  
  save_file(prefix + "_list_" + str(list_num + 1), list_to_add)


def replace_in_list(prefix, obj_code, obj):
  
  objects = get_all_objects(prefix)
  for dbobj in objects:
    if dbobj.code == obj_code:
      index = objects.index(dbobj)
      list_num = math.floor(index / 50)
      list_to_replace = get_file(prefix + "_list_" + str(list_num + 1))
      list_index = 0
      for listdbobj in list_to_replace:
        if jsonpickle.decode(listdbobj).code == obj_code:
          list_to_replace[list_index] = jsonpickle.encode(obj)
          save_file(prefix + "_list_" + str(list_num + 1), list_to_replace)
          return
        list_index += 1

      print("none found")
      return

  



def remove_from_list(prefix, obj_ambig):
  if isinstance(obj_ambig, int) or isinstance(obj_ambig, str):
    obj_found = get_from_list(prefix, obj_ambig)
  else:
    obj_found = obj_ambig

  objects = get_all_objects(prefix)
  objects_e = [jsonpickle.encode(obj) for obj in objects]

  if obj_found == None:
    print("No Identifier Found")
    return None

  object_to_remove = jsonpickle.encode(obj_found)
  if len(objects_e) == 0 or (not object_to_remove in objects_e):
    print("No Identifier Found")
    return None
  index = objects_e.index(object_to_remove)
  list_num = math.floor(index / 50)
  list_to_add = get_file(prefix + "_list_" + str(list_num + 1))
  list_to_add.remove(object_to_remove)
  if len(list_to_add) == 0:
    delete_file(prefix + "_list_" + str(list_num + 1))
    return obj_found

  save_file(prefix + "_list_" + str(list_num + 1), list_to_add)
  if list_num + 1 == get_prefix(prefix + "_list_"):
    return obj_found
  for x in range(list_num + 1, len(get_prefix(prefix + "_list_"))):
    
    list1 = get_file(prefix + "_list_" + str(x))
    list2 = get_file(prefix + "_list_" + str(x + 1))
    list1.append(list2[0])
    list2.remove(list2[0])
    save_file(prefix + "_list_" + str(x), list1)

    if len(list2) == 0:
      delete_file(prefix + "_list_" + str(x + 1))
    else:
      save_file(prefix + "_list_" + str(x + 1), list2)

  return obj_found


def get_all_objects(prefix):
  list_keys_unordered = get_prefix(prefix + "_list_")
  if len(list_keys_unordered) == 0:
    print("no keys of type " + prefix)
    return []
  list_keys = [str(prefix + "_list_" + str(x + 1)) for x in range(len(list_keys_unordered))]
  lists = [list(get_file(listt)) for listt in list(list_keys)]
  list_objects = sum(list(lists), [])
  objs = [jsonpickle.decode(obj) for obj in list_objects]
  return objs

async def smart_get_user(user_id, bot):
  user = bot.get_user(user_id)
  if user == None:
    print("fetched")
    user = await bot.fetch_user(user_id)
  return user