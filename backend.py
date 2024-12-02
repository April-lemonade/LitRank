import duckdb
import numpy as np
import pandas as pd
from fastapi import FastAPI, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from zhconv import convert
import re  # 引入正则表达式模块

app = FastAPI()
origins = [
    "http://localhost:5173",  # 您前端的源地址
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许来自特定源的请求
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部信息
)
base_path = './datasets/WomenWriting/'
table_names = [
    'poet', 'poem', 'poempoetlinks', 'work', 'region',
    'poetregionlinks', 'workpoemlinks', 'workpoetlinks', 'relation', 'region', 'cycle'
]

poet = pd.read_csv('./datasets/WomenWriting/poet.csv')
poem = pd.read_csv('./datasets/WomenWriting/poem.csv')
poempoetlinks = pd.read_csv('./datasets/WomenWriting/poempoetlinks.csv')
subwork = pd.read_csv('./datasets/WomenWriting/subwork.csv')
subworkpoemlinks = pd.read_csv('./datasets/WomenWriting/subworkpoemlinks.csv')
subworkpoetlinks = pd.read_csv('./datasets/WomenWriting/subworkpoetlinks.csv')
work = pd.read_csv('./datasets/WomenWriting/work.csv')
workpoemlinks = pd.read_csv('./datasets/WomenWriting/workpoemlinks.csv')
workpoetlinks = pd.read_csv('./datasets/WomenWriting/workpoetlinks.csv')
poetregionlinks = pd.read_csv('./datasets/WomenWriting/poetregionlinks.csv')
relation = pd.read_csv('./datasets/WomenWriting/relation.csv')
region = pd.read_csv('./datasets/WomenWriting/region.csv')
cycle = pd.read_csv('./datasets/WomenWriting/cycle.csv')

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

