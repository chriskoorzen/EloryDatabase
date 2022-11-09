'''
Project Elory: elephant memory
Tag and index personal media files
Author chriskoorzendev@gmail.com
All Rights Reserved.
'''
# TODO - Handle sqlite Integrity errors for failed UNIQUE constraints ("add" functions)
# TODO - Give a better info message for failed lookups on "link" and "unlink" (_get_rowid helper function)

import sqlite3

DB_NAME = "elory.db"
CONNECTION = ''
CURSOR = ''


# Test Data
def quick_run():
    file_list = ['/root/2019/20191213/vid_007.mp4', '/root/2019/20191213/voice001.mp3', '/root/2019/20191106/img_1234.jpg', '/root/2019/20191106/img_56.jpg', '/root/2020/20200605/voice008.mp3', '/root/2020/20200307/img_8898.jpg', '/root/2020/20200809/img_009.jpg', '/root/2020/20200809/vid_778.mp4', '/root/2020/20200809/journal_20200809.txt']
    init_database()
    add_many_files('root')
    add_tag_group('People')
    add_tag_group('Places')
    add_tag_group('Ideals')
    add_tag('Jack', 'People')
    add_tag('Samantha', 'People')
    add_tag('Lee', 'People')
    add_tag('New York', 'Places')
    add_tag('Cape Town', 'Places')
    add_tag('Tokyo', 'Places')
    add_drive('BckUp_Mk_I')
    add_drive('BckUp_Mk_II')
    for i in file_list:
        link_file_to_drive('BckUp_Mk_I', i)
        link_file_to_drive('BckUp_Mk_II', i)
    for i in range(len(file_list)):
        if i < 3:
            link_tag_to_filename('Jack', file_list[i])
            link_tag_to_filename('Tokyo', file_list[i])
            continue
        elif i < 6:
            link_tag_to_filename('Samantha', file_list[i])
            link_tag_to_filename('New York', file_list[i])
            continue
        elif i < 9:
            link_tag_to_filename('Lee', file_list[i])
            link_tag_to_filename('Cape Town', file_list[i])
            continue


# Connection function. Get db ready for use (boilerplate)
def connect(db_name=DB_NAME):
    global CONNECTION, CURSOR
    CONNECTION = sqlite3.connect(db_name)
    CURSOR = CONNECTION.cursor()
    CURSOR.execute("PRAGMA foreign_keys = ON")      # Enforce Foreign Key constraints
    CONNECTION.commit()


# Setup function to create database structure
def init_database():
    # try:
    CURSOR.executescript(
        '''BEGIN;
        CREATE TABLE filenames(file_id INTEGER PRIMARY KEY, file_path TEXT UNIQUE NOT NULL);
        CREATE TABLE drives(drive_id INTEGER PRIMARY KEY, drive_name TEXT UNIQUE NOT NULL);
        CREATE TABLE tag_groups(group_id INTEGER PRIMARY KEY, group_name TEXT UNIQUE NOT NULL);
        CREATE TABLE tags(tag_id INTEGER PRIMARY KEY, tag_name TEXT NOT NULL, tag_group INTEGER NOT NULL, FOREIGN KEY(tag_group) REFERENCES tag_groups(group_id) ON DELETE RESTRICT ON UPDATE CASCADE, UNIQUE(tag_name, tag_group) ON CONFLICT FAIL);
        CREATE TABLE drive_filenames_m2m(drive INTEGER, filepath INTEGER, FOREIGN KEY(drive) REFERENCES drives(drive_id) ON DELETE RESTRICT ON UPDATE CASCADE, FOREIGN KEY(filepath) REFERENCES filenames(file_id) ON DELETE RESTRICT ON UPDATE CASCADE, UNIQUE(drive, filepath) ON CONFLICT FAIL);
        CREATE TABLE tag_filenames_m2m(tag INTEGER, file INTEGER, FOREIGN KEY(tag) REFERENCES tags(tag_id) ON DELETE RESTRICT ON UPDATE CASCADE, FOREIGN KEY(file) REFERENCES filenames(file_id) ON DELETE RESTRICT ON UPDATE CASCADE, UNIQUE(tag, file) ON CONFLICT FAIL);
        COMMIT;
        '''
    )
    print("Tables successfully created")
    # except sqlite3.OperationalError:
    #     print("One or more tables with the same name already exists.\nOperation Aborted.")


