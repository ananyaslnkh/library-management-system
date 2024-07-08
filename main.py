from flask import Flask, render_template, request, url_for, redirect, session
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'secret'


def create_server_connection():
    host_name = 'localhost'
    user_name = 'root'
    user_password = '####'
    db_name = 'store'
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        if connection.is_connected():
            print("MySQL Database connection successful")
    except Error as err:
        print(f"Error: '{err}'")
    return connection


def read_query(query, values=None):
    connection = create_server_connection()
    cursor = connection.cursor()
    result = None
    try:
        cursor.execute(query, values) if values else cursor.execute(query)
        result = cursor.fetchall()
    except Error as err:
        print(f"Error: '{err}'")
    finally:
        cursor.close()
        connection.close()
    return result


def execute_query(query, values=None):
    connection = create_server_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(query, values) if values else cursor.execute(query)
        connection.commit()
    except Error as err:
        print(f"Error: '{err}'")
        connection.rollback()
    finally:
        print(cursor.statement)
        cursor.close()
        connection.close()

def get_filtered_books(filter_option=None, filter_value=None):
    query = """
    SELECT
        b.book_id,
        b.title,
        a.author_name,
        p.publisher_name,
        g.genre_name,
        b.price,
        b.total_copies,
        b.available_copies
    FROM
        books b
        JOIN authors a ON b.author_id = a.author_id
        JOIN publishers p ON b.publisher_id = p.publisher_id
        JOIN genres g ON b.genre_id = g.genre_id
    WHERE 1=1
    """

    if filter_option and filter_value:
        if filter_option in {'genre', 'author', 'publisher'}:
            query += f" AND {filter_option[0]}.{filter_option}_name = %s"
            values = (filter_value,)
    query += ";"

    return read_query(query, values)


def purchase_book(user_id, password, book_name):
    user_query = "SELECT * FROM users WHERE user_id = %s AND password = %s;"
    user_result = read_query(user_query, (user_id, password))

    if not user_result:
        print("Invalid user credentials. Purchase failed.")
        return "Invalid user credentials. Purchase failed."

    if user_id == 1:
        print("Admins cannot purchase books.")
        return "Admins cannot purchase books."

    availability_query = "SELECT available_copies FROM books WHERE title = %s;"
    available_copies_result = read_query(availability_query, (book_name,))

    if not available_copies_result or available_copies_result[0][0] <= 0:
        print("This book is currently not available for purchase.")
        return "Book not available for purchase."

    purchase_query = "INSERT INTO purchases (book_id, user_id, purchase_date) VALUES ((SELECT book_id FROM books WHERE title = %s), %s, NOW());"
    execute_query(purchase_query, (book_name, user_id))

    update_query = "UPDATE books SET available_copies = available_copies - 1 WHERE title = %s;"
    execute_query(update_query, (book_name,))

    print(f"Purchase successful for Book: {book_name}.")
    return "Purchase successful!"


def query_books(query):
    try:
        result = read_query(query)
        if result is not None:
            return result
        else:
            print("No books found.")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []


connection = create_server_connection()


@app.route('/add_book_page')
def add_book_page():
    return render_template('add_book.html')


@app.route('/add_book_action', methods=['POST'])
def add_book_action():
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        title = request.form.get('title')
        author_id = request.form.get('author_id')
        author_name = request.form.get('author_name') 
        genre_id = request.form.get('genre_id')
        publisher_id = request.form.get('publisher_id')
        price = request.form.get('price')

        result = add_book_to_database(book_id, title, author_id, author_name, genre_id, publisher_id, price)

        print(result)
        return redirect(url_for('add_book_page'))

def get_last_inserted_id():
    query = "SELECT LAST_INSERT_ID();"
    result = execute_query(query)
    return result.fetchone()[0]

def add_book_to_database(book_id, title, author_id, author_name, genre_id, publisher_id, price):
    try:
        if author_id is None:
            author_id_result = read_query("SELECT author_id FROM authors WHERE author_name = %s;", (author_name,))
            
            if author_id_result:
                author_id = author_id_result[0][0]
            else:
                execute_query("INSERT INTO authors (author_name) VALUES (%s);", (author_name,))
                author_id = get_last_inserted_id()

        query = "CALL InsertBook(%s, %s, %s, %s, %s, %s);"
        values = (book_id, title, author_id, genre_id, publisher_id, price)
        execute_query(query, values)
        return True, "Book added successfully"
    except Exception as e:
        print(f"Error: {e}")
        return f"Failed to add book: {e}"
    
def insert_author(author_name):
    query = "INSERT INTO authors (author_name) VALUES (%s);"
    execute_query(query, (author_name,))
    return get_last_inserted_id()      


@app.route('/update_book_page')
def update_book_page():
    return render_template('update_book.html')

@app.route('/update_book', methods=['POST'])
def update_book_action():
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        title = request.form.get('title')
        author_id = request.form.get('author_id')
        genre_id = request.form.get('genre_id')
        publisher_id = request.form.get('publisher_id')
        price = request.form.get('price')

        result_message = update_book_in_database(book_id, title, author_id, genre_id, publisher_id, price)
        return render_template('update_book.html', result_message=result_message)


def update_book_in_database(book_id, title, author_id, genre_id, publisher_id, price):
    try:
        query = "CALL UpdateBook(%s, %s, %s, %s, %s, %s);"
        values = (book_id, title, author_id, genre_id, publisher_id, price)
        execute_query(query, values)
        return "Book updated successfully"  
    except Exception as e:
        print(f"Error: {e}")
        return f"Failed to update book: {e}"
    

