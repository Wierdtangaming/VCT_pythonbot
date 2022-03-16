import os
from github import Github
from zipfile import ZipFile
import zipfile
from savefiles import create_error_file

from savefiles import backup

BUFSIZE = 1024

def backup_full():
  save_to_github("backup", backupf=True)




def save_to_github(message, backupf=False):

  user = os.environ['GithubUsername']
  token = os.environ['GithubToken']
  
  g = Github(user, token)
  repo = g.get_user().get_repo("dev-save-data")
  all_files = []
  contents = repo.get_contents("")

  #shutil.make_archive("backup", 'zip', "savedata/")
  d = "backup"

  os.remove("backup.zip")
  with ZipFile(d + '.zip', "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
    for root, _, filenames in os.walk("savedata/"):
      for name in filenames:
        name = os.path.join(root, name)
        name = os.path.normpath(name)
        zf.write(name, name)
    zf.close()
    
  while contents:
    file_content = contents.pop(0)
    if file_content.type == "dir":
      contents.extend(repo.get_contents(file_content.path))
    else:
      file = file_content 
      all_files.append(str(file).replace('ContentFile(path="','').replace('")',''))

  
  os.remove("gitbackup.zip")
  content = repo.get_contents(all_files[0])
  with open("gitbackup.zip", "wb") as f:
    f.write(content.decoded_content)

  
  if are_equivalent("backup.zip", "gitbackup.zip"):
    print("Local and github are the same.")
    return

  
  if backupf:
    backup()

    
  os.remove("backup.zip")
  with ZipFile(d + '.zip', "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
    for root, _, filenames in os.walk("savedata/"):
      for name in filenames:
        name = os.path.join(root, name)
        name = os.path.normpath(name)
        zf.write(name, name)
    zf.close()
    
  
  #data = base64.b64encode(open("backup.zip", "rb").read())
  data = open("backup.zip", "rb").read()
  
  repo.update_file("backup.zip", message, data, content.sha)
  print("Backed up to git.")
  return
  




def are_equivalent(filename1, filename2):
    """Compare two ZipFiles to see if they would expand into the same directory structure
    without actually extracting the files.
    """
  
    if (not zipfile.is_zipfile(filename1)) or (not zipfile.is_zipfile(filename2)):
      create_error_file("not valid zip", f"{zipfile.is_zipfile(filename1)}, {zipfile.is_zipfile(filename2)}")
      return False
    
    with ZipFile(filename1, 'r') as zip1, ZipFile(filename2, 'r') as zip2:
      
      # Index items in the ZipFiles by filename. For duplicate filenames, a later
      # item in the ZipFile will overwrite an ealier item; just like a later file
      # will overwrite an earlier file with the same name when extracting.
      zipinfo1 = {info.filename:info for info in zip1.infolist()}
      zipinfo2 = {info.filename:info for info in zip2.infolist()}
      
      # Do some simple checks first
      # Do the ZipFiles contain the same the files?
      if zipinfo1.keys() != zipinfo2.keys():
        print("1", len(zipinfo1.keys()), len(zipinfo2.keys()))
        return False
      
      # Do the files in the archives have the same CRCs? (This is a 32-bit CRC of the
      # uncompressed item. Is that good enough to confirm the files are the same?)
      if any(zipinfo1[name].CRC != zipinfo2[name].CRC for name in zipinfo1.keys()):
        print("2")
        return False
      
      # Skip/omit this loop if matching names and CRCs is good enough.
      # Open the corresponding files and compare them.
      for name in zipinfo1.keys():
          
        # 'ZipFile.open()' returns a ZipExtFile instance, which has a 'read()' method
        # that accepts a max number of bytes to read. In contrast, 'ZipFile.read()' reads
        # all the bytes at once.
        with zip1.open(zipinfo1[name]) as file1, zip2.open(zipinfo2[name]) as file2:
          
          while True:
            buffer1 = file1.read(BUFSIZE)
            buffer2 = file2.read(BUFSIZE)
            
            if buffer1 != buffer2:
              print("3")
              return False
            
            if not buffer1:
              break
                  
      print("4")  
      return True