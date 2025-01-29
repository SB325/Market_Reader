import bcrypt
import os
import sys
from util.logger import log
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete, update
from flask import jsonify
from util.db.models.user_accounts import User_Creds, User_Metrics
from util.db.conn import insert_engine
import pdb

Session = sessionmaker(bind=insert_engine())
user_session = Session()
engine = insert_engine()

def check_password(presented_str: str, encoded_str: str) -> bool:
    """Create function to check passed API key against hashed database value
    in order to authenticate users"""
    try:
        presented_bytes = presented_str.encode("utf-8")
        known_bytes = encoded_str.encode("utf-8")
        result = bcrypt.checkpw(presented_bytes, known_bytes)
    except Exception as exc:
        log.exception(f'Failure in password check.\n{exc}')
    
    return result

def encode_password(password: str):
    try:
        bytes_encode = password.encode(
            "utf-8"
        )  # must be converted to bytes for the salting
        salt = bcrypt.gensalt()
        new_hash = bcrypt.hashpw(
            bytes_encode, salt
        )  # the hash is what is stored in the database
        encoded_password = new_hash.decode("utf-8", "strict")
    except Exception as exc:
        log.exception(f'Failure in the password encoding process.\n{exc}')

    return encoded_password, password

def validate_user(response) -> dict:
    authenticate = False
    user_name = ''

    try:
        user_query = user_session.query(User_Creds).filter_by(
            user_name=response['user_name']).first()
        hashed_database_key = user_query.hashed_key
        password_key = response["password"]

        if check_password(password_key, hashed_database_key) == True:
            authenticate = True
            user_name = response['user_name']
        else:
            authenticate = False
    except Exception as exc:
        log.exception(f'Failure to execute authentication of request.\n{exc}')

    return {'authenticate': authenticate, 'user_name': user_name}

def create_new_user(user_name: str, password: str) -> bool:
    input_user = {}
    input_user["user_name"] = user_name
    input_user["hashed_key"], pw = encode_password(password)
    status = False
    try:
        with engine.connect() as conn:
            conn.execute(insert(User_Creds).on_conflict_do_nothing(
                        index_elements=['user_name']
                        ), [ input_user ])
            conn.commit()
        status = True
    except Exception as exc:
        log.error(f'Failure to create new user.\n{exc}')
    
    return status

def delete_user(user_name: str, password: str) -> bool:
    try:
        credentials = {'user_name':user_name, 'password':password}
        if validate_user(credentials)['authenticate']:

            query = user_session.query(User_Creds).filter(
                        User_Creds.user_name == user_name
                        )
            if not query.first():
                log.warning(f'User {user_name} does not exist in database.')
                return False
            else:
                with engine.connect() as conn:
                    conn.execute(
                        delete(User_Creds).where(
                        User_Creds.user_name == user_name
                        )
                    )
                    conn.commit()
                    
            log.info(f'Successfully deleted {user_name}')
        else:
            log.warning(f'Failed to authenticate user in order to update password.')
            return False

    except Exception as exc:
        log.error(f'Failure to delete user.\n{exc}')
    
    return True

def update_password(user_name: str, password: str, new_password: str) -> bool:
    try:
        # First validate password
        if validate_user({'user_name':user_name, 'password':password})['authenticate']:
            encoded_new_pw, pw = encode_password(new_password)
            encoded_old_pw, pw = encode_password(password)
            with engine.connect() as conn:
                conn.execute(
                    update(User_Creds).where(
                    User_Creds.user_name == user_name).values(
                        hashed_key=encoded_new_pw
                    )
                )
                conn.commit()
        else:
            log.warning(f'Failed to authenticate user in order to update password.')
            return False
    except Exception as exc:
        log.error(f'Failure to delete user.\n{exc}')
    
    return True

def show_users():
    users_returned = user_session.query(User_Creds.user_name).all()
    return [n[0] for n in users_returned]

def user_exists(username: str):
    user_returned = user_session.query(User_Creds.user_name).where(
                User_Creds.user_name==username
                )
    pdb.set_trace()
    return user_returned
