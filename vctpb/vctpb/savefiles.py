import os
from datetime import datetime
from pytz import timezone
import jsonpickle
import sys
import shutil
import time

def get_date_string():
  central = timezone('US/Central')
  return datetime.now(central).strftime("%Y-%m-%d-%H-%M-%S")

#year, month, day, hour, min, sec = date_string_to_vars(date_sting)
def date_string_to_vars(date_string):
  return date_string.split("-")

def get_seconds(date_string):
  hour, min, sec = (date_string_to_vars(date_string))[-3:]
  return int(hour) * 3600 + int(min) * 60 + int(sec)

def get_days(date_string):
  year, month, day = (date_string_to_vars(date_string))[:3]
  day_of_year = datetime(int(year), int(month), int(day))
  return(day_of_year - datetime(1970,1,1)).days

def get_all_names(path="files/", ext=False):
  names = os.listdir(f"savedata/{path}")
  if ext:
    return names
  return [os.path.splitext(name)[0] for name in names]

def get_prefix(prefix, path="files/", ext=False):
  names = os.listdir(f"savedata/{path}")
  prefix_names = [name for name in names if name.startswith(prefix)]
  if ext:
    return prefix_names
  return [os.path.splitext(prefix_name)[0] for prefix_name in prefix_names]

def get_file(name, path="files/"):
  path_and_file = f"savedata/{path}{name}.txt"
  r = open(path_and_file, "r")
  fs = jsonpickle.decode(r.read())
    
  return fs
  
def set_setting_test():
  with open(f"savedata/settings/save_repo.txt", "w") as f:
    f.write(jsonpickle.encode("dev-save-repo"))
    
  with open(f"savedata/settings/discord_token.txt", "w") as f:
    f.write(jsonpickle.encode("devdiscordtoken"))
    
  with open(f"savedata/settings/github_token.txt", "w") as f:
    f.write(jsonpickle.encode("devgithubtoken"))
    
  with open(f"savedata/settings/guild_ids.txt", "w") as f:
    f.write(jsonpickle.encode([731630214194659388]))
  
  
def get_setting(name):
      
  path_and_file = f"settings/{name}.txt"
  
  if not os.path.isfile(path_and_file):
    print(f"setting {name} not found.\nquitting")
    quit()
  
  r = open(path_and_file, "r")
  val = r.read()
  fs = jsonpickle.decode(val)
  return fs


def save_setting(name, val):
  path_and_file = f"settings/{name}.txt"
  with open(path_and_file, "w") as f:
    f.write(jsonpickle.encode(val))


def save_file(name, obj, path="files/"):
  path_and_file = f"savedata/{path}{name}.txt"
  with open(path_and_file, "w") as f:
    f.write(jsonpickle.encode(obj))

  
  r = open(path_and_file, "r")
  fs = jsonpickle.decode(r.read())
  if fs != obj:
    create_error_file("save error", f"Didn't save {name} to {path_and_file}.")

def make_folder(name, path):
  os.mkdir(f"savedata/{path}{name}/")

  
def delete_file(name, path):
  path_and_file = f"savedata/{path}{name}.txt"
  print(f"deleting {path_and_file}")


def delete_folder(name, path):
  path_and_file = f"savedata/{path}{name}"
  try:
    shutil.rmtree(path_and_file)
    print(f"deleted folder {path_and_file}")
  except OSError as e:
    create_error_file("delete error", f"couldn't remove {name} path {path_and_file}.")
    print("Error: %s - %s." % (e.filename, e.strerror))


def create_error_file(name, s):
  datestring = get_date_string()
  save_file(f"{name}-{datestring}", f"{s}\n{datestring}", path="errors/")
  
def backup():
  keys = get_all_names()
  date_string = get_date_string()
  print(date_string)
  make_folder(date_string, f"backup/")
  date_path = f"backup/{date_string}/"
  for key in keys:
    if not key.startswith("backup_"):
      val = get_file(key)
      save_file(key, val, path=date_path)
  delete_old_backup()


def equate(x):
  #standard
  sy = (x) ** (1/2) 
  #initial boost
  iby = -20/(x+1)
  y = int(sy + iby)
  return y



def delete_old_backup():
  file_names = get_all_names(path="backup/")
  date_string = get_date_string()
  old_file_names = []
  for file_name in file_names:
    if not file_name.startswith(date_string[:10]):
      old_file_names.append(file_name)
      
  #all files from the day deleted
  file_days_dict = {}
  for old_file_name in old_file_names:
    ymd = old_file_name[:10]
    if (day_list := file_days_dict.get(ymd)) is None:
      file_days_dict[ymd] = [old_file_name]
      continue
    day_list.append(old_file_name)
    file_days_dict[ymd] = day_list
  
  file_days = list(file_days_dict.items())
  singles = []
  deleted = []
  for file_day in file_days:
    if len(file_day[1]) == 1:
      singles.append(file_day[1][0])
      continue
    times = []
    for file_name in file_day[1]:
      times.append((file_name, get_seconds(file_name)))
      
    times.sort(key=lambda x: x[1])
    for time_t in times[:-1]:
      deleted.append(time_t[0])
      delete_folder(time_t[0], "backup/")
    singles.append(times[-1][0])

  print("day delete done")
    
  singles.sort(reverse=True)
  day = []
  for single in singles:
    day.append((single, get_days(single)))
  
  #first is name second is days since flipped
  high = day[0][1]
  dates_t = [(date[0], high - date[1] + 1) for date in day]
  
  layers = {}
  for date_t in dates_t:
    y = equate(date_t[1])
    if y in layers:
      layers[y].append(date_t[0])
    else:
      layers[y] = [date_t[0]]

  layer_list = list(layers.items())
  points = []
  for layer in layer_list:
    if len(layer[1]) > 1:
      for name in layer[1][:-1]:
        delete_folder(name, "backup/")

  print("done delete backup")
        
        


