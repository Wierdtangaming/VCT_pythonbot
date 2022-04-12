from sqlalchemy import text




def add_column_string(tabel_name, column_name, data_type, null, default=None):
  s = f"""ALTER TABLE {tabel_name} ADD COLUMN {column_name} {data_type}"""
  if not null:
    s += "\nNOT NULL"
  if default is not None:
    s += f"\nDEFAULT {default}"
  return s

def remove_column_string(tabel_name, column_name):
  return f"ALTER TABLE {tabel_name} DROP COLUMN {column_name}"

def alter_column_string(tabel_name, column_name, data_type, null, default=None):
  s = f"""
  CREATE TABLE temp_{tabel_name} (
  col_a INT
, col_b INT
);
"""
  if not null:
    s += "\nNOT NULL"
  if default is not None:
    s += f"\nDEFAULT {default}"
  return s


def try_remove_column(tabel_name, column_name, connection=None, engine=None):
  if connection is None:
    with engine.begin() as connection:
      return try_remove_column(tabel_name, column_name, connection)
  try:
    connection.execute(text(remove_column_string(tabel_name, column_name)))
    print("Column removed")
    return True
  except:
    print("Column not found")
    return False

def add_column(tabel_name, column_name, data_type, null, default=None, connection=None, engine=None):
  if connection is None:
    with engine.begin() as connection:
      return add_column(tabel_name, column_name, data_type, null, default, connection)
  try_remove_column(tabel_name, column_name, connection)
  connection.execute(text(add_column_string(tabel_name, column_name, data_type, null, default)))
  print("Column added")

