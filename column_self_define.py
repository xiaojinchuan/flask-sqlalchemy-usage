"""
在mysql5.7中使用JSON列
为JSON列中某些内容创建虚拟列，并为此虚拟列建立索引，以方便查询
"""

from sqlalchemy.schema import CreateColumn
from sqlalchemy.ext.compiler import compiles


@compiles(CreateColumn, 'mysql')
def mysql_genereted_column(element, compiler, **kwargs):
    """
    如果字段定义中含有generated_with, 将根据info中的generate方法修改创建列的过程
    mysql 指此函数只对mysql有效
    :param element:
    :param compiler:
    :param kwargs:
    :return:
    """
    column = element.element
    if 'generated_with' not in column.info:
        return compiler.visit_create_column(element, **kwargs)

    column_def = f'{compiler.visit_create_column(element, **kwargs)} ' \
        f'GENERATED ALWAYS AS ({column.info["generated_with"]}) VIRTUAL'

    return column_def


if __name__ == "__main__":
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy, orm
    from sqlalchemy import func, text, Column, FetchedValue

    app = Flask(__name__)
#    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:qwer1234@127.0.0.1:3306/test_db?charset=utf8mb4'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_RECORD_QUERIES'] = True
    app.config['SQLALCHEMY_ECHO'] = True

    db = SQLAlchemy(app, session_options={'autocommit': False})

    class TestModel(db.Model):
        id = Column(db.Integer, primary_key=True)
        name = Column(db.String(64))
        data = Column(db.JSON)
        # 这里创建一个写明要generate的列，这列的内容取自JSON列data中的'K'字段, 并创建索引
        K = Column(db.Integer, FetchedValue(), index=True, info={'generated_with': "json_extract(data, '$.K')"})


    db.create_all()
    db.session.add(TestModel(id=1, name='name', data={'K': 3}))
    db.session.commit()

    k = db.session.query(TestModel.K).filter(TestModel.id == 1).first()[0]
    assert k == 3

