from sklearn.model_selection import train_test_split

import numpy as np


def get_csv_data(path):
    d = np.loadtxt(path,str, delimiter=',', skiprows=1,usecols=(0,1,-1))
    return d

train_path = "../bookdatasets/Books.csv"

with open(train_path,"r",encoding="utf-8") as f:
    cnt = 0
    max_len = 200
    # my_dtype = np.dtype([("isbn","S32"),("title","S128"),("author","S256"),("publication","S256"),("Publisher","S256"),
    #                      ("Image-URL-S","S256"),("Image-URL-M","S256"),("Image-URL-L","S256")])
    data_list = np.empty(shape=(max_len,8),dtype=str)
    for i in range(1,max_len):
        data1 = f.readline()
        dataline = data1.split(",")
        if len(dataline)>8:
            # print(dataline)
            # print(len(dataline))
            cnt+=1
        else:
            print(dataline)
            data_list[i] = np.array(dataline)
    print(data_list[5])
    print(data_list)
    print(cnt)
# train_data = get_csv_data(train_path)
# y, X = np.split(train_data, [1, ], 1)
# print(train_data)
# y, X = np.split(train_data, [1, ], 1)

# print(y)


