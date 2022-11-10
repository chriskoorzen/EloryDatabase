# {table_name: {column_name: column_definition}}
tables = {"files":
              {"file_id": "INTEGER PRIMARY KEY",
               "file_path": "TEXT UNIQUE NOT NULL",
               "file_hash_name": "TEXT UNIQUE NOT NULL"},
          "tag_groups":
              {"group_id": "INTEGER PRIMARY KEY",
               "group_name": "TEXT UNIQUE NOT NULL"},
          "tags":
              {"tag_id": "INTEGER PRIMARY KEY",
               "tag_name": "TEXT NOT NULL",
               "tag_group": "INTEGER NOT NULL",
               "FOREIGN KEY(tag_group)": "REFERENCES tag_groups(group_id) ON DELETE RESTRICT ON UPDATE CASCADE",
               "UNIQUE(tag_name, tag_group)": "ON CONFLICT FAIL"},
          "tagged_files_m2m":
              {"tag": "INTEGER",
               "file": "INTEGER",
               "FOREIGN KEY(tag)": "REFERENCES tags(tag_id) ON DELETE RESTRICT ON UPDATE CASCADE",
               "FOREIGN KEY(file)": "REFERENCES files(file_id) ON DELETE RESTRICT ON UPDATE CASCADE",
               "UNIQUE(tag, file)": "ON CONFLICT FAIL"}
          }

tableTemplate = "BEGIN;\n"                                      # SQL script start
for table in tables.keys():
    tableTemplate += f"CREATE TABLE {table}"                    # Open Table definition
    tableTemplate += "("                                        # Open column definitions
    for column in tables[table].keys():
        tableTemplate += f"{column} {tables[table][column]}"    # Add column and constraints
        tableTemplate += ", "                                   # split column definitions
    tableTemplate = tableTemplate.rstrip(", ")                  # remove last split
    tableTemplate += ");\n"                                     # close column definitions, close table definition
tableTemplate += "COMMIT;\n"                                    # SQL script end
