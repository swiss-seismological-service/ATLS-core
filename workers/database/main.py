import flask
import flask.ext.sqlalchemy
import flask.ext.restless

app = flask.Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////vagrant/ramsis/basel.rms'
db = flask.ext.sqlalchemy.SQLAlchemy(app)


class ModelResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    failed = db.Column(db.Boolean)
    failure_reason = db.Column(db.String)
    t_run = db.Column(db.DateTime)
    dt = db.Column(db.Float)
    rate = db.Column(db.Float)
    b_val = db.Column(db.Float)
    prob = db.Column(db.Float)


db.create_all()
manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(ModelResult, methods=['GET', 'POST'])
app.run(port=5001)
