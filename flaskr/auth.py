import functools
import sys

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required'
        if not password:
            error = 'Password is required'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
                print('Se ha registrado correctamente!', file=sys.stderr)
            except db.IntegrityError:
                error = f"User {username} is already registered."
            else:
                return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        error = None
        user = db.execute(
            "SELECT * FROM user WHERE username = ?", (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            
            print('Se ha iniciado session correctamente!', file=sys.stderr)
            return redirect(url_for('index'))

        flash(error)
    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ? ', (user_id,)
        ).fetchone()


@bp.route('/logout')
def logout():
    print(f"Se ha cerrado la session: {g.user['username']}", file= sys.stderr)
    session.clear()
    
    return redirect(url_for('index'))


# Este decorador retorna una nueva funcion vista que envuelve a la vista original
# a la cual ha sido aplicada
# la nueva funcion verifica si un usuario esta cargado y lo redirecciona
# a la pagina de login si es que no hay alguno.
# Si un usuario ha sido cargado el decorador llama a la vista original y continua
# su ejecucion normalmente.
# El nombre asociado a una vista es tambien llamado END-POINT
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view
