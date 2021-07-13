from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import Config
import numpy as np
import pandas as pd

app = Flask(__name__)
app.config.from_object(Config)
app.debug = True
db = SQLAlchemy(app)

dataset = pd.read_csv(Config.RATING_PATH, low_memory=False)

re_users = dataset['User-ID'].unique()
re_items = dataset['ISBN'].unique()

users_kv = {}
for i in range(0,re_users.shape[0]):
    users_kv[re_users[i]] = i
items_kv = {}
for i in range(0,re_items.shape[0]):
    items_kv[re_items[i]] = i

train_data_matrix = np.zeros((re_users.shape[0], re_items.shape[0]))
for line in dataset.itertuples():
    train_data_matrix[users_kv[line[2]], items_kv[line[3]]] = line[4]

from app.api import api

app.register_blueprint(api,url_prefix='/api/v2.0')