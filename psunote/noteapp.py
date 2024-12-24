import flask

import models
import forms
import datetime


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/delete/<int:note_id>", methods=["POST"])
def notes_delete(note_id):
    db = models.db
    note = db.session.get(models.Note, note_id)
    
    if note is None:
        flask.flash("Note not found!", "error")
        return flask.redirect(flask.url_for("index"))
    
    db.session.delete(note)
    db.session.commit()
    
    flask.flash("Note deleted successfully!", "success")
    return flask.redirect(flask.url_for("index"))


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()
    
    return flask.redirect(flask.url_for("index"))


@app.route('/submit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    db = models.db
    note = db.session.get(models.Note, id)
    if flask.request.method == 'POST':
        title = flask.request.form['title']
        description = flask.request.form['description']
        tags = flask.request.form['tags']

        note.title = title
        note.description = description
        note.tags[0].name = tags
        note.updated_date = datetime.datetime.now()
        db.session.add(note)
        db.session.commit()
        return flask.redirect(flask.url_for('success')) 
    return flask.render_template('index.html')  


@app.route('/success')
def success():
    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>", methods=["GET", "POST"])
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )
    
    
@app.route("/tags/delete/<int:tag_id>", methods=["POST"])
def tags_delete(tag_id):
    db = models.db
    tag = db.session.get(models.Tag, tag_id)

    note_ids = db.session.query(models.Note.id).all()
    note_ids_list = [note_id[0] for note_id in note_ids]
    for note_id in note_ids_list:
        note = db.session.get(models.Note, note_id)
        if note.tags[0].id == tag.id:
            db.session.delete(note)
            db.session.commit()

    if tag is None:
        flask.flash("Tag not found!", "error")
        return flask.redirect(flask.url_for("index"))
    
    db.session.delete(tag)
    db.session.commit()
    
    flask.flash("Tag deleted successfully!", "success")
    return flask.redirect(flask.url_for("index"))


@app.route("/tags/edit/<int:tag_id>", methods=["POST"])
def tags_edit(tag_id):
    db = models.db
    tag = db.session.get(models.Tag, tag_id)
    tags = flask.request.form['tag']

    tag.name = tags
    
    db.session.commit()

    return flask.redirect(flask.url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
