import discord
from colorinterface import hex_to_tuple


def get_role(user, username):
  return None
  roles = user.roles
  for role in roles:
    if role.name == f"Prediction {username}":
      return role
  return None

async def create_role(guild, username, hex, bot):
  return None
  role = await guild.create_role(name = f"Prediction {username}", color=discord.Color.from_rgb(*hex_to_tuple(hex)))
  await set_position(guild, role, bot)
  print(role.position)
  return role
  
  
async def set_position(guild, role, bot):  
  oroles = guild.roles
  user = bot.user
  for orole in oroles:
    if user in orole.members and not orole.is_default():
      await role.edit(position=orole.position-1)
  
async def add_role(user, role):
  await user.add_roles(role)

async def delete_role(role):
  await role.delete()
  
async def recolor_role(role, hex):
  await role.edit(color=discord.Color.from_rgb(*hex_to_tuple(hex)))
  
async def rename_role(role, new_name):
  await role.edit(name=new_name)

async def set_role(guild, author, username, hex, bot):
  return None
  role = get_role(author, username)
  if role is None:
    role = await create_role(guild, username, hex, bot)
    await add_role(author, role)
  else:
    await recolor_role(role, hex)

async def unset_role(author, username):
  role = get_role(author, username)
  if role is not None:
    await delete_role(role)
    
async def edit_role(author, username, hex):
  return None
  role = get_role(author, username)
  if role is not None:
    await recolor_role(role, hex)
  
async def set_role_name(author, username, new_name):
  role = get_role(author, username)
  if role is not None:
    await rename_role(role, new_name)
  
def has_role(user, username):
  return False
  return get_role(user, username) is not None