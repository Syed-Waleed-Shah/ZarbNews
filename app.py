from flask import Flask, render_template, redirect, url_for, Response, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from datetime import datetime
import secrets
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite'
db = SQLAlchemy(app)
api_base = "https://breakernews.net/api/v1/"
api_key = "TsMsvGDMLBbp-kKjSVqRiONSfja5Ocpf"

languages = [
    {"name":"english", "code":'en', "text_justification":"right"},
    {"name":"urdu", "code":'ur', "text_justification":"left"},
    {"name":"hindi", "code":'hi', "text_justification":"right"}
]




class News(db.Model):
    id = db.Column(db.String, primary_key=True)
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
        response = requests.get(api_base + "/news/500?key={0}&lang={1}".format(api_key, language['code']))
        if response.status_code == 200:
            articles = response.json()
            for article in articles:
                title = article.get('title')
                body = article.get('body')
                category = article.get('category')
                imageUrl = article.get('imageUrl')
                date = article.get('date')
                id = secrets.token_urlsafe(16)
                news = News(id=id, title=title, body=body, category=category, imageUrl=imageUrl, language=language['name'], date=date)

                # Before adding news in database checking whether news already exists in database
                result = News.query.filter(News.title==title, News.imageUrl==imageUrl).all()
                if len(result) < 1:
                    db.session.add(news)
                    db.session.commit()
   
scheduler = APScheduler()
scheduler.add_job(id='news fetcher', func = fetchNews, trigger = 'interval', seconds = 100)
scheduler.start()


def getNews(language, category, count=20):
    return News.query.filter(News.language == language, News.category == category).order_by(News.id.desc()).limit(count)

def getArticle(id):
    result = db.session.execute("""SELECT id, title, body, date, imageUrl, category from news where id=:id""", {"id":id})
    row = result.fetchone()
    if row == None:
        return None
    return {
        "id":row[0], "title":row[1], "body":row[2], "date":row[3], "imageUrl":row[4], "category":row[5]
    }


def getCategories(language):
    result = db.session.execute("""SELECT DISTINCT category from news where language=:lang""", {'lang':language})
    # result = db.session.query(News.category.distinct())
    return [value[0] for value in result]

def joinList(lst, sep=','):
    result = ''
    for index in range(len(lst)-1):
        result += lst[index] + sep

    if len(lst) > 0:
        result += lst[len(lst)-1]
    return result



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
    articles = getNews(language, "latest")
    categories = getCategories(language)
    return render_template('index2.html', articles = articles, categories = categories, language=language) 


@app.route("/<language>/<category>/")
def category(language, category):
    # categoriesInfo = requests.get(api_base + '/news/categories?key=' + api_key + "&lang=" + language).json()
    # categories = categoriesInfo['categories']    
    # articles = requests.get(api_base + 'news/{0}/20?key={1}&lang={2}'.format(category + ",international", api_key, language))
    articles = getNews(language, category)
    categories = getCategories(language)
    return render_template('category.html', articles = articles, categoryName = category, categories = categories, language=language)

@app.route("/<language>/<category>/<article_id>")
def details(language, category, article_id):
    article = getArticle(article_id)
    if article == None:
        return "Unable to find this article"
    categories = getCategories(language)
    return render_template('single-post.html', article = article, categories = categories, language=language, hideBreakingNews=True)

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
    <td>title</td>
     <td>category</td>
    <td>date</td>
    </tr>
    </thead>
    <tbody>
    """.format(len(articles))
    for article in articles:
        html += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td></tr>".format(article.id, article.language, article.title, article.category, article.date)

    html += "</tbody></table>"

    return html



if __name__ == '__main__':    
    app.run(debug=True, port=1111)