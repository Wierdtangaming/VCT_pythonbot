import os
from datetime import datetime
from pytz import timezone
import jsonpickle
import sys
import shutil
import time
 
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
        
        