# Helper function for retrieving rowid's
def _get_rowid(id_name, table, col, arg):
    CURSOR.execute(
        f'''SELECT {id_name} FROM {table} WHERE {col}="{arg}"'''
    )
    result = CURSOR.fetchall()
    if len(result) == 0 or len(result) > 1:
        print("Unable to retrieve unique rowid for arguments")
        return None
    return result[0][0]


# Add filename. Must conform to convention: ~/root/[yyyy]/[specific date - can be yyyymmdd, yyyymm, yyyy]/[filename]
def add_filename(filepath):
    def errmsg():
        print(f"{filepath} is not a valid filepath.\nFilepath must conform to the following pattern: /root/[yyyy]/[yyyy | yyyymm | yyyymmdd]/[filename].\nOperation Aborted.")

    check = filepath.split('/')
    try:
        int(check[2])
        int(check[3])
    except (ValueError, IndexError) as e:
        errmsg()
        return
    if len(check) != 5:
        errmsg()
        return
    elif check[1] != 'root':
        errmsg()
        return
    elif len(check[2]) != 4:
        errmsg()
        return
    else:
        try:
            CURSOR.execute(
                f'''INSERT INTO filenames (file_path) VALUES ("{filepath}")'''
            )
            CONNECTION.commit()
            print(f"Successfully added {filepath} to database")
        except sqlite3.IntegrityError:
            print(f"{filepath} already exists. Skipping...")


# Helper function - add entire directory of files from "root" folder. Complain if non-conforming.
def add_many_files(dir_root='root'):
    if dir_root != 'root':
        print("Top level directory must be named 'root'.")
        print("Filepath must conform to the following pattern: /root/[yyyy]/[yyyy | yyyymm | yyyymmdd]/[filename].\nOperation Aborted.")
        return

    def add_files(tup):
        # expecting os.walk tuple: ('root/level_1/level_2', [list of sub_dirs (ignore)], [list of files])
        # Skip subdirectories
        for sub_dir in range(len(tup[1])):
            print(f"Skipping subdirectory {tup[0] + '/' + tup[1][sub_dir]} ")
        tup[1].clear()
        # Add files to database
        for file in range(len(tup[2])):
            add_filename('/' + tup[0] + '/' + tup[2][file])
            # print("added file: " + '/' + tup[0] + '/' + tup[2][file])

    def filter_level_2_directories(tup):
        # expecting os.walk tuple: ('current dir', [list of dirs], [list of files (ignore)])
        # Warn about out-of-place files
        for file in tup[2]:
            print(f"Ignoring file {tup[0] + '/' + file}")
        # Filter out non-conformant directories
        non_con = []
        for sub_dir in range(len(tup[1])):
            try:
                # print(tup)
                int(tup[1][sub_dir])
            except ValueError:
                print(f"Skipping subdirectory {tup[0] + '/' + tup[1][sub_dir]} ")
                non_con.append(tup[1][sub_dir])
        for i in non_con:
            tup[1].remove(i)

    def filter_level_1_directories(tup):
        # expecting os.walk tuple: ('current dir', [list of dirs], [list of files (ignore)])
        filter_level_2_directories(tup)     # Same basic function
        non_con = []
        for sub_dir in range(len(tup[1])):
            if len(tup[1][sub_dir]) != 4:
                print(f"Skipping subdirectory {tup[0] + '/' + tup[1][sub_dir]} ")
                non_con.append(tup[1][sub_dir])
        for i in non_con:
            tup[1].remove(i)

    # Start function
    from os import walk
    gen = walk(dir_root)

    tree = gen.send(None)
    filter_level_1_directories(tree)

    try:
        for lvl_1_sub_dir in tree[1]:
            branch = gen.send(None)
            filter_level_2_directories(branch)

            for lvl_2_sub_dir in branch[1]:
                node = gen.send(None)
                add_files(node)

        # Debug lines
        b = gen.send(None)
        print(b)
    except StopIteration:
        print("Generator exhausted.")


def list_all_files():
    CURSOR.execute(
        '''SELECT file_path FROM filenames'''
    )
    result = []
    for i in CURSOR.fetchall():
        result.append(i[0])
    return tuple(result)


