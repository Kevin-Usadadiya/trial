import sqlite3
from flask import Flask, render_template, request, flash, redirect, url_for
import random  
import string
import validators


# CONSTANTS
RANDOM_STRING_DEFAULT_LENGTH = 4


app = Flask(__name__)


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


app = Flask(__name__)
app.config['SECRET_KEY'] = 'this should be a secret random string'
# app.config['CSRF_ENABLED'] = True
app.config['SERVER_NAME'] = 'localhost:5000'

def save_url(fullUrl, shortUrl):
    conn = get_db_connection()
    url_data = conn.execute('INSERT INTO urls (original_url, shorten_url) VALUES (?, ?)',
                                    (fullUrl, shortUrl))
    conn.commit()
    conn.close()
    return url_data

def unique_url(short_url):
    conn = get_db_connection()
    db_url = conn.execute('SELECT * FROM urls WHERE shorten_url = (?)', (short_url,)).fetchone()
    return db_url == None

def get_random_string(length = RANDOM_STRING_DEFAULT_LENGTH):  
    letters = string.ascii_lowercase
    result = ''.join((random.choice(letters)) for x in range(length))  
    return result

@app.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        url = request.form['url']
        custom_short_url = request.form['custom_id']                  
        valid= validators.url(url)
        
        if not url:
            flash('The URL is required!')
            return redirect(url_for('index'))
        elif valid != True:
            flash("Invalid url")    
        else:
            if not custom_short_url:
                custom_short_url = get_random_string()
                while not unique_url(custom_short_url):
                    custom_short_url = get_random_string()
            elif not unique_url(custom_short_url):
                flash('The provided shorten url already exist for some other original url.')
                return redirect(url_for('index'))

            
            save_url(url, custom_short_url)

            short_url = request.host_url + custom_short_url

            return render_template('index.html', short_url=short_url)
            
    return render_template('index.html')

@app.route('/<shorten_url>')
def url_redirect(shorten_url):
    conn = get_db_connection()
    if shorten_url:
        url_data = conn.execute('SELECT * FROM urls WHERE shorten_url = (?)', (shorten_url,)).fetchone()
        # In python the select query expects that we return tuple which has one or more values and so we are passing ','
        original_url = url_data['original_url']
        clicks = url_data['clicks']

        conn.execute('UPDATE urls SET clicks = ? WHERE shorten_url = ?',
                     (clicks+1, shorten_url))

        conn.commit()
        conn.close()
        return redirect(original_url)
    else:
        flash('Invalid URL')
        return redirect(url_for('index'))



@app.route('/stats')
def stats():
    conn = get_db_connection()
    db_urls = conn.execute('SELECT id, created, original_url, shorten_url, clicks FROM urls' 
                           ).fetchall()
    conn.close()

    urls = []
    for url in db_urls:
        url = dict(url)
        url['shorten_url'] = request.host_url + url['shorten_url']
        urls.append(url)

    return render_template('stats.html', urls=urls)

@app.route('/delete/<int:id>')
def delete_task(id):
        conn = get_db_connection()
        sql = 'DELETE FROM urls WHERE id=?'
        cur = conn.cursor()
        cur.execute(sql, (id,))
        conn.commit()
        return render_template('index.html',id = id)

@app.route('/delete_all')
def delete_all():
        conn = get_db_connection()
        sql = 'DELETE FROM urls'
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == "__main__":
    app.run(debug=True)