# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import datetime
import io

app = Flask(__name__)
app.secret_key = "your_secret_key"

def create_db():
    conn = sqlite3.connect('links.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS links
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, content TEXT, expire_at DATETIME, is_file INTEGER)''')
    conn.commit()
    conn.close()

def add_link(category, content, expire_at):
    conn = sqlite3.connect('links.db')
    c = conn.cursor()
    if len(content) > 10:
        filename = "{}_{}.txt".format(category, datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
        with io.open(filename, 'w', encoding='utf-8') as f:  # Spécifier l'encodage UTF-8
            f.write(content)  # Écrire le contenu dans le fichier
        c.execute('''INSERT INTO links (category, content, expire_at, is_file) VALUES (?, ?, ?, ?)''', (category, filename, expire_at, 1))
    else:
        c.execute('''INSERT INTO links (category, content, expire_at, is_file) VALUES (?, ?, ?, ?)''', (category, content, expire_at, 0))
    conn.commit()
    conn.close()


def get_active_links():
    conn = sqlite3.connect('links.db')
    c = conn.cursor()
    c.execute('''SELECT category, content, is_file FROM links WHERE expire_at > ?''', (datetime.datetime.now(),))
    active_links = c.fetchall()
    conn.close()

    categorized_links = {}
    for category, content, is_file in active_links:
        if category in categorized_links:
            categorized_links[category].append({'content': content, 'is_file': is_file})
        else:
            categorized_links[category] = [{'content': content, 'is_file': is_file}]
    return categorized_links

def delete_expired_links():
    conn = sqlite3.connect('links.db')
    c = conn.cursor()
    c.execute('''DELETE FROM links WHERE expire_at <= ?''', (datetime.datetime.now(),))
    conn.commit()
    conn.close()

def delete_category(category):
    conn = sqlite3.connect('links.db')
    c = conn.cursor()
    c.execute('''DELETE FROM links WHERE category = ?''', (category,))
    conn.commit()
    conn.close()

@app.route('/')
def home():
    delete_expired_links() 
    active_links = get_active_links()
    return render_template('index.html', active_links=active_links)

@app.route('/add', methods=['POST'])
def add():
    category = request.form['category']
    content = request.form['content']
    expire_at = datetime.datetime.now() + datetime.timedelta(days=2) 
    add_link(category, content, expire_at)
    return redirect(url_for('home'))

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)
  
@app.route('/delete_category', methods=['POST'])
def delete_category_route():
    data = request.get_json()
    category = data.get('category')
    if category:
        delete_category(category)
        return "Category deleted successfully", 200
    else:
        return "Bad request. Category not provided", 400

if __name__ == '__main__':
    create_db() 
    app.run(debug=True)
