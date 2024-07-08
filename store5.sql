CREATE database store;
USE store;
CREATE TABLE publishers (
    publisher_id INT PRIMARY KEY,
    publisher_name VARCHAR(50) NOT NULL
);

CREATE TABLE genres (
    genre_id INT PRIMARY KEY,
    genre_name VARCHAR(30) NOT NULL
);

CREATE TABLE authors (
    author_id INT PRIMARY KEY,
    author_name VARCHAR(30) NOT NULL
);


CREATE TABLE users (
    user_id INT PRIMARY KEY,
    username VARCHAR(20) NOT NULL,
    password VARCHAR(20) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('Admin', 'Normal'))
);

CREATE TABLE books (
    book_id INT PRIMARY KEY,
    title VARCHAR(50) NOT NULL,
    author_id INT,
    genre_id INT,
    publisher_id INT,
    price INT,
    total_copies INT DEFAULT 0,
    available_copies INT DEFAULT 0,
    FOREIGN KEY (author_id) REFERENCES authors(author_id),
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id),
    FOREIGN KEY (publisher_id) REFERENCES publishers(publisher_id)
);

CREATE TABLE purchases (
    purchase_id INT PRIMARY KEY AUTO_INCREMENT,
    book_id INT,
    user_id INT,
    purchase_date DATE,
    FOREIGN KEY (book_id) REFERENCES books(book_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
ALTER TABLE purchases AUTO_INCREMENT=1;

INSERT INTO publishers (publisher_id, publisher_name) VALUES
    (1, 'Penguin Random House'),
    (2, 'Bloomsbury'),
    (3, 'Reed Elsevier'),
    (4, 'Phoenix Publishing');

INSERT INTO genres (genre_id, genre_name) VALUES
    (1, 'Fiction'),
    (2, 'Adventure'),
    (3, 'Autobiography'),
    (4, 'Humour'),
    (5, 'Dystopian'),
    (6, 'Romance'),
    (7, 'Thriller');

INSERT INTO authors (author_id, author_name) VALUES
    (1, 'F. Scott Fitzgerald'),
    (2, 'Rachael Lippincott'),
    (3, 'Alexandra Dumas'),
    (4, 'Jonathan Swift'),
    (5, 'Malala Yousafzai'),
    (6, 'A.P.J Abdul Kalam'),
    (7, 'Jenny Lawson'),
    (8, 'Alex Michaelides');
    
INSERT INTO authors (author_id, author_name) VALUE (9, 'André Aciman');

INSERT INTO books (book_id, title, author_id, genre_id, publisher_id, price, total_copies, available_copies) VALUES
    (1, 'The Great Gatsby', 1, 1, 1, 499, 10, 7),
    (2, 'Five Feet Apart', 2, 6, 2, 599, 12, 10),
    (3, 'The Three Musketeers', 3, 2, 4, 599, 12, 10),
    (4, 'Gullivers Travels', 4, 2, 3, 399, 10, 9),
    (5, 'I Am Malala', 5, 3, 1, 499, 9, 9),
    (6, 'Wings of Fire', 6, 3, 3, 599, 11, 10),
    (7, 'Lets Pretend This Never Happened', 7, 4, 2, 399, 18, 10),
    (8, 'The Maidens', 8, 7, 1, 499, 10, 8),
    (9, 'The silent Patient', 8, 7, 4, 399, 10, 7);

INSERT INTO users (user_id, username, password, role) VALUES
    (1, 'admin', 'adminpassword', 'Admin'),
    (2, 'user', 'userpassword', 'Normal');

INSERT INTO purchases (book_id, user_id, purchase_date) VALUES
    (1, 2, '2023-01-01'),
    (2, 2, '2023-02-15');

CREATE USER 'admin'@'localhost' IDENTIFIED BY 'admin';
CREATE USER 'user'@'localhost' IDENTIFIED BY 'user';
GRANT SELECT, INSERT, UPDATE, DELETE ON bookstore.* TO 'admin'@'localhost';
GRANT SELECT ON store.inventory TO 'admin'@'localhost';
GRANT SELECT ON store.* TO 'user'@'localhost';
SHOW GRANTS FOR 'root'@'localhost';


DELIMITER //

CREATE PROCEDURE InsertBook(
    IN p_book_id INT,
    IN p_title VARCHAR(50),
    IN p_author_id INT,
    IN p_genre_id INT,
    IN p_publisher_id INT,
    IN p_price INT
)
BEGIN
    
    IF NOT EXISTS (SELECT 1 FROM authors WHERE author_id = p_author_id) THEN
      
        INSERT INTO authors (author_id, author_name) VALUES (p_author_id, (SELECT author_name FROM authors WHERE author_id = p_author_id));
    END IF;

    INSERT INTO books (book_id, title, author_id, genre_id, publisher_id, price, total_copies, available_copies)
    VALUES (p_book_id, p_title, p_author_id, p_genre_id, p_publisher_id, p_price, 1, 1)
    ON DUPLICATE KEY UPDATE total_copies = total_copies + 1, available_copies = available_copies + 1;
END //

DELIMITER ;

DELIMITER //

CREATE PROCEDURE UpdateBook(
    IN p_book_id INT,
    IN p_title VARCHAR(50),
    IN p_author_id INT,
    IN p_genre_id INT,
    IN p_publisher_id INT,
    IN p_price INT
)
BEGIN
    UPDATE books
    SET title = p_title,
        author_id = p_author_id,
        genre_id = p_genre_id,
        publisher_id = p_publisher_id,
        price = p_price
    WHERE book_id = p_book_id;
END //

DELIMITER ;


DELIMITER //

CREATE PROCEDURE DeleteBook(IN p_book_id INT)
BEGIN
    DECLARE current_total_copies INT;
    DECLARE current_available_copies INT;

    SELECT total_copies, available_copies
    INTO current_total_copies, current_available_copies
    FROM books
    WHERE book_id = p_book_id;

    IF current_total_copies > 0 THEN
        UPDATE books
        SET total_copies = current_total_copies - 1,
            available_copies = current_available_copies - 1
        WHERE book_id = p_book_id;
    END IF;
END //

DELIMITER ;


CALL InsertBook('3', 'The Maze Runner', 1, 1, 1, 499);
CALL UpdateBook(1, 'Mockingjay', 2, 2, 2, 599);
CALL UpdateBook(1, 'The Great Gatsby', 1, 1, 1, 499);
CALL DeleteBook(2);
select * from books;
GRANT TRIGGER ON bookstore.* TO 'admin'@'localhost';

DELIMITER //

CREATE PROCEDURE SearchBooks(IN p_search_term VARCHAR(50))
BEGIN
    SELECT
        b.book_id,
        b.title,
        a.author_name,
        g.genre_name,
        p.publisher_name,
        b.price,
        b.total_copies,
        b.available_copies
    FROM
        books b
        JOIN authors a ON b.author_id = a.author_id
        JOIN genres g ON b.genre_id = g.genre_id
        JOIN publishers p ON b.publisher_id = p.publisher_id
    WHERE
        b.title LIKE CONCAT('%', p_search_term, '%');
END //

DELIMITER ;

DELIMITER //

CREATE TRIGGER SetPurchaseDate
BEFORE INSERT ON purchases
FOR EACH ROW
BEGIN
    SET NEW.purchase_date = NOW();
END //

DELIMITER ;

DELIMITER //

CREATE TRIGGER after_book_insert
AFTER INSERT ON books
FOR EACH ROW
BEGIN
    UPDATE books
    SET total_books = total_books + 1;
END //

DELIMITER ;


CREATE VIEW inventory AS
SELECT
    b.book_id,
    b.title,
    b.total_copies,
    b.available_copies
FROM books b
WHERE b.total_copies > 0;
GRANT SELECT ON store.inventory TO 'admin'@'localhost';
SELECT * FROM inventory;

-- query check
SELECT
    b.book_id,
    b.title,
    a.author_name,
    p.publisher_name,
    b.price
FROM
    books b
    JOIN authors a ON b.author_id = a.author_id
    JOIN publishers p ON b.publisher_id = p.publisher_id
    ORDER BY b.book_id;

UPDATE books
SET title = 'The Silent Patient'
WHERE book_id = 9;

UPDATE books
SET total_copies = 11, available_copies = 9
WHERE book_id=4;

select * from books;
delete from books where book_id=23;

select * from purchases;