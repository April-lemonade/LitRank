import pandas as pd
import numpy as np
import duckdb
import pyarrow.parquet as pq
from fastapi import FastAPI, Query

app = FastAPI()
base_path = './datasets/WomenWriting/'
table_names = [
    'poet', 'poem', 'poempoetlinks', 'work', 'region',
    'poetregionlinks', 'workpoemlinks', 'workpoetlinks'
]

allAuthorsRole = ['主要作者', '其他作者', '作者', '墓志詺作者', '像贊作者', '輓詞作者', '年譜作者', '傳記作者', '编輯',
                  '校閲', '題辭', '序作者', '校註者', '附記作者', '凡例作者', '跋作者']
includedAuthorsRole = ['主要作者', '其他作者', '作者', '墓志詺作者', '像贊作者', '輓詞作者', '年譜作者', '傳記作者']
editingAuthorsRole = ['编輯', '校閲', '題辭', '序作者', '校註者', '附記作者', '凡例作者', '跋作者']


def init_db():
    con = duckdb.connect()

    for table_name in table_names:
        file_path = f"{base_path}{table_name}.parquet"
        try:
            con.execute(f"CREATE VIEW {table_name} AS SELECT * FROM read_parquet('{file_path}');")
        except Exception as e:
            print(f"Failed to create view for {table_name}: {e}")
    return con


db_connection = init_db()


def get_poem_details(poemID):
    query = f'''SELECT *
    FROM poem
    WHERE poem.poemID = {poemID};'''
    result = db_connection.query(query).df()
    result.fillna(0, inplace=True)
    result_dict = result.to_dict(orient='records')
    return result_dict


def get_poet_details(poetID):
    query = f'''SELECT *
        FROM poet
        WHERE poet.poetID = {poetID};'''
    result = db_connection.query(query).df()
    result.fillna(0, inplace=True)
    result_dict = result.to_dict(orient='records')
    return result_dict


def get_work_details(workID):
    query = f'''SELECT *
            FROM work
            WHERE work.workID = {workID};'''
    result = db_connection.query(query).df()
    result.fillna(0, inplace=True)
    result_dict = result.to_dict(orient='records')
    return result_dict


def get_poem_poet(poemID):
    query = f'''SELECT poetID
                FROM poempoetlinks
                WHERE poemID = {poemID};'''
    result = db_connection.query(query).df()
    # result.fillna(0, inplace=True)
    # result_dict = result.to_dict(orient='records')
    return result['poetID'][0]


def get_poem_work(poemID):
    query = f'''SELECT workID
                FROM workpoemlinks
                WHERE poemID = {poemID};'''
    result = db_connection.query(query).df()
    # result.fillna(0, inplace=True)
    # result_dict = result.to_dict(orient='records')
    return result['workID'][0]


def get_work_poems(workID):
    query = f'''SELECT poemID
                FROM workpoemlinks
                WHERE workID = {workID};'''
    result = db_connection.query(query).df()
    result.fillna(-1, inplace=True)
    result_list = result['poemID'].tolist()
    return result_list


def get_poet_poems_by_work(poetID, workID):
    query = f'''SELECT poempoetlinks.poemID
                FROM poempoetlinks
                Inner JOIN workpoemlinks ON poempoetlinks.poemID = workpoemlinks.poemID
                WHERE poempoetlinks.poetID = {poetID} AND workpoemlinks.workID={workID};'''
    result = db_connection.query(query).df()
    result_list = result['poemID'].tolist()
    return result_list


@app.get("/{workID}", summary="获取集的详细信息，包括其中作者，以及作者在这个集中的品的id")
def get_work_full(workID: str):
    poetsInfo = []
    poets = get_work_poets(workID)
    poet_ids = [item['poetID'] for item in poets if 'poetID' in item]

    # print(poet_ids)
    for poet_id in poet_ids:
        poems = get_poet_poems_by_work(poet_id, workID)
        poetsInfo.append({'poetInfo': get_poet_details(poet_id), 'poemsID': poems})
    result = {'workInfo': get_work_details(workID), 'poetsInfo': poetsInfo}
    return result


@app.get("/work/getpoemsid/{workID}", summary='获得集中的作品')
def getWorkPoemsID(workID: str):
    query = '''
            SELECT poemID
            FROM workpoemlinks
            WHERE workID = ?
        '''
    result = db_connection.query(query, params=(workID,)).df()
    # result_dict = result.to_dict(orient='records')
    result_list = result['poemID'].tolist()
    return result_list


@app.get("/poem/{poemID}", summary="品的详细信息，包括作者和集的所有信息")
def get_poem_full(poemID: str):
    final = {'poemInfo': get_poem_details(poemID), 'poetInfo': get_poet_details(get_poem_poet(poemID)),
             'workInfo': get_work_details(get_poem_work(poemID))}
    return final


@app.get("/work/getpoetsid/{workID}", summary="获取集中收录作品的作者ID")
def get_work_poets(workID: str, role: str = Query('all', description="included/editing，为空默认为all")):
    # print("Requested workID:", workID)
    roleType = allAuthorsRole
    if role == 'included': roleType = includedAuthorsRole
    if role == 'editing': roleType = editingAuthorsRole

    query = f'''
        SELECT poetID, role
        FROM workpoetlinks
        WHERE workID = ? AND role In {roleType}

    '''
    result = db_connection.query(query, params=(workID,)).df()
    result_dict = result.to_dict(orient='records')
    # result_list = result['poetID'].tolist()
    return result_dict
