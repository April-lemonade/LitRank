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

wen_keywords = ['文%', '%詩話%', '%略傳%', '%對聯%']
tu_keywords = ['照片', '圖']


# shiForms = []
# wenForms = []
# cipaiming = []
# qupaiming = []


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


@app.get('/poem/{poemID}', summary='获取单独的诗歌详情')
def get_poem_details(poemID):
    query = f'''SELECT *
    FROM poem
    WHERE poem.poemID = {poemID};'''
    result = db_connection.query(query).df()
    result.fillna(0, inplace=True)
    result_dict = result.to_dict(orient='records')
    return result_dict


@app.get('/poet/{poetID}', summary='获取单独的诗人详情')
def get_poet_details(poetID):
    query = f'''SELECT *
        FROM poet
        WHERE poet.poetID = {poetID};'''
    result = db_connection.query(query).df()
    result.fillna(0, inplace=True)
    result_dict = result.to_dict(orient='records')
    return result_dict


@app.get('/work/{workID}', summary='获取单独的集的详情')
def get_work_details(workID):
    query = f'''SELECT *
            FROM work
            WHERE work.workID = {workID};'''
    result = db_connection.query(query).df()
    result.fillna(0, inplace=True)
    result_dict = result.to_dict(orient='records')
    return result_dict


@app.get('/getpoempoet/{poemID}', summary='根据品id查询作者id')
def get_poem_poet(poemID):
    # print(poemID)
    query = f'''SELECT poetID
                FROM poempoetlinks
                WHERE poemID = {poemID};'''
    result = db_connection.query(query).df()
    # print(result['poetID'][0])
    # result.fillna(0, inplace=True)
    # result_dict = result.to_dict(orient='records')
    return int(result['poetID'][0])


@app.get('/getpoemwork/{workID}', summary='根据品id查询集id')
def get_poem_work(poemID):
    query = f'''SELECT workID
                FROM workpoemlinks
                WHERE poemID = {poemID};'''
    result = db_connection.query(query).df()
    # result.fillna(0, inplace=True)
    # result_dict = result.to_dict(orient='records')
    return int(result['workID'][0])


@app.get('/work/{workID}/{poetID}', summary='获取某个集中某个作者的品的id;举例work38,poet274')
def get_poet_poems_by_work(poetID, workID):
    query = f'''SELECT poempoetlinks.poemID
                FROM poempoetlinks
                Inner JOIN workpoemlinks ON poempoetlinks.poemID = workpoemlinks.poemID
                WHERE poempoetlinks.poetID = {poetID} AND workpoemlinks.workID={workID};'''
    result = db_connection.query(query).df()
    result_list = result['poemID'].tolist()
    return result_list


@app.get("/workFull/{workID}", summary="获取集的详细信息，包括其中作者，以及作者在这个集中的品的id")
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


@app.get("/getworkpoems/{workID}", summary='获得集中的品ID')
def get_work_poem(workID: str):
    print(workID)
    query = f'''
            SELECT DISTINCT workpoemlinks.poemID
            FROM workpoemlinks
            WHERE workpoemlinks.workID = {workID}
        '''
    result = db_connection.query(query).df()
    # result_dict = result.to_dict(orient='records')
    result_list = result['poemID'].tolist()
    # print(result_list)
    return result_list


@app.get("/poemFull/{poemID}", summary="品的详细信息，包括作者和集的所有信息")
def get_poem_full(poemID: str):
    final = {'poemInfo': get_poem_details(poemID), 'poetInfo': get_poet_details(get_poem_poet(poemID)),
             'workInfo': get_work_details(get_poem_work(poemID))}
    return final


@app.get("/getworkpoetsid/{workID}", summary="获取集中收录作品的作者ID,按收录或者参与编辑或者完整")
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


@app.get("/getpoetworkincluded/{poetID}", summary="获取作者被收录的集id")
def get_poet_work(poetID: str):
    query = f'''
            SELECT DISTINCT workID
            FROM workpoetlinks
            WHERE poetID = {poetID} AND role In {includedAuthorsRole}
        '''
    result = db_connection.query(query).df()
    # result_dict = result.to_dict(orient='records')
    result_list = result['workID'].tolist()
    return result_list


@app.get("/getpoetworkediting/{poetID}", summary="获取作者参与编辑的集id")
def get_poet_work(poetID: str):
    query = f'''
            SELECT DISTINCT workID
            FROM workpoetlinks
            WHERE poetID = {poetID} AND role In {editingAuthorsRole}
        '''
    result = db_connection.query(query).df()
    # result_dict = result.to_dict(orient='records')
    result_list = result['workID'].tolist()
    return result_list


@app.get("/getgenre1", summary='获取一级分类和数量统计')
def get_genre():
    wen_conditions = " OR ".join([f"genreHZ LIKE '{kw}'" for kw in wen_keywords])
    tu_conditions = " OR ".join([f"genreHZ = '{kw}'" for kw in tu_keywords])

    query = f'''
               SELECT
            CASE
                WHEN {wen_conditions} THEN '文'
                WHEN {tu_conditions} THEN '圖'
                ELSE genreHZ          
            END AS genre_group,
            COUNT(*) AS num_poems
        FROM poem
        GROUP BY genre_group
        ORDER BY num_poems DESC
            '''
    result = db_connection.query(query).df()
    result_dict = result.to_dict(orient='records')
    # result_list = result['genreHZ'].tolist()
    return result_dict


@app.get("/getgenre2/{genre}", summary='根据一级分类获取二级分类和数量统计')
def get_genre(genre):
    columnName = ''
    genreName = ''
    if genre in ['詩', '诗']:
        columnName = 'Form'
        genreName = '詩'
    elif genre in ['詞', '词']:
        columnName = 'TitleHZ'
        genreName = '詞'
    elif genre in ['曲']:
        columnName = '曲'
        genreName = '曲'
    elif genre in ['文']:
        columnName = 'GenreHZ'
        genreName = '文'
    query = f'''
            SELECT {columnName},COUNT(*) AS count
            FROM poem
            WHERE genreHZ Like '{genreName}%'
            GROUP BY {columnName}
            '''
    result = db_connection.query(query).df()
    result_dict = result.to_dict(orient='records')
    # result_list = result['genreHZ'].tolist()
    return result_dict
