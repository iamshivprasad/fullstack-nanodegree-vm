# Catalog App

An application that provides a list of items within a variety of categories as well as provide an authentication system. Authenticated users can post, edit and delete their own items.

## Getting Started

The following softwares and dependencies are required to be present in the target machine to run this tool.
- Python 3.7
- httplib2
- requests
- flask
- flask_httpauth
- oauth2client
- sqlalchemy
- passlib


## How to Run

Setup the database by executing the below statement.

```
python databasemodels.py
```

Once the database has been setup, execute the below statement to run the application.

```
python views.py
```

## Additional Information
Users can log in using their Google credentials. Once the user has logged in, he is able to Add, Edit and Delete items.
All users are able to view all the items avaialble in the Catalog. But only the creator of the item can modify or delete an item.

## Author

-   Shiv - iamshiv.trainings@gmail.com
