from flask_wtf import FlaskForm
from wtforms import fields, widgets, validators
from wtforms.validators import DataRequired, Optional
from werkzeug.urls import url_encode


class MultiCheckboxField(fields.SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class QueryForm(FlaskForm):
    regionid = fields.SelectField(
        '縣市',
        choices=[
            ('1', '台北市'),
            ('3', '新北市'),
        ],
        validators=[DataRequired()],
    )

    lessor_sex = fields.SelectField(
        '聯繫人/屋主 性別',
        choices=[
            ('2', '不限'),
            ('0', '女'),
            ('1', '男'),
        ],
        validators=[DataRequired()],
    )

    sex = fields.SelectField(
        '租客 性別要求',
        choices=[
            ('2', '不限'),
            ('0', '女'),
            ('1', '男'),
        ],
        validators=[DataRequired()],
    )

    role_type = fields.SelectField(
        '刊登者角色',
        choices=[
            ('3', '不限'),
            ('0', '屋主'),
            ('1', '代理人'),
            ('2', '仲介'),
        ],
    )

    linkman = fields.StringField(
        '聯繫人/屋主 姓名(最長四個字符，會使屋主性別選項失效)',
        [validators.Length(max=4, message='Please provide at most 4 characters')]
    )

    tel = fields.StringField(
        '電話'
    )

    price_upper = fields.IntegerField(
        '租金上限', validators=[
            Optional(
                strip_whitespace=True)])

    price_lower = fields.IntegerField(
        '租金下限', validators=[
            Optional(
                strip_whitespace=True)])

    area_upper = fields.IntegerField(
        '坪數上限', validators=[
            Optional(
                strip_whitespace=True)])

    area_lower = fields.IntegerField(
        '坪數下限', validators=[
            Optional(
                strip_whitespace=True)])

    submit = fields.SubmitField('查詢')

    def to_dict(self):
        obj = {}
        for attr, value in self.__dict__['_fields'].items():
            if attr != 'submit' and attr != 'csrf_token' and value.data is not None:
                obj[attr] = value.data
        return obj
