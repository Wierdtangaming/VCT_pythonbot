import discord
from colorinterface import hex_to_tuple


def get_role(user, username):
  roles = user.roles
  for role in roles:
    if role.name == f"Prediction {username}":
      return role
  return None

async def create_role(guild, username, hex):
  role = await guild.create_role(name = f"Prediction {username}", color=discord.Color.from_rgb(*hex_to_tuple(hex)))
  await set_position(guild, role)
  print(role.position)
  return role
  
  
async def set_position(guild, role):  
  highest_position = 0
  oroles = guild.roles
  try:
    for orole in oroles:
      if orole.position > highest_position and role.permissions.administrator == False:
        print(orole.name, orole.position, role.permissions)
        highest_position = orole.position
        await role.edit(position=orole.position)
        highest_position = orole.position
  except:
    pass
  print(highest_position, role.position)
  
  
async def add_role(user, role):
  await user.add_roles(role)

async def delete_role(role):
  await role.delete()
  
async def recolor_role(role, hex):
  await role.edit(color=discord.Color.from_rgb(*hex_to_tuple(hex)))
  print(role.position)

async def set_role(guild, author, username, hex):
  role = get_role(author, username)
  if role is None:
    role = await create_role(guild, username, hex)
    await add_role(author, role)
  else:
    await recolor_role(role, hex)
    
  await set_position(guild, role)

async def unset_role(author, username):
  role = get_role(author, username)
  if role is not None:
    await delete_role(role)
    
async def edit_role(guild, author, username, hex):
  role = get_role(author, username)
  if role is not None:
    await recolor_role(role, hex)
    await set_position(guild, role)
    
  
def has_role(user, username):
  return get_role(user, username) is not None