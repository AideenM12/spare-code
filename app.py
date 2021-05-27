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