@app.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method == "POST":
        # check if username is already in use
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("This username already exists")
            return redirect(url_for("registration")) 

        sign-up{
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")).lower(),
            "email": request.form.get("email")
        }
    return render_template("sign-up.html")

    @app.route("/login")
def login():
    try:
        form = RegistrationForm(request.form)

        return render_template("login.html")

if "user" not in session:
        flash("Please Log in to continue")
        return redirect(url_for("login"))

 flash("You are not authorized to view this page")
        return redirect(url_for("profile"))



 else:
        topic_name = list(mongo.db.topics.find().sort("topic_name", 1))
        topics = list(mongo.db.articles.find())
        article = mongo.db.articles.find()
        articles = {}
        for topic in topics:
            if topic["article"] in topics:
                articles["topic"].append(topic._id)
            else:
                print(topic["_id"])
                articles["topic_id"] = topic["_id"]

        return render_template("topics.html",
                               topics=topics,
                               articles=articles,
                               article=article,
                               topic_name=topic_name)









@app.route("/topics")
def topics():
    if "user" not in session:
        flash("Please Log in to continue")
        return redirect(url_for("login"))
    else:
        topics = list(mongo.db.topics.find().sort("topic_name", 1))
        return render_template("topics.html", topics=topics)

 topics = list(mongo.db.articles.find())
       
        for topic in topics:
            if topic["topic_name"] in topics:
                topics["topic"].append(topic._id)
            else:
                print(topic["_id"])
                topics["topic_id"] = topic["_id"]



Then that's your challenge for this evening: add some articles to populate it, or find a different way to filter articles by topic (since topic_name is a field on article