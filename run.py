import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from flask_paginate import Pagination, get_page_args
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect, validate_csrf, ValidationError
from wtforms import (
    Form, TextField,
    PasswordField, validators)
from wtforms.validators import InputRequired, EqualTo

if os.path.exists("env.py"):
    import env

# Articles pagination limit
PER_PAGE = 6

# Flask app setup
app = Flask(__name__)
csrf = CSRFProtect(app)

csrf.init_app(app)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)

# Pagination
"""Credit: Ed Bradley\
@ https://github.com/Edb83/self-isolution/blob/master/app.py
"""


def paginate(articles):
    page, per_page, offset = get_page_args(
        page_parameter='page', per_page_parameter='per_page')
    offset = page * PER_PAGE - PER_PAGE
    return articles[offset: offset + PER_PAGE]


def pagination_args(articles):
    page, per_page, offset = get_page_args(
        page_parameter='page', per_page_parameter='per_page')
    total = len(articles)
    return Pagination(page=page, per_page=PER_PAGE, total=total)


"""
End Credit
"""


@app.route("/")
@app.route("/index")
def index():
    """
    Links to home page when using the main website link
    """
    articles = mongo.db.articles.find()
    return render_template("index.html",
                           articles=articles)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """
    Links to contact page
    """
    return render_template("contact.html")


@app.route("/articles")
def articles():
    """
    Links articles from database to site and displays all
    articles
    """
    articles = list(mongo.db.articles.find())
    articles_paginate = paginate(articles)
    pagination = pagination_args(articles)
    topic = mongo.db.topics.find()
    topic_name = list(mongo.db.topics.find().sort("topic_name", 1))

    topics = {}
    for article in articles:
        if article["topic_name"] in topics:
            topics["article"].append(article._id)
        else:
            print(article["_id"])
            topics["article_id"] = article["_id"]

    return render_template("articles.html",
                           articles=articles_paginate,
                           page_title="Articles",
                           pagination=pagination,
                           topic=topic,
                           topics=topics,
                           topic_name=topic_name,
                           article=article)


@app.route("/search",  methods=["GET", "POST"])
def search():
    """
    Returns search results from user input query based on indexes
    of article name, article content and topic name.
    """
    query = request.form.get("query")
    articles = list(mongo.db.articles.find({"$text": {"$search": query}}))
    articles_paginate = paginate(articles)
    pagination = pagination_args(articles)

    return render_template("articles.html",
                           articles=articles_paginate,
                           page_title="Article Results",
                           pagination=pagination)


"""
The below code was taken from
https://wtforms.readthedocs.io/en/stable/crash_course/
"""


class LoginForm(Form):
    """
    Form fields for user login
    """
    username = TextField('Username')
    password = PasswordField('Password')


"""
End Credit
"""

"""
The below code was found on 
https://pythonprogramming.net/flask-registration-tutorial/
"""


class RegistrationForm(Form):
    """
    Form fields and validators for registration, 
    WTForms is used to validate the registration form fields.
    """
    username = TextField('Username',
                         [validators.Length(min=4, max=20),
                          validators.Regexp(r'^\w+$', message=(
                              "Username must contain only letters "
                              "numbers or underscore"))])

    email = TextField('Email Address', [validators.Length(min=6, max=50)])

    password = PasswordField('New Password', [
        validators.InputRequired(),
        validators.EqualTo('confirm', message='Passwords must match'),
        validators.Regexp(r'^\w+$', message=(
            "Password must contain only letters numbers or underscore"))
    ])

    confirm = PasswordField('Repeat Password')


