from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from flask_wtf.file import FileAllowed
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField(
        "Имя пользователя",
        validators=[
            DataRequired(message="Введите имя пользователя."),
            Length(min=3, max=64, message="Имя должно быть от 3 до 64 символов.")
        ]
    )
    password = PasswordField(
        "Пароль",
        validators=[
            DataRequired(message="Введите пароль."),
            Length(min=6, message="Пароль должен быть не короче 6 символов.")
        ]
    )
    confirm_password = PasswordField(
        "Повторите пароль",
        validators=[
            DataRequired(message="Повторите пароль."),
            EqualTo("password", message="Пароли не совпадают.")
        ]
    )
    submit = SubmitField("Зарегистрироваться")

    def validate_username(self, username):
        if User.query.filter_by(username=username.data).first():
            raise ValidationError("Это имя пользователя уже занято.")

class LoginForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")

class RecipeForm(FlaskForm):
    title = StringField("Название рецепта", validators=[DataRequired(), Length(max=200)])
    category = StringField("Категория", validators=[Length(max=80)])
    description = TextAreaField("Краткое описание")
    cooking_time = StringField("Время приготовления")
    ingredients = TextAreaField("Ингредиенты (через запятую)")
    instructions = TextAreaField("Пошаговая инструкция")
    image = FileField(
        "Картинка",
        validators=[
            FileAllowed(["jpg","jpeg","png","gif"],
                        "Только изображения!")
        ]
    )
    submit = SubmitField("Сохранить")

class CommentForm(FlaskForm):
    text = TextAreaField("Комментарий", validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField("Отправить")