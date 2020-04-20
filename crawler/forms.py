from flask_wtf import FlaskForm
from wtforms import fields, widgets, validators
from wtforms.validators import DataRequired


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
            ('0', '不限'),
            ('1', '男'),
            ('2', '女'),
        ],
        validators=[DataRequired()],
    )

    sex = fields.SelectField(
        '租客 性別要求',
        choices=[
            ('0', '不限'),
            ('1', '男'),
            ('2', '女'),
        ],
        validators=[DataRequired()],
    )

    role_type = fields.SelectField(
        '刊登者角色',
        choices=[
            ('0', '非屋主'),
            ('1', '屋主'),
        ],
    )

    linkman = fields.StringField(
        '聯繫人/屋主 姓名(最長四個字符，會使屋主性別選項失效)',
        [validators.Length(max=4, message='Please provide at most 4 characters')]
    )

    tel = fields.StringField(
        '電話'
    )

    submit = fields.SubmitField('查詢')