@app.route("/registration", methods=["GET", "POST"])
def registration():
    """
    Allows users to sign up to the site, create an account profile
    and send data to the database
    """
    try:
        form = RegistrationForm(request.form)

        if request.method == 'POST' and form.validate():
            existing_user = mongo.db.users.find_one(
                {"username": request.form.get("username").lower()})

            if existing_user:
                flash("Username already exists")
                return redirect(url_for("registration"))

            signup = {
                "username": request.form.get("username").lower(),
                "email": request.form.get("email").lower(),
                "password": generate_password_hash(
                    request.form.get("password"))
            }
            mongo.db.users.insert_one(signup)

            session["user"] = request.form.get("username").lower()
            flash('You have signed up successfully!')
            return redirect(url_for("profile", username=session['user']))

        return render_template('sign-up.html', form=form)

    except Exception as e:
        return (str(e))


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Allows users to login and access their profile 
    by checking their password and username to make sure 
    it corresponds with the users collection in the database.
    """
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()

                flash("Welcome back {}!".format(
                    request.form.get("username")))
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                flash("Incorrect Username/password, Please try again")
                return redirect(url_for("login"))

        else:
            flash("Incorrect Username/password, Please try again")
            return redirect(url_for("login"))

    return render_template("login.html", title='Login', form=form)


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    """
    Links users to their profiles by checking the session username
    against the users collection in the database. Profile page 
    displays all the user's contributions upon successful
    log in.
    """
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    articles = list(mongo.db.articles.find(
        {"created_by": session["user"]}).sort("_id", -1))

    if session["user"]:
        return render_template("profile.html", username=username,
                               articles=articles)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    """
    Allows users to logout of their profile
    by removing users from session cookie and redirects
    to log in page.
    """
    flash("You have logged out successfully!")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_article", methods=["GET", "POST"])
def add_article():
    """
    Allows users to contribute towards the site
    with their own unique articles and stores articles
    in MongoDB articles collection.
    """
    topics = mongo.db.topics.find().sort("topic_name", 1)
    locations = mongo.db.locations.find().sort("location_name", 1)

    if "user" not in session:
        flash("Please Log in to continue")
        return redirect(url_for("login"))
    elif request.method != "POST":
        return render_template("add_article.html", topics=topics,
                               locations=locations)
    else:
        article = {
            "topic_name": request.form.get("topic_name"),
            "article_name": request.form.get("article_name"),
            "image_url": request.form.get("image_url"),
            "article_article": request.form.get("article_article"),
            "location_name": request.form.get("location_name"),
            "created_by": session["user"],
            "date_added": request.form.get("date_added")
        }
        mongo.db.articles.insert_one(article)
        flash("Article contribution successful!")
        return redirect(url_for("articles"))

    return render_template("add_article.html", topics=topics,
                           locations=locations)


@app.route("/edit_article/<article_id>", methods=["GET", "POST"])
def edit_article(article_id):
    """
    Allows users to edit their contributions to the site
    and updates the articles collection in MongoDB.
    """
    article = mongo.db.articles.find_one({"_id": ObjectId(article_id)})
    topics = mongo.db.topics.find().sort("topic_name", 1)
    locations = mongo.db.locations.find().sort("location_name", 1)
    article_creator = article["created_by"]

    if "user" not in session:
        flash("Please Log in to continue")
        return redirect(url_for("login"))

    elif session["user"] != article_creator and session["user"] != "admin":
        flash("You are not authorized to edit this material")
        return redirect(url_for("articles"))

    elif request.method != "POST":
        return render_template("edit_article.html", article=article,
                               topics=topics, locations=locations)

    else:
        adjust = {
            "topic_name": request.form.get("topic_name"),
            "article_name": request.form.get("article_name"),
            "image_url": request.form.get("image_url"),
            "article_article": request.form.get("article_article"),
            "location_name": request.form.get("location_name"),
            "created_by": session["user"],
            "date_added": request.form.get("date_added")
        }
        mongo.db.articles.update({"_id": ObjectId(article_id)}, adjust)
        flash("Article update successful!")

    return redirect(url_for("articles"))


@app.route("/delete_article/<article_id>")
def delete_article(article_id):
    """
    Allows users to delete their contributions to site 
    and removes the specific article from the articles collection in
    MongoDB.
    """
    article = mongo.db.articles.find_one({"_id": ObjectId(article_id)})
    article_creator = article["created_by"]

    if "user" not in session:
        flash("Please Log in to continue")
        return redirect(url_for("login"))

    elif session["user"] != article_creator and session["user"] != "admin":
        flash("You are not authorized to edit this material")
        return redirect(url_for("articles"))

    else:
        mongo.db.articles.remove({"_id": ObjectId(article_id)})
        flash("Article successfully deleted.")
        return redirect(url_for("articles"))


@app.route("/topics")
def topics():
    """
    Displays a series of topics on the topics page
    and links to the topics collection in MongoDB.
    """
    if "user" not in session:
        flash("Please Log in to continue")
        return redirect(url_for("login"))

    else:
        topics = list(mongo.db.topics.find().sort("topic_name", 1))
        topic_name = list(mongo.db.topics.find())
        article_list = {}

        for topic in topics:
            if topic["topic_name"] in topics:
                topic["article_list"].append(topic._id)
            else:
                print(topic["_id"])
                topic["topic_id"] = topic["_id"]

        return render_template("topics.html",
                               topics=topics,
                               topic_name=topic_name,
                               article_list=article_list)


@app.route("/filter/topic/<topic_id>")
def filter_topics(topic_id):
    """
    Filters articles page based on topic
    to only show articles with the same topic
    name.
    """
    topics = list(mongo.db.topics.find())
    topic = mongo.db.topics.find_one({"_id": ObjectId(topic_id)})
    articles = list(mongo.db.articles.find(
        {"topic_name": topic["topic_name"]}).sort("_id", -1))
    pagination = pagination_args(articles)
    articles_paginate = paginate(articles)

    return render_template("articles.html",
                           articles=articles_paginate,
                           topic=topic,
                           topics=topics,
                           page_title=topic["topic_name"],
                           pagination=pagination)


@app.route("/add_topic", methods=["GET", "POST"])
def add_topic():
    """
    Allows Admin to add more topics to the site 
    and MongoDB as they see fit.
    """
    topics = mongo.db.topics.find().sort("topic_name", 1)

    if "user" not in session:
        flash("Please Log in to continue")
        return redirect(url_for("login"))

    elif session["user"].lower() != "admin":
        flash("You are not authorized to view this page")
        return redirect(url_for("topics"))

    elif request.method != "POST":
        return render_template("add_topic.html",
                               topics=topics)

    else:
        topic = {
            "topic_name": request.form.get("topic_name"),
            "article_list": [""]

        }
        mongo.db.topics.insert_one(topic)
        flash("Topic contribution successful!")
        return redirect(url_for("topics"))

    return render_template("topics.html", topics=topics,
                           topic=topic)


@app.route("/edit_topic/<topic_id>", methods=["GET", "POST"])
def edit_topic(topic_id):
    """
    Allows admin to edit site topics and updates
    MongoDB accordingly
    """
    topic = mongo.db.topics.find_one({"_id": ObjectId(topic_id)})

    if "user" not in session:
        flash("Please Log in to continue")
        return redirect(url_for("login"))

    elif session["user"].lower() != "admin":
        flash("You are not authorized to edit this material")
        return redirect(url_for("topics"))

    elif request.method != "POST":
        return render_template("edit_topic.html", topic=topic)

    else:
        adjust = {
            "topic_name": request.form.get("topic_name"),
            "article_list": []
        }
        mongo.db.topics.update({"_id": ObjectId(topic_id)}, adjust)
        flash("Topic update successful!")

    return redirect(url_for("topics"))


@app.route("/delete_topic/<topic_id>")
def delete_topic(topic_id):
    """
    Allows admin to delete topics as they see fit and
    removes the topic from the topics collection in the
    database.
    """
    topic = mongo.db.topics.find_one({"_id": ObjectId(topic_id)})

    if "user" not in session:
        flash("Please Log in to continue")
        return redirect(url_for("login"))

    elif session["user"].lower() != "admin":
        flash("You are not authorized to edit this material")
        return redirect(url_for("topics"))

    else:
        mongo.db.topics.remove({"_id": ObjectId(topic_id)})
        flash("Topic successfully deleted.")
        return redirect(url_for("topics", topic=topic))


@app.route("/further_reading")
def further_reading():
    """
    Displays external reading source information and links
    to the further_reading collection in the database.
    """
    further_reading = list(mongo.db.further_reading.find())

    return render_template("further_reading.html",
                           page_title="Further Reading",
                           further_reading=further_reading)


@app.route("/add_further_reading", methods=["GET", "POST"])
def add_further_reading():
    """
    Allows admin to add relevant external reading
    sources information to the site and the further_reading
    collection in the database as they see appropriate. 
    """
    topics = mongo.db.topics.find().sort("topic_name", 1)

    if "user" not in session:
        flash("Please Log in to continue")
        return redirect(url_for("login"))
    elif session["user"].lower() != "admin":
        flash("You are not authorized to view this page")
        return redirect(url_for("topics"))
    elif request.method != "POST":
        return render_template("add_further_reading.html",
                               further_reading=further_reading,
                               topics=topics)
    else:
        reading = {
            "topic_name": request.form.get("topic_name"),
            "book_title": request.form.get("book_title"),
            "website": request.form.get("website"),
            "article_title": request.form.get("article_title"),
            "author": request.form.get("author"),
            "date_published": request.form.get("date_published"),
            "publisher": request.form.get("publisher"),
        }
        mongo.db.further_reading.insert_one(reading)
        flash("Further Reading contribution successful!")
        return redirect(url_for("topics"))

    return render_template("topics.html", topics=topics,
                           reading=reading,
                           further_reading=further_reading)


@app.route("/edit_further_reading/<reading_id>", methods=["GET", "POST"])
def edit_further_reading(reading_id):
    """
    Allows admin to update the further reading page
    and further_reading collection in the database
    as they see fit.
    """
    reading = mongo.db.further_reading.find_one({"_id": ObjectId(reading_id)})
    topics = mongo.db.topics.find().sort("topic_name", 1)

    if "user" not in session:
        flash("Please Log in to continue")
        return redirect(url_for("login"))
    elif session["user"].lower() != "admin":
        flash("You are not authorized to view this page")
        return redirect(url_for("topics"))

    elif request.method != "POST":
        return render_template("edit_further_reading.html", reading=reading,
                               topics=topics)

    else:
        adjust = {
            "topic_name": request.form.get("topic_name"),
            "book_title": request.form.get("book_title"),
            "website": request.form.get("website"),
            "article_title": request.form.get("article_title"),
            "author": request.form.get("author"),
            "date_published": request.form.get("date_published"),
            "publisher": request.form.get("publisher"),
        }
        mongo.db.further_reading.update({"_id": ObjectId(reading_id)}, adjust)
        flash("Material update successful!")

    return redirect(url_for("topics"))


@app.route("/delete_further_reading/<reading_id>")
def delete_further_reading(reading_id):
    """
    Allows admin to delete material from
    the further reading page and removes
    this material from further_reading collection
    in the database as admin sees appropriate.
    """
    reading = mongo.db.further_reading.find_one({"_id": ObjectId(reading_id)})

    if "user" not in session:
        flash("Please Log in to continue")
        return redirect(url_for("login"))

    elif session["user"].lower() != "admin":
        flash("You are not authorized to view this page")
        return redirect(url_for("topics"))
    else:
        mongo.db.further_reading.remove({"_id": ObjectId(reading_id)})
        flash("Material successfully deleted.")
        return redirect(url_for("topics", reading=reading))


@app.route("/filter_reading/further_reading/<topic_id>")
def filter_reading(topic_id):
    """
    Filters further reading based on topic
    so that when it is displayed to the user
    it is relevant to the topic they have clicked on.
    """
    topics = list(mongo.db.topics.find())
    topic = mongo.db.topics.find_one({"_id": ObjectId(topic_id)})

    further_reading = list(mongo.db.further_reading.find(
        {"topic_name": topic["topic_name"]}).sort("_id", -1))
    return render_template("further_reading.html",
                           further_reading=further_reading,
                           topic=topic,
                           topics=topics,
                           page_title="Further Reading")


# @app.errorhandler(500)
# def server_error(error):
# return render_template("500.html", error=error), 500


# @app.errorhandler(404)
# def error404(e):
# return render_template('404.html'), 404


# Change to False before submission
if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)