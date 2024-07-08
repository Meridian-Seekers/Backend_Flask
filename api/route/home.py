from distutils import debug
from http import HTTPStatus
from logging import info
from xml.dom import ValidationErr
from flask import Blueprint, request, jsonify, current_app, session
from flasgger import swag_from
from werkzeug.security import generate_password_hash, check_password_hash
from api.schema.player import PlayerSchema, LoginSchema

home_api = Blueprint('api', __name__)


@home_api.route('/')
@swag_from({
    'responses': {
        HTTPStatus.OK.value: {
            'description': 'Welcome to the Flask Starter Kit',
            'schema': {}
        }
    }
})
def welcome():
    return jsonify({'message': 'Welcome to the Flask Starter Kit'}), HTTPStatus.OK


@home_api.route('/signup', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': PlayerSchema
        }
    ],
    'responses': {
        HTTPStatus.CREATED.value: {
            'description': 'Player successfully registered',
            'schema': PlayerSchema
        },
        HTTPStatus.BAD_REQUEST.value: {
            'description': 'Invalid input'
        }
    }
})
def signup():
    try:
        data = request.get_json()
        schema = PlayerSchema()

        if 'Active_status' in data:
            del data['Active_status']

        validated_data = schema.load(data)

        # Check if email already exists
        cursor = current_app.mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Player WHERE Email = %s",
                       (validated_data['Email'],))
        existing_player = cursor.fetchone()

        if existing_player:
            return jsonify({'message': 'Email already registered'}), HTTPStatus.BAD_REQUEST

        # Hash the password
        hashed_password = generate_password_hash(validated_data['Password'])

        # Insert new player
        cursor.execute(
            "INSERT INTO Player (Email, F_name, L_name, Password) VALUES (%s, %s, %s, %s)",
            (validated_data['Email'], validated_data['F_name'],
             validated_data['L_name'], hashed_password)
        )
        current_app.mysql.commit()
        cursor.close()

        new_player = {
            'Email': validated_data['Email'],
            'F_name': validated_data['F_name'],
            'L_name': validated_data['L_name'],
            'Password': hashed_password
        }

        return jsonify(new_player), HTTPStatus.CREATED
    except ValidationErr as err:
        return jsonify(err), HTTPStatus.BAD_REQUEST


@home_api.route('/login', methods=['POST'])
@swag_from({
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': LoginSchema
        }
    ],
    'responses': {
        HTTPStatus.OK.value: {
            'description': 'Player successfully logged in',
            'schema': PlayerSchema
        },
        HTTPStatus.UNAUTHORIZED.value: {
            'description': 'Invalid email or password'
        }
    }
})
def login():
    try:
        data = request.get_json()
        schema = LoginSchema()

        if 'Active_status' in data:
            del data['Active_status']

        validated_data = schema.load(data)
        
        print(validated_data)

        # Check if the player exists
        cursor = current_app.mysql.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Player WHERE Email = %s",
                       (validated_data['Email'],))

        player = cursor.fetchone()

        if player and check_password_hash(player['Password'], validated_data['Password']):
            # Set session data upon successful login
            session['email'] = player['Email']  # Store email in session
            session.permanent = True  # Make the session persist beyond browser closure if desired

            # Update Active_status to True (1)
            cursor = current_app.mysql.cursor(dictionary=True)
            cursor.execute(
                "UPDATE Player SET Active_status = TRUE WHERE Email = %s", (validated_data['Email'],))
            current_app.mysql.commit()
            cursor.close()
            
            if player['Active_status'] == 1:
                player['Active_status'] = 'true' 
            else:
                player['Active_status'] = 'false'

            return jsonify({'message': 'Login successful', 'player': player}), HTTPStatus.OK
        else:
            return jsonify({'message': 'Invalid email or password'}), HTTPStatus.UNAUTHORIZED
    except ValidationErr as err:
        return jsonify(err), HTTPStatus.BAD_REQUEST


@home_api.route('/logout', methods=['POST'])
@swag_from({
    'responses': {
        HTTPStatus.OK.value: {
            'description': 'Player successfully logged out'
        },
        HTTPStatus.UNAUTHORIZED.value: {
            'description': 'No active session found'
        }
    }
})
def logout():
    data = request.get_json()
    print(data)
    email = data['Email']

    player = cursor.fetchone()
   # Update Active_status to False (0)
    cursor = current_app.mysql.cursor(dictionary=True)
    cursor.execute(
        "UPDATE Player SET Active_status = FALSE WHERE Email = %s", (email,))
    current_app.mysql.commit()
    cursor.close()

    if player['Active_status'] == 0:
        player['Active_status'] = 'true' 
    else:
        player['Active_status'] = 'false'

    # Clear session data
    session.pop('email', None)

    return jsonify({'message': 'Logout successful'}), HTTPStatus.OK

