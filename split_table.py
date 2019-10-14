from typing import Type
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy, Model

db = SQLAlchemy(app, session_options={'autocommit': False})

_created_tables = {}

# 父类, 定义表字段
class ParentModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# 根据tablename生成相应的表
def gen_model_type(tablename: str) -> Type[ParentModel]
    if tablename in _created_tables:
        return _created_tables[tablename]

    model_class = type(
        tablename+'_Model',
        (ParentModel,),
        dict(__tablename__=tablename)
    )
    model_class.__table__.create(db.session.bind, checkfirst=True)
    _created_tables[tablename] = model_class
    return model_class

