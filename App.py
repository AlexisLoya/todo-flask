from flask import Flask, render_template, request, redirect, url_for, flash, make_response, session
from flask_mysqldb import MySQL
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from forms import LoginForm, DeleteTodoForm, UpdateTodoForm, TodoForm, ChangePassword
from config import Config
# initializations
app = Flask(__name__)

# Mysql Connection
app.config['MYSQL_HOST'] = 'todos-database.cj4midcurokg.us-east-1.rds.amazonaws.com'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = 'admin123'
app.config['MYSQL_DB'] = 'todo_list'
#Bootstrap
bootstrap = Bootstrap(app)

app.config.from_object(Config)

#Mysql
mysql = MySQL(app)


# routes
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html', error=error)


@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html', error=error)


@app.route('/')
def Index():
    user_ip = request.remote_addr
    session['user_ip'] = user_ip
    return make_response(redirect('/login'))

@app.route('/hello', methods=['GET', 'POST'])
def hello():
    #tomar cookie del response
    user_ip = session.get('user_ip')
    name = session.get('name')
    #todos
    cur = mysql.connection.cursor()
    cur.execute('SELECT id_user, name, id_todos, descripcion, complet from todo_list.users join todos t on users.id_user = t.user_id WHERE name=%s'
    , ([name]))
    todos = cur.fetchall()
    session['todos'] = todos
    
    todo_form = TodoForm()
    delete_form = DeleteTodoForm()
    update_form = UpdateTodoForm()
    #diccionario
    context = {
        'user_ip': user_ip,
        'name':name,
        'todo_form': todo_form,
        'delete_form': delete_form,
        'update_form': update_form,
        'todos':todos
    }
    if todo_form.validate_on_submit():     
        try:
            description = str(todo_form.description.data)
            user_id = session.get('user_id')
            #user_id = int(user_id[0])
            print('id_user ---->',[user_id])
            print(type(user_id))
            print('description ---->',description)
            print(type(description))
            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO todo_list.todos (user_id, descripcion) VALUES (%s,%s)', (user_id, description))
            mysql.connection.commit()
            #flash
            flash('Tarea registrada','success')
            return redirect(url_for('hello'))
        except Exception as e:
            print(e)
            #flash
            flash('Ocurrió un error','danger')

    return render_template('hello.html', **context)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    login_form = LoginForm()
    context = {
        'signup_form':LoginForm()
    }
    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data
        try:
            cur = mysql.connection.cursor()
            cur.execute('INSERT INTO todo_list.users (name, password) VALUES (%s,%s)', (username, password))
            mysql.connection.commit()
            #flash
            flash('Nombre de usuario registrado con exito','success')
            cur.execute('SELECT id_user from todo_list.users WHERE name=%s', ([username]))
            user_id = cur.fetchall()
            session['user_id'] = user_id[0]
            session['name'] = username
            session['password'] = password
            return redirect(url_for('hello'))
        except Exception as e:
            print(e)
            #flash
            flash('Nombre de usuario ya esta registrado','warning')
        return redirect(url_for('Index'))

    return render_template('signup.html', **context)

@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()
    context = {
        'login_form':LoginForm()
    }
    if login_form.validate_on_submit():
        username = login_form.username.data
        password = login_form.password.data
        print(1)
        try:
            print(1.1)
            curl = mysql.connection.cursor()
            curl.execute("SELECT * FROM todo_list.users WHERE name=%s",([username]))
            user = curl.fetchone()
            user_password = str(user[2])
            print(user_password, 'type:',type(user_password))
            print(password, 'type:',type(password))
            curl.close()
            print(2)
            if len(user) > 0:
                print(3)
                if user[2] == password:
                    print(4)
                    session['user_id'] = user[0]
                    session['name'] = user[1]
                    session['password'] = user[2]
                    flash('Bienvenido!','success')
                    return redirect(url_for('hello'))
                flash('Usuario o contraseña incorrectos', 'warning')
                return redirect(url_for('login'))
            else:
                flash('El usuario no existe', 'danger')
                return redirect(url_for('Index'))
        except  Exception as e:
            print(e)
            #flash
            flash('El usuario no existe', 'danger')
        return redirect(url_for('Index'))

    return render_template('login.html', **context)

@app.route('/logout')
def logout():
    session.clear()
    return make_response(redirect('/'))


@app.route('/edit/<id>', methods = ['POST', 'GET'])
def get_contact(id):
    cur = mysql.connection.cursor()
    cur.execute('UPDATE todo_list.todos SET complet=1 WHERE id_todos=%s',[id])
    mysql.connection.commit()
    flash('tarea terminada','success')
    return redirect(url_for('hello'))


@app.route('/delete/<string:id>', methods = ['POST','GET'])
def delete_contact(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM todo_list.todos WHERE id_todos = {0}'.format(id))
    mysql.connection.commit()
    flash('tarea Eliminada','warning')
    return redirect(url_for('hello'))


@app.route('/perfil/<id>', methods = ['POST','GET'])
def perfil(id):
    name = session.get('name')
    user_id = session.get('user_id')
    change_password = ChangePassword()
    context = {
        'name':name,
        'change_password':change_password
    }
    if change_password.validate_on_submit():
        password = change_password.password.data
        repeat_password = change_password.repeat_password.data
        if password == repeat_password:
            cur = mysql.connection.cursor()
            cur.execute('UPDATE todo_list.users SET password=%s WHERE id_user=%s',[password,id])
            mysql.connection.commit()
            flash('Contraseña actualizada','success')
            return redirect(url_for('hello'))
        flash('Las contraseñas no coinciden', 'warning')
        return render_template('profile.html', **context)
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM todo_list.users WHERE id_user =%s',[id])
        mysql.connection.commit()
        flash('Cuenta eliminada', 'danger')
        session.clear()
        return make_response(redirect('/'))

    return render_template('profile.html', **context)
    
'''

'''
# starting the app
if __name__ == "__main__":
    app.run(port=8080, debug=True)
