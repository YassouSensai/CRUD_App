from flask import Flask, request, render_template, redirect, send_file, Blueprint, url_for, flash, abort, session
from datetime import datetime

from toudou.models import create_todo, get_all_todos, get_todo, update_todo, delete_todo, get_todo_by_name, init_db
from toudou.services import import_from_csv, export_to_csv

from toudou.models import TodoForm, SearchForm
from dotenv import load_dotenv

import logging
import io
import os
import csv

from werkzeug.security import generate_password_hash, check_password_hash
from flask_httpauth import HTTPBasicAuth



#####################################################################################################
######################################## Première partie ############################################
#####################################################################################################


############################################ Définitions ############################################
web_ui = Blueprint("web_ui", __name__, url_prefix="/")

@web_ui.route("/<page>")
def show(page):
    return render_template(f"pages/{page}.html")


####################################### Configuration de logging ####################################
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("toudou.log"),
        logging.StreamHandler()
    ]
)


############################################ Pour les erreurs ############################################
@web_ui.errorhandler(500)
def handle_internal_error(error):
    flash("Erreur interne du serveur", "error")
    logging.exception(error)  # Enregistrer l'exception dans les logs
    return redirect(url_for("web_ui.show", page="home"))

@web_ui.errorhandler(403)
def handle_forbidden_error(error):
    flash("Vous n'êtes pas autorisé à accéder à cette fonctionnalité.", "error")
    logging.exception(error)
    message = "Veuillez vous identifier en tant qu'administrateur !!! " \
              "En tant qu'utilisateur lambda, vous n'êtes pas autorisé à accéder à cette fonctionnalité. "\
              "En d'autres termes, vous avez la possibilité de :"

    return render_template("home.html", message=message), 403


########################################### Authentification #########################################
users = {
    "admin": generate_password_hash("admin"),
    "user": generate_password_hash("user")
}
auth = HTTPBasicAuth()


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = os.getenv("TOUDOU_FLASK_SECRET_KEY", "secret!")
    app.register_blueprint(web_ui)

    @auth.verify_password
    def verify_password(username, password):
        if username in users and check_password_hash(users.get(username), password):
            session['username'] = username
            return True

    return app


def get_role():
    return "admin" if session.get('username') == "admin" else "user"


#####################################################################################################
######################################## Seconde partie #############################################
#####################################################################################################


######################################## Routes principales #########################################
@web_ui.route("/")
@auth.login_required
def index():
    return render_template('home.html')


######################################## Pour la creation ###########################################
@web_ui.route('/create-link', methods=['GET', 'POST'])
@auth.login_required
def createLink():
    form = TodoForm()
    if form.validate_on_submit():
        return redirect('/get-all')
    return render_template('create.html', form=form)


@web_ui.route('/create', methods=['GET', 'POST'])
@auth.login_required
def create_todo_route():
    if get_role() != "admin":
        abort(403)

    form = TodoForm()
    if form.validate_on_submit():
        task = form.task.data
        due = form.due.data
        complete = form.complete.data
        create_todo(task=task, due=due, complete=complete)

        flash('Tâche créée avec succès!', 'success')
        return redirect(url_for('web_ui.get_all_todos_views', message2='Tâche créée avec succès!'))
    return render_template('create.html', form=form)


######################################## Pour la lecture ###########################################
@web_ui.route('/get/<todo_id>')
@auth.login_required
def get_todo_views(todo_id):
    return str(get_todo(todo_id))


@web_ui.route('/search', methods=['GET'])
@auth.login_required
def search_todo():
    form = SearchForm(request.args)
    if form.validate():
        search_query = form.search.data
        if search_query:
            todos = get_todo_by_name(search_query)
        else:
            todos = get_all_todos()
        enumerated_todos = [(index + 1, format_todo_dates(todo)) for index, todo in enumerate(todos)]
        return render_template('list.html', todos=enumerated_todos, search_term=search_query, form=form)
    flash("Veuillez entrer un terme de recherche valide", "error")
    return redirect('/get-all')


@web_ui.route('/get-all')
@auth.login_required
def get_all_todos_views():
    todos = get_all_todos()
    enumerated_todos = [(index + 1, format_todo_dates(todo)) for index, todo in enumerate(todos)]
    form = SearchForm()
    message = request.args.get('message')
    return render_template('list.html', todos=enumerated_todos, form=form, message=message)


def format_todo_dates(todo):
    formatted_due_date = todo.due.strftime("%A %d %B %Y")
    return (todo.task, formatted_due_date, todo.complete, todo.id)


##################################### Importation/Exportation #######################################
@web_ui.route('/import-link')
@auth.login_required
def importLink():
    return render_template('import.html')


@web_ui.route('/import-csv', methods=['POST'])
@auth.login_required
def import_csv():
    if get_role() != "admin":
        abort(403)
    if 'file' not in request.files:
        flash('Aucun fichier sélectionné', 'error')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('Aucun fichier sélectionné', 'error')
        return redirect(request.url)
    if file:
        try:
            import_from_csv(file)
            flash('Importation réussie', 'success')
        except Exception as e:
            flash(f'Erreur lors de l\'importation : {str(e)}', 'error')
            logging.exception(e)  # Enregistrer l'exception dans les logs
    return render_template('home.html', message2='Importation réussie avec succès !')

@web_ui.route('/export-csv')
@auth.login_required
def export_csv():
    csv_data = export_to_csv()
    csv_binary = io.BytesIO(csv_data.getvalue().encode())
    return send_file(
        csv_binary,
        mimetype='text/csv',
        as_attachment=True,
        download_name='todos.csv'  # Spécifiez le nom de fichier personnalisé
    )


######################################## Pour la mise à jour ###########################################
@web_ui.route('/update-link/<todo_id>', methods=['GET'])
@auth.login_required
def updateLink(todo_id):
    todo = get_todo(todo_id)
    form = TodoForm(obj=todo)
    if todo:
        return render_template('update.html', todo=todo, form=form)
    else:
        return "Toudou not found"


@web_ui.route('/update/<todo_id>', methods=['GET', 'POST'])
@auth.login_required
def update_todo_views(todo_id):
    if get_role() != "admin":
        abort(403)
    todo = get_todo(todo_id)
    form = TodoForm(obj=todo)
    if form.validate_on_submit():
        task = form.task.data
        due = form.due.data
        complete = form.complete.data
        update_todo(todo_id, task, complete, due)
        flash('Tâche mise à jour avec succès!', 'success')
        return redirect(url_for('web_ui.get_all_todos_views', message2='Tâche mis à jour avec succès !'))
    return render_template('update.html', form=form, todo=todo)


@web_ui.route('/delete/<todo_id>', methods=['GET'])
@auth.login_required
def delete_todo_views(todo_id):
    if get_role() != "admin":
        abort(403)
    todo = get_todo(todo_id)
    if todo:
        delete_todo(todo_id)
    return redirect(url_for('web_ui.get_all_todos_views', message2='Tâche supprimée avec succès !'))















