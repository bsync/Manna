from flask import render_template
from main import app
from forms import LoginForm, MenuForm

page_titles = "home login events"

# Index
@app.route('/', methods=['GET'])
def app_index():
    return render_template('home.html', config=app.config)

@app.route('/login', methods=['GET'])
def login():
    form = LoginForm()
    return render_template('login.html', title='Sign In', form=form)

@app.route('/edmenu', methods=['GET', 'POST'])
def edit_menus():
    form = MenuForm()
    ptitles = page_titles.split()
    pchoices = zip(ptitles, [ p[0].upper() + p[1:] for p in ptitles ])
    form.pageSelectField.choices=pchoices
    return render_template('edmenu.html', form=form)

