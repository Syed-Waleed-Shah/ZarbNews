from flask import Flask, render_template, redirect, url_for, Response, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from datetime import datetime
import secrets
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
api_base = "http://127.0.0.1:5000/api/v1/"
api_key = "TsMsvGDMLBbp-kKjSVqRiONSfja5Ocpf"

languages = [
    {"name":"english", "code":'en', "text_justification":"right", "default_category":"latest"},
    {"name":"urdu", "code":'ur', "text_justification":"left", "default_category":"national"},
    {"name":"hindi", "code":'hi', "text_justification":"right", "default_category":"india"}
]




class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.String)
    title = db.Column(db.String)
    body = db.Column(db.String)
    category = db.Column(db.String(30))
    imageUrl = db.Column(db.String)
    language = db.Column(db.String(20))
    date = db.Column(db.String)

# ---------------------------------------------------------------------
# SCHEDULED JOB TO FETCH NEWS PERIODICALLY FROM breakernews API
# ---------------------------------------------------------------------
def fetchNews():
    # Looping through all languages to fetch news
    for language in languages:
        response = requests.get(api_base + "news/50?key={0}&lang={1}".format(api_key, language['code']))
        if response.status_code == 200:
            articles = response.json()
            for article in articles:
                title = article.get('title')
                body = article.get('body')
                category = article.get('category')
                imageUrl = article.get('imageUrl')
                date = article.get('date')
                id = secrets.token_urlsafe(16)
                news = News(url_id=id, title=title, body=body, category=category, imageUrl=imageUrl, language=language['name'], date=date)

                # Before adding news in database checking whether news already exists in database
                result = News.query.filter(News.title==title, News.imageUrl==imageUrl).all()
                if len(result) < 1:
                    try:
                        db.session.add(news)
                        db.session.commit()
                        url = "https://127.0.0.1:1111/post/" + id
                        data = {"message": title + "\n" + url, "link":url,  "access_token":"EAALMC9xx9ToBAF2Dw4NSIZAroJ3kLYOvHqPsropOH7TBBINiVeHFLBTGwBl6YSf8aTxNDqxPCp1fPr74do9r12q2qZCHylVe4OZCOXCgypQqx6hj7eWYnXESzf64fXV0c6vNktRGXcDUUpq0udXpbttDJZAUYUEnt85707LH1wZDZD"}
                        response = requests.post(url="https://graph.facebook.com/105840371657222/feed", data=data)
                    except:
                        print('DB Error')
    
    print("Job Executed Sucessfully:" + str(datetime.now()))
scheduler = APScheduler()
scheduler.add_job(id='news fetcher', func = fetchNews, trigger = 'interval', seconds = 100)
scheduler.start()


def getNews(language, category=None, count=20):
    if category != None:
        params = {"language":language, "category":category, "count":count}
        result = db.session.execute("""SELECT url_id, title, date, imageUrl, category from news where language=:language and category=:category ORDER BY id DESC LIMIT :count""", params)
    else:
        params = {"language":language, "count":count}
        result = db.session.execute("""SELECT url_id, title, date, imageUrl, category from news where language=:language ORDER BY id DESC LIMIT :count""", params)
    rows = result.fetchall()
    output = []
    if rows == None:
        return None

    for row in rows:
        output.append({"id":row[0], "title":row[1], "date":row[2], "imageUrl":row[3], "category":row[4]})

    return output

       

def getArticle(id):
    result = db.session.execute("""SELECT url_id, title, body, date, imageUrl, category, language from news where url_id=:id""", {"id":id})
    row = result.fetchone()
    if row == None:
        return None
    return {
        "id":row[0], "title":row[1], "body":row[2], "date":row[3], "imageUrl":row[4], "category":row[5], "language":row[6]
    }


def getCategories(language):
    result = db.session.execute("""SELECT DISTINCT category from news where language=:lang""", {'lang':language})
    # result = db.session.query(News.category.distinct())
    return [value[0] for value in result]

def languageInfo(language_name):
    for lang in languages:
        if lang.get('name') == language_name:
            return lang
    return None

def joinList(lst, sep=','):
    result = ''
    for index in range(len(lst)-1):
        result += lst[index] + sep

    if len(lst) > 0:
        result += lst[len(lst)-1]
    return result

def translateCategories(categories, lang_code):
    from translate import Translator
    translator = Translator(to_lang=lang_code)
    output = []
    for category in categories:        
        output.append([category,translator.translate(category)])

    return output



@app.route('/')
def index():
    return redirect('/english')

@app.route('/<language>/')
def home(language):    
    # response = requests.get(api_base + '/news/categories?key=' + api_key + "&lang=" + language)
    # if response.status_code == 200:
    #     categoriesInfo = response.json()
    #     categories = categoriesInfo['categories']
    #     joinedCategories = joinList(categories)
    #     articles = requests.get(api_base + 'news/{0}/6?key={1}&lang={2}'.format(joinedCategories, api_key,language))
    #     return render_template('index2.html', news = articles.json(), categories = categories, language=language)
    
    # return "Website is down"     
    langInfo = languageInfo(language) 
    if langInfo == None:
        return "<h1>404 Page Not Found</h1>"
    articles = getNews(language, langInfo.get('default_category'))
    categories = getCategories(language)
    
    # categories = translateCategories(categories, langInfo.get('code'))
    return render_template('index2.html', articles = articles, categories = categories, language=language) 


@app.route("/<language>/<category>/")
def category(language, category):
    # categoriesInfo = requests.get(api_base + '/news/categories?key=' + api_key + "&lang=" + language).json()
    # categories = categoriesInfo['categories']    
    # articles = requests.get(api_base + 'news/{0}/20?key={1}&lang={2}'.format(category + ",international", api_key, language))
    category = category.replace('-', ' ')
    articles = getNews(language, category)
    categories = getCategories(language)

    return render_template('category.html', articles = articles, categoryName = category, categories = categories, language=language)

@app.route("/post/<article_id>")
def details(article_id):
    article = getArticle(article_id)    
    
    if article == None:
        return "Unable to find this article"

    category = article.get('category')
    language = article.get('language')
    fromcategory = getNews(language=language, category=category, count=8)
    latest = getNews(language=language, count=12)
    categories = getCategories(language)
    return render_template('single-post.html', article = article, fromcategory=fromcategory, latest=latest, category=category, categories = categories, language=language, hideBreakingNews=True)

@app.route('/test/categories/<language>')
def test_categories(language):
    return jsonify(getCategories(language))

@app.route('/test/article/<title>')
def test_article(title):
    return jsonify(getArticle(title))

@app.route('/private/query/database/<query>')
def exec_query(query):
    db.session.execute(query)
    db.session.commit()
    return "Executed Sucessfully"

@app.route('/test')
def test():    
    articles = News.query.all()
    html = """
    <h1>Total Articles : {0}</h1>
    <table>
    <thead>
    <tr>
    <td>id</td>
    <td>language</td>    
     <td>category</td>
    <td>date</td>
    <td>title</td>
    </tr>
    </thead>
    <tbody>
    """.format(len(articles))
    for article in articles:
        html += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td></tr>".format(article.id, article.language, article.category, article.date, article.title)

    html += "</tbody></table>"

    return html

@app.route('/test/urdu-test')
def urdu_test():
    categories = getCategories('urdu')
    return render_template('urdu-test.html', categories=categories)


if __name__ == '__main__':    
    app.run(debug=True, port=1111)