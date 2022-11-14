import sys
from flask import (
    Blueprint, flash, g,
    redirect, render_template, request, url_for
)

from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p join user u on p.author_id = u.id'
        ' order by created desc'
    ).fetchall()

    return render_template('blog/index.html', posts=posts)

@bp.route('/')
def edit_post():
    return render_template('blog/update.html')


@bp.route('/create', methods=('GET','POST'))
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required'
        if not body:
            error = 'Body is required'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_post(id, check_autor=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p join user u on p.author_id = u.id'
        ' where p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} desn't exists.")

    if check_autor and post['author_id'] != g.user['id']:
        abort(403)
    return post

@bp.route('/<int:id>/update', methods=('GET','POST'))
@login_required
def update(id):
    post = get_post(id)
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'There must be a title'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post set title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            print('Post actualizado correctamente', file=sys.stderr)
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html')

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))