# Add tag_group
def add_tag_group(tag_group_name):
    # try:
    CURSOR.execute(
        f'''INSERT INTO tag_groups (group_name) VALUES ("{tag_group_name}")'''
    )
    CONNECTION.commit()
    print(f"Successfully added {tag_group_name} to database")
    # except sqlite3.IntegrityError:
    #     print("Tag Group already exists. Abort Operation.")


# Modify tag_group name
def rename_tag_group(old_name, new_name):
    CURSOR.execute(
        f'''UPDATE tag_groups SET group_name="{new_name}" WHERE group_name="{old_name}"'''
    )
    CONNECTION.commit()
    success = CURSOR.rowcount
    if success:
        print(f'Successfully changed Group Name from "{old_name}" to "{new_name}"')
    else:
        print('Nothing done')


def list_all_tag_groups():
    CURSOR.execute(
        '''SELECT group_name FROM tag_groups'''
    )
    result = []
    for i in CURSOR.fetchall():
        result.append(i[0])
    return tuple(result)


# Add tag
def add_tag(tag_name, tag_group):
    # try:
    group_id = _get_rowid('group_id', 'tag_groups', 'group_name', tag_group)
    if group_id is None:
        return
    CURSOR.execute(
        f'''INSERT INTO tags (tag_name, tag_group) VALUES ("{tag_name}", {group_id})'''
    )
    CONNECTION.commit()
    print(f'Successfully added tag "{tag_name}" of group "{tag_group}" to database')
    # except sqlite3.IntegrityError:
    #     print("Tag already exists. Abort Operation.")


# Modify tag name
def rename_tag(old_name, new_name):
    CURSOR.execute(
        f'''UPDATE tags SET tag_name="{new_name}" WHERE tag_name="{old_name}"'''
    )
    CONNECTION.commit()
    success = CURSOR.rowcount
    if success:
        print(f'Successfully changed Tag Name from "{old_name}" to "{new_name}"')
    else:
        print('Nothing done')


def list_all_tags():
    CURSOR.execute(
        '''SELECT tag_name FROM tags'''
    )
    result = []
    for i in CURSOR.fetchall():
        result.append(i[0])
    return tuple(result)        # TODO add associated group to result


# Add drive
def add_drive(drive):
    # try:
    CURSOR.execute(
        f'''INSERT INTO drives (drive_name) VALUES ("{drive}")'''
    )
    CONNECTION.commit()
    print(f'Successfully added drive "{drive}" to database')

    # except sqlite3.IntegrityError:
    #     print("Drive already exists. Abort Operation.")


# Modify Drive name
def rename_drive(old_name, new_name):
    CURSOR.execute(
        f'''UPDATE drives SET drive_name="{new_name}" WHERE drive_name="{old_name}"'''
    )
    CONNECTION.commit()
    success = CURSOR.rowcount
    if success:
        print(f'Successfully changed Drive Name from "{old_name}" to "{new_name}"')
    else:
        print('Nothing done')


def list_all_drives():
    CURSOR.execute(
        '''SELECT drive_name FROM drives'''
    )
    result = []
    for i in CURSOR.fetchall():
        result.append(i[0])
    return tuple(result)


# Associate tag with filename
def link_tag_to_filename(tag, file):
    # try:
    tag_id = _get_rowid('tag_id', 'tags', 'tag_name', tag)
    file_id = _get_rowid('file_id', 'filenames', 'file_path', file)
    if tag_id is None or file_id is None:
        return
    CURSOR.execute(
        f'''INSERT INTO tag_filenames_m2m (tag, file) VALUES ({tag_id}, {file_id})'''
    )
    CONNECTION.commit()
    print(f"Successfully linked {tag} to {file}")

    # except sqlite3.IntegrityError:
    #     print("Link already exists. Abort Operation.")


# Dissociate tag with filename
def unlink_tag_from_filename(tag, file):
    tag_id = _get_rowid('tag_id', 'tags', 'tag_name', tag)
    file_id = _get_rowid('file_id', 'filenames', 'file_path', file)
    if tag_id is None or file_id is None:
        return
    CURSOR.execute(
        f'''DELETE FROM tag_filenames_m2m WHERE tag={tag_id} AND file={file_id}'''
    )
    CONNECTION.commit()
    success = CURSOR.rowcount
    if success:
        print(f'Successfully unlinked tag "{tag}" from file "{file}"')
    else:
        print('Nothing done')


