from flask import Flask, render_template, redirect, url_for, Response, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from datetime import datetime
from datetime import timedelta
import time
import secrets
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['HOST_URL'] = "http://demo.breakernews.net"
db = SQLAlchemy(app)
api_base = "https://breakernews.net/api/v1/"
api_key = "gWxn2GjLfqKkBzsWo9tJebCQ22Hl0pgd"

languages = [
    {"name":"english", "code":'en', "text_justification":"right", "default_category":"latest"},
    {"name":"urdu", "code":'ur', "text_justification":"left", "default_category":"national"},
    {"name":"hindi", "code":'hi', "text_justification":"right", "default_category":"india"}
]


# ---------------------------------------------------------------------
# SCHEDULED JOB TO FETCH NEWS PERIODICALLY FROM breakernews API
# ---------------------------------------------------------------------
def fetchNews():
    # Looping through all languages to fetch news
    languages = languagesInfo()
    for language in languages:
        code = language.get("code")
        name = language.get("name")
        response = requests.get(api_base + "news/100?key={0}&lang={1}".format(api_key, code))
        if response.status_code == 200:
            articles = response.json()
            for article in articles:
                title = article.get('title')
                body = article.get('body')
                category = article.get('category')
                imageUrl = article.get('imageUrl')
                date = article.get('date')
                url_id = secrets.token_urlsafe(16)
                
                if newsExists(title) == False:
                    try:
                        addNews(url_id, title, body, category, imageUrl, name, date)
                        time.sleep(10)
                        # url = app.config.get('HOST_URL') + "/post/" + id
                        # data = {"message": title + "\n" + url, "link":url,  "access_token":"EAALMC9xx9ToBAF2Dw4NSIZAroJ3kLYOvHqPsropOH7TBBINiVeHFLBTGwBl6YSf8aTxNDqxPCp1fPr74do9r12q2qZCHylVe4OZCOXCgypQqx6hj7eWYnXESzf64fXV0c6vNktRGXcDUUpq0udXpbttDJZAUYUEnt85707LH1wZDZD"}
                        # response = requests.post(url="https://graph.facebook.com/105840371657222/feed", data=data)
                        print("News Added:" + title)
                    except Exception as e:
                        print('DB Error', e)
        else:
            print("Error Response From API:", response.status_code)

def postToFacebook():
    languages = languagesInfo()
    for language in languages:
        
        if language.get('socialmedia').get('facebook') != None:
            lang_name = language.get('name')
            params = {"language":lang_name}
            row = db.session.execute("""SELECT id, url_id, title from news WHERE DATE(news.current_time) >= DATE('now') AND DATE(news.current_time) < DATE('now', '+1 day') AND language=:language AND posted_to_fb = 0 ORDER BY current_time desc LIMIT 1;""", params).fetchone()
            if row:
                id = row[0]
                url_id = row[1]
                title = row[2]

                url = app.config.get('HOST_URL') + "/post/" + url_id
                access_token = language.get("socialmedia").get("facebook").get("access_token")
                page_id = language.get("socialmedia").get("facebook").get("page_id")
                data = {"message": title + "\n" + url, "link":url,  "access_token":access_token}
                response = requests.post(url="https://graph.facebook.com/{0}/feed".format(page_id), data=data)
                if response.status_code == 200:
                    print("Posted To Facebook:", title)
                    markAsPostedToFb(id)
                else:
                    print(">>Failed To Post To Facebook:",response.json(),title)

                time.sleep(10)
    
scheduler = APScheduler()
scheduler.add_job(id='news fetcher', func = fetchNews, trigger = 'interval', seconds = 300)
scheduler.add_job(id='post to fb', func = postToFacebook, trigger = 'interval', seconds = 300)
scheduler.start()


def markAsPostedToFb(id):
    params = {"id":id}
    db.session.execute("""UPDATE news set posted_to_fb=true where id=:id""", params)
    db.session.commit()

def getNews(language, category=None, count=20):
    if category != None:
        params = {"language":language, "category":category, "count":count}
        result = db.session.execute("""SELECT url_id, title, date, imageUrl, category, news.current_time from news where language=:language and category=:category ORDER BY id DESC LIMIT :count""", params)
    else:
        params = {"language":language, "count":count}
        result = db.session.execute("""SELECT url_id, title, date, imageUrl, category, news.current_time from news where language=:language ORDER BY id DESC LIMIT :count""", params)
    rows = result.fetchall()
    output = []
    if rows == None:
        return None

    for row in rows:
        output.append({"id":row[0], "title":row[1], "date":row[2], "imageUrl":row[3], "category":row[4], "dateRaw":row[5]})

    return output


def getNewsCategorically(language, categories, count):
    output = []
    for category in categories:
        articles = getNews(language, category, count)
        output.append({"category":category, "articles":articles})

    return output

       

def getArticle(id):
    result = db.session.execute("""SELECT url_id, title, body, date, imageUrl, category, language, news.current_time from news where url_id=:id""", {"id":id})
    row = result.fetchone()
    if row == None:
        return None
    return {
        "id":row[0], "title":row[1], "body":row[2], "date":row[3], "imageUrl":row[4], "category":row[5], "language":row[6], "dateRaw":row[7]
    }


def getCategories(language):
    result = db.session.execute("""SELECT DISTINCT category from news where language=:lang""", {'lang':language})
    # result = db.session.query(News.category.distinct())
    return [value[0] for value in result]

def languagesInfo():
    rows = db.session.execute("""select id, name, code from languages""")
    output = []
    for row in rows:
        output.append({
            "id":row[0],
            "name":row[1],
            "code":row[2],
            "socialmedia":{"facebook":facebookInfo(row[0])}
        })

    return output

