from flask import flash, redirect, render_template, url_for
from flask_login import login_user, logout_user, login_required

from app.auth import auth_bp
from app.auth.forms import LoginForm, RegistrationForm
from app.extensions import db
from app.models import User


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        existing_username = User.query.filter_by(
            username=form.username.data
        ).first()

        if existing_username:
            flash("That username is already taken.", "danger")
            return render_template("auth/register.html", form=form)

        existing_email = User.query.filter_by(
            email=form.email.data
        ).first()

        if existing_email:
            flash(
                "An account with this email already exists.",
                "danger"
            )
            return render_template("auth/register.html", form=form)

        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip().lower()
        )

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash(
            "Account created successfully. Please log in.",
            "success"
        )

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data.strip().lower()
        ).first()

        if user and user.check_password(form.password.data):
            login_user(user)

            flash(
                "You have logged in successfully.",
                "success"
            )

            return redirect(url_for("dashboard.index"))

        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template(
        "auth/login.html",
        form=form
    )
@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(url_for("auth.login"))