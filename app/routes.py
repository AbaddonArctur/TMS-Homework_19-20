import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import User, Recipe, Comment
from app.forms import RegistrationForm, LoginForm, RecipeForm, CommentForm
from app.utils import allowed_file, save_and_resize_image

main = Blueprint("main", __name__)

@main.route("/")
def index():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 6

    query = Recipe.query

    if q:
        query = query.filter(
            (Recipe.title.ilike(f"%{q}%")) |
            (Recipe.ingredients.ilike(f"%{q}%")) |
            (Recipe.category.ilike(f"%{q}%"))
        )
    if category:
        query = query.filter(Recipe.category.ilike(f"%{category}%"))

    pagination = query.order_by(Recipe.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    recipes = pagination.items

    return render_template(
        "index.html",
        recipes=recipes,
        pagination=pagination,
        q=q,
        category=category
    )

@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Регистрация прошла успешно! Теперь войдите.", "success")

        return redirect(url_for("main.login"))

    return render_template("register.html", form=form)

@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    error = None

    if request.method == "POST":
        if not form.username.data or not form.password.data:
            error = "Введите имя пользователя и пароль."
        else:
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.check_password(form.password.data):
                error = "Неверное имя пользователя или пароль."
            else:
                login_user(user)
                flash("Вы успешно вошли!", "success")
                return redirect(url_for("main.index"))

    return render_template("login.html", form=form, error=error)

@main.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("main.index"))

# Add recipe (only authenticated)
@main.route("/recipe/add", methods=["GET", "POST"])
@login_required
def add_recipe():
    form = RecipeForm()

    if form.validate_on_submit():
        image_filename = None
        thumb_filename = None
        file = form.image.data
        if file and allowed_file(file.filename):
            image_filename, thumb_filename = save_and_resize_image(file, base_name=form.title.data.replace(" ", "_"))

        recipe = Recipe(
            title=form.title.data,
            category=form.category.data,
            description=form.description.data,
            cooking_time=form.cooking_time.data,
            ingredients=form.ingredients.data,
            instructions=form.instructions.data,
            image_filename=image_filename,
            thumb_filename=thumb_filename,
            author=current_user
        )

        db.session.add(recipe)
        db.session.commit()
        flash("Рецепт успешно добавлен!", "success")

        return redirect(url_for("main.index"))

    return render_template(
        "add_recipe.html",
        form=form,
        max_size_kb=current_app.config['MAX_CONTENT_LENGTH'] // 1024
    )

@main.route("/recipe/<int:recipe_id>", methods=["GET", "POST"])
def recipe_detail(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    form = CommentForm()

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Только зарегистрированные пользователи могут оставлять комментарии.", "warning")
            return redirect(url_for("main.login"))

        comment = Comment(text=form.text.data, author=current_user, recipe=recipe)
        db.session.add(comment)
        db.session.commit()
        flash("Комментарий добавлен.", "success")

        return redirect(url_for("main.recipe_detail", recipe_id=recipe.id))

    comments = Comment.query.filter_by(recipe_id=recipe.id, parent_id=None).order_by(Comment.created_at.desc()).all()

    return render_template("recipe_detail.html", recipe=recipe, form=form, comments=comments)


@main.route("/comment/<int:comment_id>/reply", methods=["POST"])
@login_required
def reply_comment(comment_id):
    parent = Comment.query.get_or_404(comment_id)
    recipe = parent.recipe
    text = request.form.get("text")

    if not text:
        flash("Комментарий не может быть пустым.", "warning")
        return redirect(url_for("main.recipe_detail", recipe_id=recipe.id))

    reply = Comment(text=text, author=current_user, recipe=recipe, parent=parent)
    db.session.add(reply)
    db.session.commit()
    flash("Ответ добавлен.", "success")

    return redirect(url_for("main.recipe_detail", recipe_id=recipe.id))


@main.route("/recipe/<int:recipe_id>/edit", methods=["GET", "POST"])
@login_required
def edit_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)

    if recipe.author != current_user:
        abort(403)
    form = RecipeForm(obj=recipe)

    if form.validate_on_submit():
        recipe.title = form.title.data
        recipe.category = form.category.data
        recipe.description = form.description.data
        recipe.cooking_time = form.cooking_time.data
        recipe.ingredients = form.ingredients.data
        recipe.instructions = form.instructions.data
        file = form.image.data
        if file and allowed_file(file.filename):
            image_filename, thumb_filename = save_and_resize_image(file, base_name=form.title.data.replace(" ", "_"))
            recipe.image_filename = image_filename
            recipe.thumb_filename = thumb_filename
        db.session.commit()
        flash("Рецепт обновлён!", "success")

        return redirect(url_for("main.recipe_detail", recipe_id=recipe.id))

    return render_template("edit_recipe.html", form=form, recipe=recipe)


@main.route("/recipe/<int:recipe_id>/delete", methods=["POST"])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)

    if recipe.author != current_user:
        flash("Вы можете удалять только свои рецепты.", "danger")
        return redirect(url_for("main.recipe_detail", recipe_id=recipe.id))

    try:
        if recipe.image_filename:
            os.remove(os.path.join(current_app.config["UPLOAD_FOLDER"], recipe.image_filename))
        if recipe.thumb_filename:
            os.remove(os.path.join(current_app.config["UPLOAD_FOLDER"], recipe.thumb_filename))
    except Exception:
        pass

    db.session.delete(recipe)
    db.session.commit()
    flash("Рецепт удалён.", "info")

    return redirect(url_for("main.index"))

@main.route("/comment/<int:comment_id>/delete", methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    recipe_id = comment.recipe_id

    if comment.author != current_user:
        flash("Вы можете удалять только свои комментарии.", "danger")
        return redirect(url_for("main.recipe_detail", recipe_id=recipe_id))

    db.session.delete(comment)
    db.session.commit()

    flash("Комментарий удалён.", "info")
    return redirect(url_for("main.recipe_detail", recipe_id=recipe_id))