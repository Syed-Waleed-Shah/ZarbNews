from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    body = db.Column(db.String)
    category = db.Column(db.String(30))
    imageUrl = db.Column(db.String)
    language = db.Column(db.String(20))
    date = db.Column(db.DateTime)


    