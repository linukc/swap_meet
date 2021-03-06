from flask import Flask, render_template, redirect, request, abort, url_for, send_from_directory, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import imghdr
import io
import requests
from cloudipsp import Api, Checkout
from sqlalchemy import func, any_, or_

from forms.products import ProductsForm
from forms.user import RegisterForm, LoginForm
from data.products import Products
from data.users import User
from data import db_session
from forms.custom_flask_wtf_validators import know_location

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'secret_key'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 #1 MB image max size
app.config['UPLOAD_PATH'] = os.path.join('static','uploads')
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/icon'),
                               'favicon.ico', mimetype='image/gif')


@app.errorhandler(413) #image max size error handler
def too_large(e):
    return "File is too large; max 0.5 MB", 413


@app.errorhandler(404) #debug
def too_large(e):
    print(e)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data,
            location=form.location.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/")
def index():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        products = db_sess.query(Products).filter(Products.is_private != True, Products.user != current_user)
    else:
        products = db_sess.query(Products).filter(Products.is_private != True)
    return render_template("index.html", products_for_sale=products,
                                         searchbar_title='Search...')


@app.route("/my_products")
@login_required
def my_products():
    db_sess = db_session.create_session()
    products_invisible = db_sess.query(Products).filter(Products.user == current_user, Products.is_private == True)
    products_visible = db_sess.query(Products).filter(Products.user == current_user, Products.is_private != True)
    return render_template("index.html", products_invisible=products_invisible,
                                         products_visible=products_visible)


@app.route('/product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()

        product = Products()
        product.title = form.title.data
        product.description = form.description.data
        product.location = form.location.data
        product.price = form.price.data
        product.is_private = form.is_private.data
        product.category = form.category.data

        #save image  
        f = form.photo.data
        if f:
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_PATH'], filename))
            product.photo = filename

        #тут через раз падает с багом lazy
        current_user.products.append(product)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/my_products')
    return render_template('product.html', title='Добавление товара', form=form)


@app.route('/product_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def products_delete(id):
    db_sess = db_session.create_session()
    product = db_sess.query(Products).filter(Products.id == id, Products.user == current_user).first()
    if product:
        db_sess.delete(product)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/my_products')


@app.route('/product_pub/<int:id>', methods=['GET'])
@login_required
def products_publish(id):
    db_sess = db_session.create_session()
    product = db_sess.query(Products).filter(Products.id == id, Products.user == current_user).first()
    if product.is_private:
        product.is_private=False
        db_sess.commit()
    else:
        abort(404)
    return redirect('/my_products')


@app.route('/product_hide/<int:id>', methods=['GET'])
@login_required
def products_hide(id):
    db_sess = db_session.create_session()
    product = db_sess.query(Products).filter(Products.id == id, Products.user == current_user).first()
    if not product.is_private:
        product.is_private=True
        db_sess.commit()
    else:
        abort(404)
    return redirect('/my_products')


@app.route('/product/<int:id>/map', methods=['GET'])
def product_map(id):
    db_sess = db_session.create_session()
    product = db_sess.query(Products).filter(Products.id == id).first()

    longi, latt = know_location(req=product.location)
    map_params = {
                  "size": ",".join(['450', '450']),
                  "l": "map",
                  "pt":f"{longi},{latt},flag"}
    if current_user.is_authenticated:
        longi_user, latt_user = know_location(req=current_user.location)
        map_params['pt'] += f'~{longi_user},{latt_user},home'
    else:
        map_params['z'] = 13

    r = requests.get("http://static-maps.yandex.ru/1.x/", params = map_params)
    return redirect(r.url)


@app.route('/product/<int:id>/buy', methods=['GET'])
def product_payment(id):
    db_sess = db_session.create_session()
    product = db_sess.query(Products).filter(Products.id == id).first()

    api = Api(merchant_id=1396424,
              secret_key='test')

    checkout = Checkout(api=api)

    data = {
        "currency": "RUB",
        "amount": int(product.price)*100
    }
    url = checkout.url(data).get('checkout_url')
    return redirect(url)


@app.route('/product/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    form = ProductsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        product = db_sess.query(Products).filter(Products.id == id, Products.user == current_user).first()
        if product:
            form.title.data = product.title
            form.description.data = product.description
            form.location.data = product.location
            form.is_private.data = product.is_private
            form.price.data = product.price
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        product = db_sess.query(Products).filter(Products.id == id, Products.user == current_user).first()
        if product:
            product.title = form.title.data
            product.description = form.description.data
            product.location = form.location.data
            product.price = form.price.data
            product.is_private = form.is_private.data
            product.category = form.category.data

            #save image  
            f = form.photo.data
            if f:
                filename = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_PATH'], filename))
                product.photo = filename
                
            db_sess.commit()
            return redirect('/my_products')
        else:
            abort(404)
    return render_template('product.html', title='Редактирование товара', form=form)


@app.route('/user_profile', methods=['GET', 'POST'])
@login_required
def edit_user():
    form = RegisterForm()
    if request.method == "GET":
        form.email.data = current_user.email
        form.name.data = current_user.name
        form.about.data = current_user.about
        form.location.data = current_user.location
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        if user:
            user.name=form.name.data
            user.email=form.email.data
            user.about=form.about.data
            user.location=form.location.data
            user.set_password(form.password.data)  
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('register.html', title='Редактирование профиля', form=form)

 
@app.route('/search', methods=['GET','POST'])
def search():
    if request.method == 'POST':
        db_sess = db_session.create_session()

        search_req = request.form.get('searchbar')
        sql_search_req = [str.lower(f'''%{i}%''') for i in search_req.split()]

        if current_user.is_authenticated:
            products = db_sess.query(Products).filter(Products.is_private != True, 
                                                  or_(*[func.lower(Products.title).like(i) for i in sql_search_req]),
                                                  Products.user != current_user)
        else:
            products = db_sess.query(Products).filter(Products.is_private != True, 
                                                  or_(*[func.lower(Products.title).like(i) for i in sql_search_req]))
    return render_template("index.html", products_for_sale=products, 
                                         searchbar_title=f"Результаты по запросу: {search_req}")


def main():
    db_session.global_init("db/store.db")
    app.run()


if __name__ == '__main__':
    main()
