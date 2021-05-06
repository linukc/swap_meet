from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField, FloatField, FileField
import wtforms.validators as val
from flask_wtf.file import FileAllowed, FileRequired
from forms.custom_flask_wtf_validators import known_location

class ProductsForm(FlaskForm):
    title = StringField('Заголовок', validators=[val.DataRequired()])
    description = TextAreaField("Описание")
    location = StringField('Местоположение', validators=[val.DataRequired(), known_location])
    price = FloatField('Цена', validators=[val.DataRequired(), val.number_range(min=0)])
    photo = FileField('Изображение', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    is_private = BooleanField("Личное")
    submit = SubmitField('Применить')