def languageInfo(language_name):
    params = {"language":language_name}
    rows = db.session.execute("""select id, name, code from languages where name = :language""", params)
    output = []
    for row in rows:
        output.append({
            "id":row[0],
            "name":row[1],
            "code":row[2],
            "socialmedia":{"facebook":facebookInfo(row[0])}
        })

    return output

def facebookInfo(language_id):
    params = {"id":language_id}
    rows = db.session.execute("""SELECT id,page_id,access_token from facebook where language_id=:id""", params).fetchall()
    if len(rows) == 0:
        return None
    
    return {        
        "id":rows[0][0],
        "page_id":rows[0][1],
        "access_token":rows[0][2]
    }

def getLanguagesNames():
    result = db.session.execute("""SELECT DISTINCT name from languages""")
    # result = db.session.query(News.category.distinct())
    return [value[0] for value in result]

def languagesAndCategories():
    output = []
    languagesNames = getLanguagesNames()
    for languageName in languagesNames:        
        categories = getCategories(languageName)
        output.append({"name":languageName, "categories":categories})

    return output





def addNews(url_id, title, body, category, imageUrl, language, date):
    params = {"url_id":url_id, "title":title, "body":body, "category":category, "imageUrl":imageUrl, "language":language, "date":date}
    db.session.execute("INSERT INTO news(url_id, title, body, category, imageUrl, language, date) values(:url_id, :title, :body, :category, :imageUrl, :language, :date)", params)
    db.session.commit()
    return True


def newsExists(title):
    params = {"title":title}
    result = db.session.execute("SELECT * from news where title=:title", params)
    rows = result.fetchall()
    if len(rows) > 0:
        return True
    
    return False


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

def updateLanguageInfo(id, name, code):
    params = {"id":id, "name":name, "code":code}
    db.session.execute("UPDATE languages set name=:name, code=:code where id=:id", params)
    db.session.commit()
    return True

def updateFacebookPageInfo(id, page_id, access_token):
    params = {"id":id, "page_id":page_id, "access_token":access_token}
    db.session.execute("UPDATE facebook set page_id=:page_id, access_token=:access_token where id=:id", params)
    db.session.commit()
    return True

def addFacebookPageInfo(id, language_id, page_id, access_token):
    params = {"id":id, "language_id":language_id, "page_id":page_id, "access_token":access_token}
    db.session.execute("INSERT INTO facebook(page_id, access_token, language_id) values(:page_id, :access_token, :language_id) ", params)
    db.session.commit()
    return True

@app.route('/')
def index():
    return redirect('/english')

@app.route('/sitemap.xml', methods=['GET'])
def sitemapindex():   
    host = request.host_url
    languages = languagesInfo()
    sitemap_index = render_template('sitemap_index.xml', host=host, languages=languages)
    response= make_response(sitemap_index)
    response.headers["Content-Type"] = "application/xml"    

    return response 

@app.route('/<language>/sitemap.xml', methods=['GET'])
def sitemap(language):
    articles = getNews(language, count=1000)
    host = request.host_url
    
    sitemap = render_template('sitemap.xml', host=host, articles=articles)
    response= make_response(sitemap)
    response.headers["Content-Type"] = "application/xml" 

    return response

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
    articles = getNews(language, count=18)
    categories = getCategories(language)
    articles2 = getNewsCategorically(language, categories, 4)
    footer = languagesAndCategories()
    # categories = translateCategories(categories, langInfo.get('code'))
    return render_template('index2.html', articles = articles, articles2=articles2, categories = categories, language=language, footer=footer) 


@app.route("/<language>/<category>/")
def category(language, category):
    # categoriesInfo = requests.get(api_base + '/news/categories?key=' + api_key + "&lang=" + language).json()
    # categories = categoriesInfo['categories']    
    # articles = requests.get(api_base + 'news/{0}/20?key={1}&lang={2}'.format(category + ",international", api_key, language))
    articles = getNews(language, category)
    categories = getCategories(language)
    footer = languagesAndCategories()
    return render_template('category.html', articles = articles, categoryName = category, categories = categories, language=language, footer=footer)

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
    footer = languagesAndCategories()
    return render_template('single-post.html', article = article, fromcategory=fromcategory, latest=latest, category=category, categories = categories, language=language, hideBreakingNews=True, footer=footer)

@app.route("/dashboard", methods=["GET","POST"])
def admin():    
    if request.args.get("username") == "syedwaleedshah" and request.args.get("password") == "usingsystem.dashboard":
        if request.method == "POST" and request.form.get("language"):        
            id = request.form.get("id")
            name = request.form.get("name")
            code = request.form.get("code")
            updateLanguageInfo(id, name, code)

        elif request.method == "POST" and request.form.get("facebook"):        
            id = request.form.get("id")
            language_id = request.form.get("language_id")
            page_id = request.form.get("page_id")
            access_token = request.form.get("access_token")

            # Case of creating new facebook page information
            if id == "":
                addFacebookPageInfo(id,language_id,page_id,access_token)
            # Case of updating facebook page information
            else:
                updateFacebookPageInfo(id, page_id, access_token)
            



        langInfo = languagesInfo()
        return render_template('dashboard.html', languagesInfo=langInfo)
    else:
        return "<h1>Page Not Found<h1>"


   

@app.route("/google-trends")
def googletrends():
    return render_template("google-trends.html")

@app.route('/test/categories/<language>')
def test_categories(language):
    return jsonify(getCategories(language))

@app.route('/test/article/<title>')
def test_article(title):
    return jsonify(getArticle(title))

@app.route('/app/test/languageinfo')
def test_languageinfo():
    return jsonify(languagesInfo())

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
    app.run(debug=True, port=5001)