from Infinity import app, database
from Infinity.models import User, Calendar, File, Task

with app.app_context():
    database.drop_all()
    database.create_all()
    database.session.commit()