import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pandas as pd
import duckdb
import numpy as np
import altair as alt
import json
from urllib.request import urlopen
import time
import os
import plotly.express as px

poet = pd.read_csv('../../CCGIV/datasets/WomenWriting/poet.csv')
poem = pd.read_csv('../../CCGIV/datasets/WomenWriting/poem.csv')
poempoetlinks = pd.read_csv('../../CCGIV/datasets/WomenWriting/poempoetlinks.csv')
subwork = pd.read_csv('../../CCGIV/datasets/WomenWriting/subwork.csv')
subworkpoemlinks = pd.read_csv('../../CCGIV/datasets/WomenWriting/subworkpoemlinks.csv')
subworkpoetlinks = pd.read_csv('../../CCGIV/datasets/WomenWriting/subworkpoetlinks.csv')
work = pd.read_csv('../../CCGIV/datasets/WomenWriting/work.csv')
workpoemlinks = pd.read_csv('../../CCGIV/datasets/WomenWriting/workpoemlinks.csv')
workpoetlinks = pd.read_csv('../../CCGIV/datasets/WomenWriting/workpoetlinks.csv')

poet.fillna(value=np.nan, inplace=True)
poem.fillna(value=np.nan, inplace=True)

con = duckdb.connect()
con.register('poet', poet)
con.register('poem', poem)
con.register('poempoetlinks', poempoetlinks)
con.register('subwork', subwork)
con.register('subworkpoemlinks', subworkpoemlinks)
con.register('subworkpoetlinks', subworkpoetlinks)
con.register('work', work)
con.register('workpoemlinks', workpoemlinks)
con.register('workpoetlinks', workpoetlinks)

