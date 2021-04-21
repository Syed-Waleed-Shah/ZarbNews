import requests
from datetime import datetime
api_base = "http://localhost:5000/api/v1/"
api_key = "1d_ZKu124CDq3rlCU7N0Vgn18z4iyeow"

print(datetime.now())
categoriesInfo = requests.get(api_base + '/news/categories?key=' + api_key).json()
categories = categoriesInfo['categories']
print(categories)
news = []
articles = requests.get(api_base + 'news/latest,pakistan,entertainment,sports,business,technology,international,fact,health,world')
# for category in categories:
#     articles = requests.get(api_base + 'async/news/{0}/6?key={1}'.format(category, api_key))
#     news.append({"category":category, "articles":articles.json()})   
if articles.status_code == 200:
    print(articles)

print(articles.status_code)
print(datetime.now())