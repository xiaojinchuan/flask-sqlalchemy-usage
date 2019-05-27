from typing import Union, List
from flask_sqlalchemy import SQLAlchemy, BaseQuery, Model
from sqlalchemy.schema import CreateTable
from sqlalchemy.ext.compiler import compiles

from flask import Flask
app = Flask(__name__)
#    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:qwer1234@127.0.0.1:3306/test_db?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_RECORD_QUERIES'] = True
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app, session_options={'autocommit': False})


def new_view_ddl(*entities):
    """
    replacement of db.session.query
    Can't use db.session.query, as there is no session on start
    :param entities:
    :return:
    """
    return BaseQuery(entities)


class ViewTable:
    def __init__(self, *, view_ddl: Union[str, BaseQuery], dependencies: List[Model]):
        if not view_ddl or not dependencies:
            raise ValueError
        self.__view_ddl = view_ddl
        self.__dependencies = dependencies

    def __call__(self, cls):
        cls.__table__.info['is_view'] = True
        cls.__table__.info['view_ddl'] = self.__view_ddl
        for d in self.__dependencies:
            cls.__table__.add_is_dependent_on(d.__table__)

        return cls

# How to create a view:
# declare a view as table with sqlalchemy
# and decorate it with ViewTable
# You need to specify the ddl to create the view and the tables it depends on.
@compiles(CreateTable)
def compile_table(element, compiler, **kw):
    table = element.element
    if table.info.get('is_view', False):
        sql = table.info["view_ddl"]
        if not isinstance(sql, str):
            sql = sql.statement.compile(dialect=db.engine.dialect, compile_kwargs={"literal_binds": True})
            sql = f"CREATE VIEW `{table.name}` AS {sql}"
    else:
        sql = compiler.visit_create_table(element, **kw)
    return sql


if __name__ == "__main__":

    class ATable(db.Model):
        __tablename__ = 'a_table'
        id = db.Column(db.Integer, primary_key=True)
        x = db.Column(db.Integer)
        y = db.Column(db.Integer)

    class BTable(db.Model):
        __tablename__ = 'b_table'
        id = db.Column(db.Integer, primary_key=True)
        a_id = db.Column(db.Integer)
        m = db.Column(db.String(32))
        n = db.Column(db.String(32))

    @ViewTable(
        view_ddl=new_view_ddl(
            ATable.id,
            ATable.x.label('a_x'),
            ATable.y.label('a_y'),
            BTable.m,
            BTable.n
        ).outerjoin(BTable, BTable.a_id == ATable.id),
        dependencies=[ATable, BTable]
    )
    class ABView(db.Model):
        __tablename__ = 'a_and_b_view'
        id = db.Column(db.Integer, primary_key=True)
        a_x = db.Column(db.Integer)
        a_y = db.Column(db.Integer)
        m = db.Column(db.String(32))
        n = db.Column(db.String(32))


    db.create_all()
    db.session.add(ATable(id=1, x=100, y=200))
    db.session.add(BTable(id=1, a_id=1, m='mmm', n='nnn'))
    db.session.commit()

    v = db.session.query(ABView).filter(ABView.m == 'mmm').first()
    
    assert v.a_x == 100
    assert v.a_y == 200
    assert v.m == 'mmm'
    assert v.n == 'nnn'

