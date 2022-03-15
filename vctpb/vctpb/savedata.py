import os
from github import Github
import shutil


def save_to_github(message):
  print(os.getcwd())
  user = os.environ['GithubUsername']
  token = os.environ['GithubToken']

  
  g = Github(user, token)
  repo = g.get_user().get_repo("dev-save-data")
  all_files = []
  contents = repo.get_contents("")


  shutil.make_archive("backup", "zip", "savedata")












  return
  
  while contents:
    file_content = contents.pop(0)
    if file_content.type == "dir":
      contents.extend(repo.get_contents(file_content.path))
    else:
      file = file_content 
      all_files.append(str(file).replace('ContentFile(path="','').replace('")',''))
  
  with open('', 'r') as file:
    content = file.read()
  
  # Upload to github
  git_prefix = 'dev-save-data/'
  git_file = git_prefix + 'backup/'
  if git_file in all_files:
    contents = repo.get_contents(git_file)
    repo.update_file(contents.path, "committing files", content, contents.sha, branch="master")
    print(git_file + ' UPDATED')
  else:
    repo.create_file(git_file, "committing files", content, branch="master")
    print(git_file + ' CREATED')
