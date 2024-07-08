# library-management-system
DBMS mini project

The Library Management System is designed to manage book inventory, user authentication, and book borrowing and returning. Built with Flask, a Python web framework, and MySQL for the database

Functionality:

1. User Authentication:
   Users and administrators can log in with their credentials. (set default username and password in the database)
   Used sessions to ensure that the user and admin have access to different parts of the application

2. Admin functionality:
   Add book 
   Update book details - title, author, genre, publisher, and price can be updated
   Delete book
   View inventory - including details like title, author, genre, publisher, price, total copies, and available copies
   View purchases

3. User functionality:
   View available books - including details like title, author, genre, publisher, price
   Filter books - users can filter books by genre, author, and publisher
   Borrow Books - users can borrow available books. The system checks user credentials and book availability before processing the request
   Return Books - Users can return borrowed books, and the system updates the available copies accordingly