# Associate drive to filename
def link_file_to_drive(drive, filepath):
    # try:
    drive_id = _get_rowid('drive_id', 'drives', 'drive_name', drive)
    file_id = _get_rowid('file_id', 'filenames', 'file_path', filepath)
    if drive_id is None or file_id is None:
        return
    CURSOR.execute(
        f'''INSERT INTO drive_filenames_m2m (drive, filepath) VALUES ({drive_id}, {file_id})'''
    )
    CONNECTION.commit()
    print(f'Successfully linked drive "{drive}" to file "{filepath}"')

    # except sqlite3.IntegrityError:
    #     print("Link already exists. Abort Operation.")


# Dissociate drive from filename
def unlink_file_from_drive(drive, filepath):
    drive_id = _get_rowid('drive_id', 'drives', 'drive_name', drive)
    file_id = _get_rowid('file_id', 'filenames', 'file_path', filepath)
    if drive_id is None or file_id is None:
        return
    CURSOR.execute(
        f'''DELETE FROM drive_filenames_m2m WHERE drive={drive_id} AND filepath={file_id}'''
    )
    CONNECTION.commit()
    success = CURSOR.rowcount
    if success:
        print(f'Successfully unlinked drive "{drive}" from "{filepath}"')
    else:
        print('Nothing done')


# Retrieve filenames where [drive]
def list_files_by_drive(drive):
    drive_id = _get_rowid('drive_id', 'drives', 'drive_name', drive)
    if drive_id is None:
        return
    CURSOR.execute(
        f'''SELECT filepath FROM drive_filenames_m2m WHERE drive={drive_id}'''
    )
    res = CURSOR.fetchall()
    result = []
    for i in res:
        CURSOR.execute(
            f'''SELECT ALL file_path FROM filenames WHERE file_id={i[0]}'''
        )
        result.append(CURSOR.fetchall()[0][0])
    return tuple(result)


# TODO add filter function to find "file" with specified tags
# Retrieve filenames where [tag]
def list_files_by_tag(tag):
    tag_id = _get_rowid('tag_id', 'tags', 'tag_name', tag)
    if tag_id is None:
        return
    CURSOR.execute(
        f'''SELECT file FROM tag_filenames_m2m WHERE tag={tag_id}'''
    )
    res = CURSOR.fetchall()
    result = []
    for i in res:
        CURSOR.execute(
            f'''SELECT ALL file_path FROM filenames WHERE file_id={i[0]}'''
        )
        result.append(CURSOR.fetchall()[0][0])
    return tuple(result)


# Retrieve tags where [filename]
def list_tags_of_file(file):
    file_id = _get_rowid('file_id', 'filenames', 'file_path', file)
    if file_id is None:
        return
    CURSOR.execute(
        f'''SELECT tag FROM tag_filenames_m2m WHERE file={file_id}'''
    )
    res = CURSOR.fetchall()
    result = []
    for i in res:
        CURSOR.execute(
            f'''SELECT ALL tag_name FROM tags WHERE tag_id={i[0]}'''
        )
        result.append(CURSOR.fetchall()[0][0])
    return tuple(result)


# Retrieve drives where [filepath]
def list_drives_of_file(file):
    file_id = _get_rowid('file_id', 'filenames', 'file_path', file)
    if file_id is None:
        return
    CURSOR.execute(
        f'''SELECT drive FROM drive_filenames_m2m WHERE filepath={file_id}'''
    )
    res = CURSOR.fetchall()
    result = []
    for i in res:
        CURSOR.execute(
            f'''SELECT drive_name FROM drives WHERE drive_id={i[0]}'''
        )
        result.append(CURSOR.fetchall()[0][0])
    return tuple(result)


# Helper function - Check if file exists for [filename] entry - unlink stale entries
# Helper function - Alert if [filename] is not associated with any tags
# Helper function - Alert if [filename] is not associated with any drives
# Helper function - Associate multiple files (in a directory) to a drive