@app.route('/delete_book_page')
def delete_book_page():
    return render_template('delete_book.html')

@app.route('/delete_book', methods=['POST'])
def delete_book_action():
    if request.method == 'POST':
        book_id = request.form.get('book_id')
        result_message = delete_book_from_database(book_id)
        return render_template('delete_book.html', result_message=result_message)

def delete_book_from_database(book_id):
    try:

        check_book_query = "SELECT * FROM inventory WHERE book_id = %s;"
        check_book_result = read_query(check_book_query, (book_id,))
        
        if not check_book_result:
            return "Book does not exist."

        admin_delete_query = "CALL DeleteBook(%s);"
        execute_query(admin_delete_query, (book_id,))

        check_user_book_query = "SELECT * FROM books WHERE book_id = %s;"
        check_user_book_result = read_query(check_user_book_query, (book_id,))

        if check_user_book_result:
            user_delete_query = "DELETE FROM books WHERE book_id = %s AND available_copies = 0 AND total_copies = 0;"
            execute_query(user_delete_query, (book_id,))

        return "Book deleted successfully"  
    except Exception as e:
        print(f"Error: {e}")
        return f"Failed to delete book: {e}"



@app.route('/view_purchase')
def view_purchase():
    if 'admin' in session:
        query_select_all_purchases = "SELECT * FROM purchases;"
        purchases = query_books(query_select_all_purchases)
        return render_template('view_purchase.html', purchases=purchases)
    else:
        return redirect(url_for('login'))
    

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        error_message = None

        if username == 'admin' and password == 'adminpassword':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))

        user_query = "SELECT * FROM users WHERE username = %s AND password = %s;"
        user_result = read_query(user_query, (username, password,))

        if user_result:
            session['user_id'] = user_result[0][0]
            return redirect(url_for('user_dashboard'))
        else:
            error_message = "Invalid credentials. Please try again."

    else:
        error_message = None

    return render_template('login.html', error_message=error_message)


@app.route('/')
def index():
    query_select_all_books = """
    SELECT
        b.book_id,
        b.title,
        a.author_name,
        p.publisher_name,
        b.price,
        g.genre_name
    FROM
        books b
        JOIN authors a ON b.author_id = a.author_id
        JOIN publishers p ON b.publisher_id = p.publisher_id
        JOIN genres g ON b.genre_id = g.genre_id
    ORDER BY b.book_id;
    """
    books = query_books(query_select_all_books)
    return render_template('dash.html', books=books)


@app.route('/filter', methods=['POST'])
def filter_books():
    filter_option = request.form.get('filter_option')
    filter_value = request.form.get('filter_value')
    filtered_books = get_filtered_books(filter_option, filter_value)
    return render_template('filtered_books.html', filtered_books=filtered_books,
                           filter_heading=f"Books Filtered by {filter_option.capitalize()}")


@app.route('/purchase', methods=['POST'])
def purchase():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        book_name = request.form.get('book_name')

        if user_id == '1':
            return "Admins cannot purchase books."

        success = purchase_book(user_id, password, book_name)

        if success:
            return "Purchase successful!"
        else:
            return "Book not available for purchase or invalid user credentials."

    return redirect(url_for('index'))


@app.route('/purchase')
def purchase_page():
    return render_template('purchase.html')    


@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' in session:
        query_select_all_books = """
        SELECT
            b.book_id,
            b.title,
            a.author_name,
            p.publisher_name,
            b.price,
            g.genre_name
        FROM
            books b
            JOIN authors a ON b.author_id = a.author_id
            JOIN publishers p ON b.publisher_id = p.publisher_id
            JOIN genres g ON b.genre_id = g.genre_id
        ORDER BY b.book_id;
        """
        books = query_books(query_select_all_books)
        return render_template('dash.html', books=books)
    else:
        return redirect(url_for('login'))


@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' in session:
        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'add':
                book_id = request.form.get('book_id')
                title = request.form.get('title')
                author_id = request.form.get('author_id')
                genre_id = request.form.get('genre_id')
                publisher_id = request.form.get('publisher_id')
                price = request.form.get('price')

                result = add_book_to_database(book_id, title, author_id, genre_id, publisher_id, price)
                if result == "Success":
                    print("Book added successfully", "success")
                else:
                    print(result, "danger")
                return redirect(url_for('add_book_page'))  
            
            elif action == 'update':
                book_id = request.form.get('book_id')
                title = request.form.get('title')
                author_id = request.form.get('author_id')
                genre_id = request.form.get('genre_id')
                publisher_id = request.form.get('publisher_id')
                price = request.form.get('price')

                result = update_book_in_database(book_id, title, author_id, genre_id, publisher_id, price)
                if result == "Success":
                    print("Book updated successfully", "success")
                else:
                    print(result, "danger")

                return redirect(url_for('update_book_page'))

            elif action == 'delete':
                book_id = request.form.get('book_id')
                result = delete_book_from_database(book_id)
                if result == "Success":
                    print("Book deleted successfully", "success")
                else:
                    print(result, "danger")

                return redirect(url_for('delete_book_page'))
            
        inventory_query = "SELECT * FROM inventory;"
        inventory_data = query_books(inventory_query)
        

        return render_template('admin.html', inventory_data=inventory_data)
    else:
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