# 数据库连接依赖
def get_db_connection():
    # 每次调用都创建一个新的连接
    con = duckdb.connect(database=':memory:', read_only=False)
    # 假设所有的数据表都可以在内存中创建，或者从磁盘加载
    return con


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
def get_poem_details(poemID, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    query = f'''SELECT *
    FROM poem
    WHERE poem.poemID = {poemID};'''
    result = db_connection.query(query).df()
    result.fillna(0, inplace=True)
    result_dict = result.to_dict(orient='records')
    return result_dict


@app.get('/poet/{poetID}', summary='获取单独的诗人详情')
def get_poet_details(poetID, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    db_connection = get_db_connection()
    query = f'''SELECT *
        FROM poet
        WHERE poet.poetID = {poetID};'''
    result = db_connection.query(query).df()
    result.fillna(0, inplace=True)
    result_dict = result.to_dict(orient='records')
    return result_dict


@app.get('/work/{workID}', summary='获取单独的集的详情')
def get_work_details(workID, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    db_connection = get_db_connection()
    query = f'''SELECT *
            FROM work
            WHERE work.workID = {workID};'''
    result = db_connection.query(query).df()
    result.fillna(0, inplace=True)
    result_dict = result.to_dict(orient='records')
    return result_dict


@app.get('/getpoempoet/{poemID}', summary='根据品id查询作者id')
def get_poem_poet(poemID, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
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
def get_poem_work(poemID, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    query = f'''SELECT workID
                FROM workpoemlinks
                WHERE poemID = {poemID};'''
    result = db_connection.query(query).df()
    # result.fillna(0, inplace=True)
    # result_dict = result.to_dict(orient='records')
    return int(result['workID'][0])


@app.get('/work/{workID}/{poetID}', summary='获取某个集中某个作者的品的id;举例work38,poet274')
def get_poet_poems_by_work(poetID, workID, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    db_connection = get_db_connection()
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

    poet_ids = get_work_poets(workID)
    # poet_ids = [item['poetID'] for item in poets]

    # print(poet_ids)
    for poet_id in poet_ids:
        poems = get_poet_poems_by_work(poet_id, workID)
        poetsInfo.append({'poetInfo': get_poet_details(poet_id), 'poemsID': poems})
    result = {'workInfo': get_work_details(workID), 'poetsInfo': poetsInfo}
    return result


@app.get("/getworkpoems/{workID}", summary='获得集中的品ID')
def get_work_poem(workID: str, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    # print(workID)
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


def get_work_poets_inner(workID: str):
    # print("Requested workID:", workID)
    roleType = allAuthorsRole

    query = f'''
        SELECT poetID, role
        FROM workpoetlinks
        WHERE workID = {workID} AND role In {roleType}

    '''
    result = db_connection.query(query).df()
    result_dict = result.to_dict(orient='records')
    # result_list = result['poetID'].tolist()
    return result_dict


@app.get("/getworkpoetsid/{workID}")
def get_work_poets(workID):
    # print("Requested workID:", workID)
    db_connection = get_db_connection()
    roleType = allAuthorsRole
    # if role == 'included': roleType = includedAuthorsRole
    # if role == 'editing': roleType = editingAuthorsRole

    query = f'''
        SELECT poetID
        FROM workpoetlinks
        WHERE workID = {workID}
    '''
    result = db_connection.query(query).df()
    # result_dict = result.to_dict(orient='records')
    result_list = result['poetID'].tolist()
    # print(result_list)
    return result_list


@app.get("/getpoetwork/{poetID}", summary="获取作者的集id")
def get_poet_work(poetID: str, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    query = f'''
            SELECT workID,titleHZ,role
            FROM relation
            WHERE poetID = {poetID}
        '''
    result = db_connection.query(query).df()
    result_dict = result.to_dict(orient='records')
    # result_list = result['workID'].tolist()
    return result_dict


@app.get("/getpoetworkediting/{poetID}", summary="获取作者参与编辑的集id")
def get_poet_work(poetID: str, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
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
def get_genre(db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
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
def get_genre(genre, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
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


@app.get('/workYear', summary='获取work的年份分布')
def workYearDistribution(db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    query = """
    SELECT
        FLOOR((PubStartYear - 1600) / 40) * 40 + 1600 AS StartYearRange,
        COUNT(*) AS Count,
        STRING_AGG(CAST(workID AS CHAR ), ',') AS WorkIDs
    FROM
        work
    WHERE
        PubStartYear IS NOT NULL AND PubStartYear BETWEEN 1600 AND 1960
    GROUP BY
        StartYearRange
    ORDER BY
        StartYearRange
    """
    result = db_connection.query(query).df()
    result['StartYearRange'] = result['StartYearRange'].astype(int).astype(str) + '-' + \
                               (result['StartYearRange'] + 39).astype(int).astype(str)
    result['WorkIDs'] = result['WorkIDs'].apply(lambda x: x.split(','))

    result_dict = result.to_dict(orient='records')
    return result_dict


def min_max_normalize(series):
    return (series - series.min()) / (series.max() - series.min()) * 100


def safe_float(value, default=0.0):
    try:
        if pd.isna(value) or abs(value) == float('inf'):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


workRank = pd.DataFrame()
workRankNew = pd.DataFrame()


@app.get('/workImportanceNew/{workPara}')
def calWorkImportanceNew(workPara, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    global poetRankNew
    workPara = workPara.split(',')
    mainWeight = float(workPara[0])
    secondWeight = float(workPara[1])
    editorWeight = float(workPara[2])

    role_weights = {
        '主要作者': mainWeight, '作者': mainWeight, '其他作者': mainWeight,
        '題辭': secondWeight, '序作者': secondWeight, '跋作者': secondWeight, '附记作者': secondWeight,
        '凡例作者': secondWeight, '墓志詺作者': secondWeight, '輓詞作者': secondWeight, '傳記作者': secondWeight,
        '像赞作者': secondWeight, '年譜作者': secondWeight,
        '编輯': editorWeight, '校閲': editorWeight, '校注者': editorWeight
    }
    workpoet = workpoetlinks.copy()
    workpoet['RoleWeight'] = workpoet['role'].map(role_weights)
    workpoet = workpoet.merge(poetRankNew, on='poetID', how='outer')
    workpoet['WorkImportance'] = workpoet['RoleWeight'] * workpoet['totalWeight']
    work_importance_total = workpoet.groupby('workID')['WorkImportance'].sum()
    max_importance = work_importance_total.max()
    normalized_importance = work_importance_total / max_importance
    normalized_importance_df = normalized_importance.reset_index()
    raw_importance = normalized_importance_df.copy()
    normalized_importance_df = normalized_importance_df.merge(work, on='workID', how='outer')[
        ['workID', 'TitleHZ', 'PubStartYear', 'WorkImportance']]
    normalized_importance_df['WorkImportance'] = np.log(normalized_importance_df['WorkImportance'] + 0.01)

    normalized_importance_sorted = normalized_importance_df.sort_values('WorkImportance', ascending=False)
    normalized_importance_sorted.set_index('workID', inplace=True)

    global workRankNew  # 确保 workRank 是全局变量

    workRankNew = normalized_importance_df.copy()

    columns_to_exclude = ['Summary', 'UniformTitle', 'VariantTitle']
    columns_to_exclude += [col for col in work.columns if 'PY' in col]
    columns_to_check = [col for col in work.columns if col not in columns_to_exclude]
    columns_to_select = ', '.join(columns_to_check)

    work.fillna('unknown', inplace=True)
    workDetailsQuery = f"SELECT {columns_to_select} FROM work WHERE workID IN ({','.join(map(str, normalized_importance_sorted.index.tolist()))})"
    workDetails = db_connection.query(workDetailsQuery).df().set_index('workID')

    # 整合结果
    combined_results = []
    for workID, row in normalized_importance_sorted.iterrows():
        work_detail = {}
        if workID in workDetails.index:
            work_detail = workDetails.loc[workID].to_dict()

        combined = {
            'workID': int(workID),
            'workCount': row.dropna().to_dict(),  # 这里使用 dropna() 移除任何NaN值，确保所有值都是JSON兼容的
            'workDetail': work_detail
        }
        combined_results.append(combined)
        # print(combined_results)
    return JSONResponse(content={"data": combined_results})
    # return ji_min_max_sorted.to_json(orient='index')


@app.get('/workImportance/{workPara}', response_class=JSONResponse)
def calWorkImportance(workPara, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    workPara = workPara.split(',')
    tici = db_connection.query(
        "SELECT workID, COUNT(DISTINCT poetID) AS ticicount FROM workpoetlinks WHERE role='題辭' GROUP BY workID").df()
    # print(tici)
    xu = db_connection.query(
        "SELECT workID, COUNT(DISTINCT poetID) AS xucount FROM workpoetlinks WHERE role='序作者' GROUP BY workID").df()
    ba = db_connection.query(
        "SELECT workID, COUNT(DISTINCT poetID) AS bacount FROM workpoetlinks WHERE role='跋作者' GROUP BY workID").df()
    includedWork = db_connection.query(
        "SELECT workID, COUNT(poemID) AS includedcount FROM workpoemlinks GROUP BY workID").df()

    tici.set_index('workID', inplace=True)
    xu.set_index('workID', inplace=True)
    ba.set_index('workID', inplace=True)
    includedWork.set_index('workID', inplace=True)

    # 合并数据
    jiRawData = pd.concat([tici, xu, ba, includedWork], axis=1).fillna(0)
    # 归一化
    for column in jiRawData.columns:
        jiRawData[column] = min_max_normalize(jiRawData[column])
    xuweight = float(workPara[1])
    baweight = float(workPara[2])
    ticiweight = float(workPara[0])
    includedweight = float(workPara[3])
    ji_min_max = jiRawData.copy()
    ji_min_max['ticiCalc'] = ticiweight * ji_min_max['ticicount']
    ji_min_max['xuCalc'] = xuweight * ji_min_max['xucount']
    ji_min_max['baCalc'] = baweight * ji_min_max['bacount']
    ji_min_max['includedCalc'] = includedweight * ji_min_max['includedcount']
    ji_min_max['totalWeight'] = ji_min_max['ticiCalc'] + ji_min_max['xuCalc'] + ji_min_max['baCalc'] + ji_min_max[
        'includedCalc']
    # ji_min_max['totalWeight'] = xuweight * ji_min_max['xucount'] + baweight * ji_min_max['bacount'] + ticiweight * \
    #                             ji_min_max['ticicount'] + includedweight * ji_min_max['includedcount']
    ji_min_max_sorted = ji_min_max.sort_values('totalWeight', ascending=False)
    global workRank  # 确保 workRank 是全局变量

    workRank = ji_min_max_sorted.copy()
    # 获取workDetail

    columns_to_exclude = ['Summary', 'UniformTitle', 'VariantTitle']
    columns_to_exclude += [col for col in work.columns if 'PY' in col]
    columns_to_check = [col for col in work.columns if col not in columns_to_exclude]
    columns_to_select = ', '.join(columns_to_check)

    work.fillna('unknown', inplace=True)
    workDetailsQuery = f"SELECT {columns_to_select} FROM work WHERE workID IN ({','.join(map(str, ji_min_max_sorted.index.tolist()))})"
    workDetails = db_connection.query(workDetailsQuery).df().set_index('workID')

    # 整合结果
    combined_results = []
    for workID, row in ji_min_max_sorted.iterrows():
        work_detail = {}
        if workID in workDetails.index:
            work_detail = workDetails.loc[workID].to_dict()

        combined = {
            'workID': int(workID),
            'workCount': row.dropna().to_dict(),  # 这里使用 dropna() 移除任何NaN值，确保所有值都是JSON兼容的
            'workDetail': work_detail
        }
        combined_results.append(combined)
        # print(combined_results)
    return JSONResponse(content={"data": combined_results})
    # return ji_min_max_sorted.to_json(orient='index')


@app.get('/getAllWorkID')
def getAllWorkID():
    db_connection = get_db_connection()
    query = """
            SELECT workpoemlinks.workID, 
                   group_concat(DISTINCT workpoetlinks.poetID, ',') AS poetIDs, 
                   group_concat(DISTINCT workpoemlinks.poemID, ',') AS poemIDs
            FROM workpoemlinks
            JOIN workpoetlinks ON workpoemlinks.workID = workpoetlinks.workID
            GROUP BY workpoemlinks.workID
        """

    result = db_connection.query(query).df()
    result_dict = result.to_dict(orient='records')  # 这会创建一个包含字典的列表，每个字典代表一个workID和它的poetIDs列表
    return result_dict


@app.get('/getWorkAbsence/{workID}')
def getWorkAbsence(workID):
    columns_to_exclude = ['Summary', 'UniformTitle', 'VariantTitle']
    columns_to_exclude += [col for col in work.columns if 'PY' in col]

    # 筛选出需要检查的列
    columns_to_check = [col for col in work.columns if col not in columns_to_exclude]
    record = work[work['workID'] == int(workID)]
    if record.empty:
        return ['unknown'] * len(columns_to_check)
    record = record.iloc[0]
    record = record[columns_to_check]
    # 检查指定ID的记录
    result = [value if pd.notna(value) else 'unknown' for value in record]
    result = [x.item() if isinstance(x, np.generic) else x for x in result]
    return result


@app.get('/getPoetAbsence/{poetID}')
def getPoetAbsence(poetID):
    columns_to_exclude = ['HuWenKai', 'xuZuoZhe', 'baZuoZhe']
    columns_to_exclude += [col for col in poet.columns if 'PY' in col]

    # 筛选出需要检查的列
    columns_to_check = [col for col in poet.columns if col not in columns_to_exclude]
    record = poet[poet['poetID'] == int(poetID)]
    if record.empty:
        return ['unknown'] * len(columns_to_check)
    record = record.iloc[0]
    record = record[columns_to_check]
    # 检查指定ID的记录
    result = [value if pd.notna(value) else 'unknown' for value in record]
    result = [x.item() if isinstance(x, np.generic) else x for x in result]
    return result


@app.get('/getWorkColumnStats/{allWorkIDs}')
def getWorkColumnStats(allWorkIDs, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    # 将 allWorkIDs 转换为列表
    allWorkIDs = allWorkIDs.split(',')

    # 排除不需要检查的列
    columns_to_exclude = ['Summary', 'UniformTitle', 'VariantTitle']
    columns_to_exclude += [col for col in work.columns if 'PY' in col]
    columns_to_check = [col for col in work.columns if col not in columns_to_exclude]

    # 为每一列生成非 'unknown' 值的查询，使用 CAST 将列转换为字符串
    non_unknown_count_queries = ', '.join([
        f"COUNT(CASE WHEN CAST({col} AS VARCHAR) != 'unknown' THEN 1 END) AS {col}_non_unknown"
        for col in columns_to_check
    ])

    # 生成 workID 列表的查询条件
    id_queries = ', '.join([str(id) for id in allWorkIDs])

    # 构建 SQL 查询以计算每列非 'unknown' 的数量
    query = f"SELECT {non_unknown_count_queries} FROM work WHERE workID IN ({id_queries})"

    # 执行查询并将结果转换为 DataFrame
    result = db_connection.query(query).df()

    # 输出每列非 'unknown' 的数量（可选）
    # for col, count in zip(columns_to_check, result.iloc[0]):
    #     print(f"Non-'unknown' count for {col}: {count}")

    # 转换结果为字典列表格式并返回
    result_dict = result.to_dict(orient='records')
    return result_dict


poetRank = pd.DataFrame()
poetRankNew = pd.DataFrame()


@app.get('/poetImportanceNew/{poetPara}')
def calPoetImportanceNew(poetPara, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    poetPara = poetPara.split(',')

    PoetParticipateWork = db_connection.query(
        "SELECT poetID, COUNT(DISTINCT workID) AS participate_count FROM workpoetlinks GROUP BY poetID ORDER BY "
        "participate_count DESC").df()

    bexiangzan = db_connection.query(
        '''SELECT p.poetassubjectID AS poetID, COUNT(DISTINCT p.poemID) AS bexiangzansubjectCount
        FROM poem p
        WHERE p.GenreHZ IN ('文﹕年譜', '文﹕略傳', '文﹕傳') AND p.poetassubjectID != 0
        GROUP BY p.poetassubjectID;''').df()

    discussed = db_connection.query(
        '''SELECT p.poetassubjectID AS poetID, COUNT(DISTINCT p.poemID) AS discussedCount
        FROM poem p
        WHERE p.GenreHZ IN ('文﹕詩話', '文﹕詞話', '文﹕案語') AND p.poetassubjectID != 0
        GROUP BY p.poetassubjectID;''').df()

    PoetParticipateWork.set_index('poetID', inplace=True)
    # xiangzanauthor.set_index('poetID', inplace=True)
    bexiangzan.set_index('poetID', inplace=True)
    discussed.set_index('poetID', inplace=True)
    # changheshi.set_index('poetID', inplace=True)

    # 合并数据
    poetRawData = pd.concat([PoetParticipateWork, bexiangzan, discussed], axis=1).fillna(0)
    # 归一化
    for column in poetRawData.columns:
        poetRawData[column] = min_max_normalize(poetRawData[column])

    participateWeight = float(poetPara[0])
    writeXZWeight = 0
    inXZWeight = float(poetPara[1])
    bediscussedWeight = float(poetPara[2])
    changheWeight = 0
    poet_min_max = poetRawData.copy()
    poet_min_max['participateCalc'] = participateWeight * poet_min_max['participate_count']
    # poet_min_max['writeXZCalc'] = writeXZWeight * poet_min_max['xiangzanauthor_count']
    poet_min_max['inXZCalc'] = inXZWeight * poet_min_max['bexiangzansubjectCount']
    poet_min_max['bediscussedCalc'] = bediscussedWeight * poet_min_max['discussedCount']
    # poet_min_max['changheCalc'] = changheWeight * poet_min_max['changheshiCount']

    poet_min_max['totalWeight'] = poet_min_max['participateCalc'] + poet_min_max['inXZCalc'] + poet_min_max[
        'bediscussedCalc']
    # ji_min_max['totalWeight'] = xuweight * ji_min_max['xucount'] + baweight * ji_min_max['bacount'] + ticiweight * \
    #                             ji_min_max['ticicount'] + includedweight * ji_min_max['includedcount']
    poet_min_max_sorted = poet_min_max.sort_values('totalWeight', ascending=False)
    max_importance = poet_min_max_sorted['totalWeight'].max()
    poet_min_max_sorted['normalized_totalWeight'] = poet_min_max_sorted['totalWeight'] / max_importance
    poet_min_max_sorted['ln_normalized_totalWeight'] = np.log(poet_min_max_sorted['normalized_totalWeight'] + 0.01)

    global poetRankNew
    poetRankNew = poet_min_max_sorted.copy()

    columns_to_exclude = ['HuWenKai', 'xuZuoZhe', 'baZuoZhe']
    columns_to_exclude += [col for col in poet.columns if 'PY' in col]
    columns_to_check = [col for col in poet.columns if col not in columns_to_exclude]
    columns_to_select = ', '.join(columns_to_check)

    poet.fillna('unknown', inplace=True)
    poetDetailsQuery = f'''SELECT 
                        poet.{columns_to_select}, 
                        COALESCE(current_region.PresentdayEquivalent, 'unknown') AS PresentdayEquivalent,
                        COALESCE(parent_region.regionHZ, 'unknown') AS ParentRegionName
                        FROM 
                            poet
                        LEFT JOIN 
                            poetregionlinks AS pr ON poet.poetID = pr.poetID
                        LEFT JOIN 
                            region AS current_region ON pr.regionID = current_region.regionID
                        LEFT JOIN 
                            region AS parent_region ON current_region.parentRegionID = parent_region.regionID
                        WHERE 
                            poet.poetID IN ({','.join(map(str, poet_min_max_sorted.index.tolist()))});'''
    poetDetails = db_connection.query(poetDetailsQuery).df().set_index('poetID')
    poetDetails['fullRegion'] = poetDetails['PresentdayEquivalent']

    # poetDetails['ParentRegionName'] = poetDetails['ParentRegionName'].apply(lambda x: convert(x, 'zh-cn')).str[:2]
    poetDetails['fullRegion'] = np.where(
        (poetDetails['fullRegion'].str.len() < 4) & (poetDetails['fullRegion'] != 'unknown') & (
                poetDetails['fullRegion'] != '北京') & (poetDetails['fullRegion'] != '天津'),  # 条件
        poetDetails['ParentRegionName'].str[:2],  # 如果条件为真
        poetDetails['fullRegion']  # 如果条件为假
    )
    poetDetails['fullRegion'] = np.where(
        poetDetails['fullRegion'] != 'unknown',  # 条件
        poetDetails['fullRegion'].str[:2],  # 如果条件为真
        poetDetails['fullRegion']  # 如果条件为假
    )
    poetDetails['fullRegion'] = poetDetails['fullRegion'].apply(lambda x: convert(x, 'zh-cn'))

    poetDetails.loc[poetDetails['fullRegion'] == '烟台', 'fullRegion'] = '山东'
    poetDetails.loc[poetDetails['fullRegion'] == '北魏', 'fullRegion'] = 'unknown'
    poetDetails.loc[poetDetails['fullRegion'] == '北直', 'fullRegion'] = '北京'
    poetDetails.loc[poetDetails['fullRegion'] == '北平', 'fullRegion'] = '北京'
    poetDetails.loc[poetDetails['fullRegion'] == '中书', 'fullRegion'] = '山西'
    poetDetails.loc[poetDetails['fullRegion'] == '广南', 'fullRegion'] = '广东'
    poetDetails.loc[poetDetails['fullRegion'] == '两浙', 'fullRegion'] = '浙江'
    poetDetails.loc[poetDetails['fullRegion'] == ' 四', 'fullRegion'] = '四川'
    poetDetails.loc[poetDetails['fullRegion'] == '*为', 'fullRegion'] = '浙江'
    poetDetails.loc[poetDetails['fullRegion'] == '利州', 'fullRegion'] = '福建'
    poetDetails.loc[poetDetails['fullRegion'] == '梓州', 'fullRegion'] = '四川'
    poetDetails.loc[poetDetails['fullRegion'] == '东晋', 'fullRegion'] = '广东'
    poetDetails.loc[poetDetails['fullRegion'] == '江南', 'fullRegion'] = '安徽'

    poetDetails['PresentdayEquivalent'] = np.where(
        poetDetails['PresentdayEquivalent'] != 'unknown',  # 条件
        poetDetails['PresentdayEquivalent'].apply(extract_last_two_and_abbreviate),  # 如果条件为真
        poetDetails['PresentdayEquivalent']  # 如果条件为假
    )

    poetDetails['StartYear'] = np.where(
        poetDetails['StartYear'] == 0,  # 如果年份为0
        'unknown',  # 替换为unknown
        poetDetails['StartYear']  # 否则保持原值
    )

    poetDetails['EndYear'] = np.where(
        poetDetails['EndYear'] == 0,  # 如果年份为0
        'unknown',  # 替换为unknown
        poetDetails['EndYear']  # 否则保持原值
    )
    # 整合结果
    combined_results = []
    for poetID, row in poet_min_max_sorted.iterrows():
        poet_detail = {}
        if poetID in poetDetails.index:
            poet_detail = poetDetails.loc[poetID].to_dict()

        combined = {
            'poetID': int(poetID),
            'poetCount': row.dropna().to_dict(),  # 这里使用 dropna() 移除任何NaN值，确保所有值都是JSON兼容的
            'poetDetail': poet_detail
        }
        combined_results.append(combined)
        # print(combined_results)

    # print(poet_min_max_sorted)
    return JSONResponse(content={"data": combined_results})


@app.get('/poetImportance/{poetPara}')
def calPoetImportance(poetPara, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    poetPara = poetPara.split(',')

    PoetParticipateWork = db_connection.query(
        "SELECT poetID, COUNT(DISTINCT workID) AS participate_count FROM workpoetlinks GROUP BY poetID ORDER BY "
        "participate_count DESC").df()

    xiangzanauthor = db_connection.query(
        "SELECT poempoetlinks.poetID,COUNT(DISTINCT poem.poemID) AS xiangzanauthor_count FROM poem,poempoetlinks "
        "WHERE poem.GenreHZ='文﹕像贊' AND poem.poemID = poempoetlinks.poemID GROUP BY poempoetlinks.poetID ORDER BY "
        "xiangzanauthor_count").df()

    bexiangzan = db_connection.query(
        "SELECT poetassubjectID AS poetID,COUNT(DISTINCT poemID) AS bexiangzansubjectCount FROM poem WHERE "
        "poem.GenreHZ='文﹕像贊' AND poetassubjectID !=0 GROUP BY poetassubjectID").df()

    discussed = db_connection.query(
        "SELECT poetassubjectID AS poetID, COUNT(DISTINCT poemID) AS discussedCount FROM poem WHERE GenreHZ!='文﹕像贊' "
        "AND poetassubjectID != 0 GROUP BY poetassubjectID").df()

    changheshi = db_connection.query(
        "SELECT changheshuxinpoetID AS poetID, COUNT(DISTINCT poemID) AS changheshiCount FROM poem WHERE "
        "changheshuxinpoetID !=0 GROUP BY changheshuxinpoetID").df()

    PoetParticipateWork.set_index('poetID', inplace=True)
    xiangzanauthor.set_index('poetID', inplace=True)
    bexiangzan.set_index('poetID', inplace=True)
    discussed.set_index('poetID', inplace=True)
    changheshi.set_index('poetID', inplace=True)

    # 合并数据
    poetRawData = pd.concat([PoetParticipateWork, xiangzanauthor, bexiangzan, discussed, changheshi], axis=1).fillna(0)
    # 归一化
    for column in poetRawData.columns:
        poetRawData[column] = min_max_normalize(poetRawData[column])

    participateWeight = float(poetPara[0])
    writeXZWeight = float(poetPara[1])
    inXZWeight = float(poetPara[2])
    bediscussedWeight = float(poetPara[3])
    changheWeight = float(poetPara[4])
    poet_min_max = poetRawData.copy()
    poet_min_max['participateCalc'] = participateWeight * poet_min_max['participate_count']
    poet_min_max['writeXZCalc'] = writeXZWeight * poet_min_max['xiangzanauthor_count']
    poet_min_max['inXZCalc'] = inXZWeight * poet_min_max['bexiangzansubjectCount']
    poet_min_max['bediscussedCalc'] = bediscussedWeight * poet_min_max['discussedCount']
    poet_min_max['changheCalc'] = changheWeight * poet_min_max['changheshiCount']

    poet_min_max['totalWeight'] = poet_min_max['participateCalc'] + poet_min_max['writeXZCalc'] + poet_min_max[
        'inXZCalc'] + poet_min_max['bediscussedCalc'] + poet_min_max['changheCalc']
    # ji_min_max['totalWeight'] = xuweight * ji_min_max['xucount'] + baweight * ji_min_max['bacount'] + ticiweight * \
    #                             ji_min_max['ticicount'] + includedweight * ji_min_max['includedcount']
    poet_min_max_sorted = poet_min_max.sort_values('totalWeight', ascending=False)

    global poetRank  # 确保 workRank 是全局变量
    poetRank = poet_min_max_sorted.copy()

    columns_to_exclude = ['HuWenKai', 'xuZuoZhe', 'baZuoZhe']
    columns_to_exclude += [col for col in poet.columns if 'PY' in col]
    columns_to_check = [col for col in poet.columns if col not in columns_to_exclude]
    columns_to_select = ', '.join(columns_to_check)

    poet.fillna('unknown', inplace=True)
    poetDetailsQuery = f'''SELECT poet.{columns_to_select}, COALESCE(region.PresentdayEquivalent, 'unknown') AS PresentdayEquivalent
                            FROM poet
                            LEFT JOIN poetregionlinks AS pr ON poet.poetID = pr.poetID
                            LEFT JOIN region ON pr.regionID = region.regionID
                            WHERE poet.poetID IN ({','.join(map(str, poet_min_max_sorted.index.tolist()))});'''
    poetDetails = db_connection.query(poetDetailsQuery).df().set_index('poetID')
    poetDetails['PresentdayEquivalent'] = np.where(
        poetDetails['PresentdayEquivalent'] != 'unknown',  # 条件
        poetDetails['PresentdayEquivalent'].apply(extract_last_two_and_abbreviate),  # 如果条件为真
        poetDetails['PresentdayEquivalent']  # 如果条件为假
    )

    poetDetails['StartYear'] = np.where(
        poetDetails['StartYear'] == 0,  # 如果年份为0
        'unknown',  # 替换为unknown
        poetDetails['StartYear']  # 否则保持原值
    )

    poetDetails['EndYear'] = np.where(
        poetDetails['EndYear'] == 0,  # 如果年份为0
        'unknown',  # 替换为unknown
        poetDetails['EndYear']  # 否则保持原值
    )
    # 整合结果
    combined_results = []
    for poetID, row in poet_min_max_sorted.iterrows():
        poet_detail = {}
        if poetID in poetDetails.index:
            poet_detail = poetDetails.loc[poetID].to_dict()

        combined = {
            'poetID': int(poetID),
            'poetCount': row.dropna().to_dict(),  # 这里使用 dropna() 移除任何NaN值，确保所有值都是JSON兼容的
            'poetDetail': poet_detail
        }
        combined_results.append(combined)
        # print(combined_results)

    # print(poet_min_max_sorted)
    return JSONResponse(content={"data": combined_results})


@app.get('/getSelectedPoets/{workIds}')
def getSelectedPoets(workIds):
    # workIds = workIds.split(',')
    db_connection = get_db_connection()
    qury = f'''
    SELECT DISTINCT poetID
    FROM workpoetlinks
    WHERE workID in ({workIds})
    '''

    results = db_connection.query(qury).df()
    result_list = results['poetID'].tolist()
    return result_list


@app.get('/getSelectedPoems/{workIds}')
def getSelectedPoems(workIds):
    # workIds = workIds.split(',')
    db_connection = get_db_connection()
    qury = f'''
    SELECT DISTINCT poemID
    FROM workpoemlinks
    WHERE workID in ({workIds})
    '''

    results = db_connection.query(qury).df()
    result_list = results['poemID'].tolist()
    return result_list


@app.get('/poemImportance/{poemPara}')
def calPoemImportance(poemPara, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    poemPara = poemPara.split(',')

    poemWorkPoetSQL = '''
    SELECT poem.poemID, workpoemlinks.workID,poempoetlinks.poetID
    FROM poem
    LEFT JOIN workpoemlinks ON poem.poemID = workpoemlinks.poemID
    LEFT JOIN poempoetlinks ON poem.poemID = poempoetlinks.poemID
    '''
    poemWorkPoet = duckdb.query(poemWorkPoetSQL).df()

    poemWorkPoet['workID'] = poemWorkPoet['workID'].fillna(0).astype(int)

    weight_mapping = workRank['totalWeight'].reindex(poemWorkPoet['workID']).reset_index(drop=True)

    poemWorkPoet = pd.concat([poemWorkPoet.reset_index(drop=True), weight_mapping.rename('workImportance')], axis=1)

    poemWorkPoet['poetID'] = poemWorkPoet['poetID'].fillna(0).astype(int)
    # poemWorkPoet['workID'] = poemWorkPoet['workID'].astype(str)
    # ji_combine.index = ji_combine.index.astype(str)
    weight_mapping = poetRank['totalWeight'].reindex(poemWorkPoet['poetID']).reset_index(drop=True)

    poemWorkPoet = pd.concat([poemWorkPoet.reset_index(drop=True), weight_mapping.rename('poetImportance')], axis=1)

    poemWorkPoet['workImportance'] = poemWorkPoet['workImportance'].fillna(0).astype(int)
    workWeight = float(poemPara[0])
    poetWeight = float(poemPara[0])
    poetImportance = poemWorkPoet.copy()

    poetImportance['totalWeight'] = workWeight * poetImportance['workImportance'] + poetWeight * poetImportance[
        'poetImportance']
    poetImportance = poetImportance.sort_values('totalWeight', ascending=False)
    poetImportance.set_index('poemID', inplace=True)

    # columns_to_exclude = ['TunePatternSubtitle', 'TunePatternSubtitlePY', 'Refs']
    columns_to_exclude = ['tempID']
    columns_to_exclude += [col for col in poem.columns if 'PY' in col]
    columns_to_check = [col for col in poem.columns if col not in columns_to_exclude]
    columns_to_select = ', '.join(columns_to_check)

    poem.fillna('unknown', inplace=True)
    poemDetailsQuery = f"SELECT {columns_to_select} FROM poem WHERE poemID IN ({','.join(map(str, poetImportance.index.tolist()))})"
    poemDetails = db_connection.query(poemDetailsQuery).df().set_index('poemID')

    # 整合结果
    combined_results = []
    for poemID, row in poetImportance.iterrows():
        poem_detail = {}
        if poemID in poemDetails.index:
            poem_detail = poemDetails.loc[poemID].to_dict()

        combined = {
            'poemID': int(poemID),
            'poemCount': row.dropna().to_dict(),  # 这里使用 dropna() 移除任何NaN值，确保所有值都是JSON兼容的
            'poemDetail': poem_detail
        }
        combined_results.append(combined)
        # print(combined_results)

    # print(poet_min_max_sorted)
    return JSONResponse(content={"data": combined_results})


@app.get("/getworkpoetsidwithrelation/{workID}")
def get_work_poets_with_relation(workID):
    db_connection = get_db_connection()

    query = f'''
        SELECT *
        FROM relation
        WHERE workID = {workID}
    '''
    result = db_connection.query(query).df()
    result_dict = result.to_dict(orient='records')
    # result_list = result['poetID'].tolist()
    # print(result_list)
    return result_dict


def extract_last_two_and_abbreviate(name):
    if isinstance(name, str):
        # 提取最后两个字
        last_two = name[-2:]
        # 转换为简写（示例为拼音首字母缩写）
        abbreviation = "".join([p[0].upper() for p in last_two])  # 拼音首字母
        return abbreviation
    return name


@app.post('/getsexdistribution/')
async def getSexDistribution(request: Request):
    poetIDs = await request.json()
    # 将 poetIDs 转换为逗号分隔的字符串
    poetIDs_str = ",".join(map(str, poetIDs))
    db_connection = get_db_connection()

    # 查询数据
    query = f'''SELECT 
    poet.poetID, 
    poet.Sex, 
    PresentdayEquivalent
FROM 
    poet, poetregionlinks, region
WHERE 
    poet.poetID IN ({poetIDs_str}) 
    AND poet.poetID = poetregionlinks.poetID 
    AND poetregionlinks.regionID = region.regionID'''

    result = db_connection.query(query).df()

    # 提取 PresentdayEquivalent 的最后两个字

    result['regionHZ'] = result['PresentdayEquivalent'].apply(extract_last_two_and_abbreviate)

    # 按地区和性别进行统计
    gender_stats = result.groupby(['regionHZ', 'Sex']).size().reset_index(name='count')

    # 将性别统计转换为透视表格式
    gender_pivot = gender_stats.pivot(index='regionHZ', columns='Sex', values='count').fillna(0)

    # 确保所有性别列都存在
    if '男' not in gender_pivot.columns:
        gender_pivot['男'] = 0
    if '女' not in gender_pivot.columns:
        gender_pivot['女'] = 0

    # 重置索引并重命名列
    gender_pivot = gender_pivot.reset_index()
    gender_pivot.columns = ['regionHZ', 'Males', 'Females']

    # 转换为字典格式并返回
    result_dict = gender_pivot.to_dict(orient='records')
    return result_dict


@app.post("/getgenre/", summary="获取分类和数量统计")
async def get_genre(request: Request):
    db_connection = get_db_connection()
    poemIDs = await request.json()

    # 定义一级分类的条件
    wen_conditions = " OR ".join([f"genreHZ LIKE '{kw}'" for kw in wen_keywords])
    tu_conditions = " OR ".join([f"genreHZ = '{kw}'" for kw in tu_keywords])

    # 获取一级分类统计
    query_level_1 = f'''
            SELECT
                COALESCE(
                    CASE
                        WHEN {wen_conditions} THEN '文'
                        WHEN {tu_conditions} THEN '圖'
                        ELSE genreHZ
                    END, 'unknown'
                ) AS genre_group,
                COUNT(*) AS num_poems
            FROM poem
            WHERE poemID IN ({",".join(map(str, poemIDs))})
            GROUP BY genre_group
            ORDER BY num_poems DESC
        '''
    level_1_result = db_connection.query(query_level_1).df()
    level_1_data = level_1_result.to_dict(orient="records")

    # 构造 D3 Treemap 格式数据
    treemap_data = {
        "name": "root",  # 根节点名称
        "children": []
    }

    for level_1_item in level_1_data:
        genre_group = level_1_item["genre_group"]
        num_poems = level_1_item["num_poems"]

        # 如果是 unknown，只保留一级分类
        if genre_group == "unknown":
            treemap_data["children"].append({
                "name": genre_group,
                "value": num_poems
            })
            continue

        # 获取二级分类统计
        if genre_group == "文":
            columnName = "GenreHZ"
            genre_condition = " OR ".join([f"genreHZ LIKE '{kw}%'" for kw in wen_keywords])
        elif genre_group == "圖":
            columnName = "GenreHZ"
            genre_condition = " OR ".join([f"genreHZ = '{kw}'" for kw in tu_keywords])
        else:
            columnName = "GenreHZ"
            genre_condition = f"genreHZ LIKE '{genre_group}%'"

        query_level_2 = f'''
            SELECT {columnName} AS sub_genre, COUNT(*) AS count
            FROM poem
            WHERE ({genre_condition}) AND poemID IN ({",".join(map(str, poemIDs))})
            GROUP BY {columnName}
            ORDER BY count DESC
        '''
        level_2_result = db_connection.query(query_level_2).df()
        level_2_data = level_2_result.to_dict(orient="records")

        # 添加一级分类及其子分类
        treemap_data["children"].append({
            "name": genre_group,
            "children": [
                {"name": sub_item["sub_genre"], "value": sub_item["count"]}
                for sub_item in level_2_data
            ]
        })

    return treemap_data


@app.get('/getpoemsbyworkpoet/{workID}/{poetID}')
def getpoemsbyworkpoet(workID, poetID):
    db_connection = get_db_connection()
    qury = f'''
        SELECT poem.poemID
        FROM poem
        JOIN poempoetlinks pp ON pp.poemID = poem.poemID
        JOIN workpoemlinks wp ON wp.poemID = poem.poemID
        WHERE pp.poetID = {poetID} AND wp.workID = {workID};
    '''
    result = db_connection.query(qury).df()
    result_list = result['poemID'].tolist()
    return result_list


@app.get('/getcyclebyyear/{years}')
def getCycleByYear(years):
    years = years.split(',')
    years = [int(year) for year in years]

    db_connection = get_db_connection()
    results = []

    for year in years:
        if year == 0:
            continue

        current_year = year
        found = False
        original_data = None  # 用来存储原始年份的查询结果

        while not found:
            query = f'''
                    SELECT Dynasty, StemBranch, Year
                    FROM cycle
                    WHERE YearXF = {current_year}
                '''
            result = db_connection.execute(query).fetchall()

            if not result:
                current_year -= 1
                continue

            # 如果是第一次查询，保存原始年份的Dynasty和StemBranch
            if current_year == year:
                if result:
                    original_data = result[0]  # 保存原始查询结果

            # 检查结果中的 Year 字段是否包含“元年”
            year_column = result[0][2]  # 假设 Year 在返回元组的第三个位置
            if '元年' in year_column:
                found = True
                date_emperor = year_column.split('元年')[0]  # 直接使用包含“元年”的日期
            else:
                current_year -= 1

        # 使用原始年份的 Dynasty 和 StemBranch
        for row in result:
            row_data = {
                "Dynasty": original_data[0] if original_data else row[0],  # 使用原始年份的Dynasty
                "StemBranch": original_data[1] if original_data else row[1],  # 使用原始年份的StemBranch
                "DateEmperor": date_emperor if '元年' in row[2] else row[2],  # 新增的 DateEmperor 字段
                "Year": original_data[2] if original_data else row[2]  # 使用查询开始的原始年份
            }
            results.append(row_data)

    return results


@app.get('/getsimilarpoetworkpubname/{workID}')
def getsimilarpoetworkpubname(workID):
    db_connection = get_db_connection()
    query = f'''SELECT DISTINCT w.workID, w.TitleHZ, w.PubNameHZ
                FROM work w
                INNER JOIN workpoetlinks wpl1 ON w.workID = wpl1.workID
                WHERE wpl1.poetID IN (
                    SELECT poetID
                    FROM workpoetlinks
                    WHERE workID = {workID}
                )
                AND w.workID != {workID}
                AND w.PubNameHZ IS NOT NULL;'''
    result = db_connection.query(query).df()
    result['TitleHZ'] = result['TitleHZ'].apply(
        lambda title: title.split(':')[0].split('：')[0].split('﹕')[0].split('(')[0].split(',')[0])
    result['WorkTitle'] = result['workID'].astype(str) + " - " + result['TitleHZ']

    result_dict = result.to_dict(orient='records')
    return result_dict


@app.get('/getpoetworkrole/{poetID}')
def getPoetWorkRole(poetID):
    db_connection = get_db_connection()
    query = f'''SELECT workID, TitleHZ, role
                FROM relation
                WHERE poetID = {poetID}
                '''
    result = db_connection.query(query).df()
    result['TitleHZ'] = result['TitleHZ'].apply(
        lambda title: title.split(':')[0].split('：')[0].split('﹕')[0].split('(')[0].split(',')[0])
    result['IDTitle'] = result['workID'].astype(str) + " - " + result['TitleHZ']
    result_dict = result.to_dict(orient='records')
    return result_dict


@app.get('/getsameworkpoetregion/{poetID}')
def getsameworkpoetregion(poetID):
    db_connection = get_db_connection()
    query = f'''WITH RelevantPoets AS (
                SELECT wp2.poetID
                FROM workpoetlinks wp1
                JOIN workpoetlinks wp2 ON wp1.workID = wp2.workID AND wp1.poetID != wp2.poetID
                WHERE wp1.poetID = {poetID}
            ),
            RegionCounts AS (
                SELECT r.PresentdayEquivalent, COUNT(*) AS freq
                FROM RelevantPoets rp
                JOIN poetregionlinks pr ON rp.poetID = pr.poetID
                JOIN region r ON pr.regionID = r.regionID
                GROUP BY r.PresentdayEquivalent
            )
            SELECT wp2.poetID, p.NameHZ, r.PresentdayEquivalent
            FROM workpoetlinks wp1
            JOIN workpoetlinks wp2 ON wp1.workID = wp2.workID AND wp1.poetID != wp2.poetID
            JOIN poet p ON wp2.poetID = p.poetID
            JOIN poetregionlinks pr ON wp2.poetID = pr.poetID
            JOIN region r ON pr.regionID = r.regionID
            JOIN RegionCounts rc ON r.PresentdayEquivalent = rc.PresentdayEquivalent
            WHERE wp1.poetID = {poetID}
            ORDER BY rc.freq DESC, r.PresentdayEquivalent;'''
    result = db_connection.query(query).df()
    result['PresentdayEquivalent'] = result['PresentdayEquivalent'].apply(extract_last_two_and_abbreviate)
    result['IDName'] = result['poetID'].astype(str) + " - " + result['NameHZ']
    result_dict = result.to_dict(orient='records')
    return result_dict


@app.get('/getsameworkpoetyear/{poetID}')
def getSameWorkPoetYear(poetID):
    db_connection = get_db_connection()
    query = f'''SELECT DISTINCT wp2.poetID, p.NameHZ, p.StartYear, p.EndYear
                    FROM workpoetlinks wp1
                    JOIN workpoetlinks wp2 ON wp1.workID = wp2.workID AND wp1.poetID != wp2.poetID
                    JOIN poet p ON wp2.poetID = p.poetID
                    WHERE wp1.poetID = {poetID}
                    ORDER BY p.StartYear;'''
    result = db_connection.query(query).df()
    result['StartYear'] = np.where(
        result['StartYear'] == 0,  # 如果年份为0
        'unknown',  # 替换为unknown
        result['StartYear']  # 否则保持原值
    )

    result['EndYear'] = np.where(
        result['EndYear'] == 0,  # 如果年份为0
        'unknown',  # 替换为unknown
        result['EndYear']  # 否则保持原值
    )
    filtered_result = result[(result['StartYear'] != 'unknown') | (result['EndYear'] != 'unknown')]
    filtered_result['IDName'] = filtered_result['poetID'].astype(str) + " - " + filtered_result['NameHZ']
    result_dict = filtered_result.to_dict(orient='records')
    return result_dict


@app.get('/getsameworkpoetethnicgroup/{poetID}')
def getSameWorkPoetEthnicGroup(poetID):
    db_connection = get_db_connection()
    query = f'''SELECT 
    wp2.poetID, 
    p.NameHZ, 
    p.EthnicGroup,
    COUNT(*) AS EthnicGroupCount  -- 计算每个种族组的出现次数
FROM 
    workpoetlinks wp1
JOIN 
    workpoetlinks wp2 ON wp1.workID = wp2.workID AND wp1.poetID != wp2.poetID
JOIN 
    poet p ON wp2.poetID = p.poetID
WHERE 
    wp1.poetID = {poetID}
GROUP BY 
    wp2.poetID, p.NameHZ, p.EthnicGroup  -- 按 poetID, NameHZ 和 EthnicGroup 分组
ORDER BY 
    EthnicGroupCount DESC,  -- 按种族组出现次数降序排列
    p.EthnicGroup;          -- 同一种族组内可以按名字或其他属性排序'''
    result = db_connection.query(query).df()
    result['IDName'] = result['poetID'].astype(str) + " - " + result['NameHZ']
    result_dict = result.to_dict(orient='records')
    return result_dict


@app.get("/getpoetworkID/{poetID}", summary="获取作者的集纯id")
def get_poet_work(poetID: str, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    query = f'''
            SELECT workID
            FROM workpoetlinks
            WHERE poetID = {poetID}
        '''
    result = db_connection.query(query).df()
    result_dict = result.to_dict(orient='records')
    # result_list = result['workID'].tolist()
    return result_dict


@app.get("/getworkpoemsdetail/{workID}")
def get_work_poem_detail(workID: str, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    # print(workID)
    query = f'''
            SELECT workpoemlinks.workID,work.TitleHZ AS workTitle,poet.poetID,poet.NameHZ,poem.poemID,poem.TitleHZ AS poemTitle
            FROM workpoemlinks
            LEFT JOIN poem ON workpoemlinks.poemID = poem.poemID
            LEFT JOIN work ON workpoemlinks.workID = work.workID
            LEFT JOIN poempoetlinks ON workpoemlinks.poemID =poempoetlinks.poemID
            LEFT JOIN poet ON poempoetlinks.poetID = poet.poetID
            WHERE workpoemlinks.workID = {workID}
        '''
    result = db_connection.query(query).df()
    # result_dict = result.to_dict(orient='records')
    sanitized_result = result.replace([np.nan, np.inf, -np.inf], "unknown")
    result_dict = sanitized_result.to_dict(orient='records')
    # result_list = result['poemID'].tolist()
    # print(result_list)
    return result_dict


@app.get("/getpoetpoemsdetail/{poetID}")
def get_poet_poem_detail(poetID: str, db_connection: duckdb.DuckDBPyConnection = Depends(get_db_connection)):
    # print(workID)
    query = f'''
            SELECT workpoetlinks.workID,work.TitleHZ AS workTitle,poet.poetID,poet.NameHZ,poem.poemID,poem.TitleHZ AS poemTitle
            FROM workpoetlinks
            LEFT JOIN work ON workpoetlinks.workID = work.workID
            LEFT JOIN poet ON workpoetlinks.poetID = poet.poetID
            LEFT JOIN poempoetlinks ON workpoetlinks.poetID = poempoetlinks.poetID
            LEFT JOIN poem ON poempoetlinks.poemID = poem.poemID
            WHERE workpoetlinks.poetID = {poetID}
        '''
    result = db_connection.query(query).df()
    # result_dict = result.to_dict(orient='records')
    sanitized_result = result.replace([np.nan, np.inf, -np.inf], "unknown")
    sanitized_result["workTitle"] = sanitized_result["workTitle"].apply(
        lambda x: re.split(r'[:：﹕(,]', x)[0].strip() if isinstance(x, str) else "unknown"
    )
    result_dict = sanitized_result.to_dict(orient='records')
    # result_list = result['poemID'].tolist()
    # print(result_list)
    return result_dict
