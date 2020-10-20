#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from CTFd.models import Challenges, Solves, Awards, Users, db
from CTFd.plugins.CTFd_first_blood import FirstBloodChallenge, FirstBloodAward, FirstBloodValueChallenge
from tests.helpers import (
    FakeRequest,
    create_ctfd,
    destroy_ctfd,
    gen_flag,
    gen_user,
    login_as_user,
    register_user,
)


def _check_first_blood_awards_data(challenge, expected_data):
    """
    Checks if the Solves and FirstBloodAward tables contain the data that matches the expected values
    Input is in this format:
    expected_data = [
        {"user": "user1", "solved": True, "bonus_points": 30, "bonus_num": 1, "bonus_name": "1st"},
        {"user": "user2", "solved": True, "bonus_points": 20, "bonus_num": 2, "bonus_name": "2nd"},
        {"user": "user3", "solved": True, "bonus_points": 10, "bonus_num": 3, "bonus_name": "3rd"},
        {"user": "user4", "solved": True, "bonus_points": None},
        {"user": "user5", "solved": False},
    ]
    """
    for expected in expected_data:
        solves = Solves.query.join(Users, Solves.user_id == Users.id).filter(Users.name == expected['user'], Solves.challenge_id == challenge.id).all()
        if not expected['solved']:
            assert len(solves) == 0
        else:
            assert len(solves) == 1
            solve = solves[0]
            awards = FirstBloodAward.query.filter(FirstBloodAward.solve_id == solve.id).all()
            if expected['bonus_points'] is None:
                assert len(awards) == 0
            else:
                assert len(awards) == 1
                award = awards[0]
                assert award.name == "{0} blood for {1}".format(expected['bonus_name'], challenge.name)
                assert award.value == expected['bonus_points']
                assert award.solve_num == expected['bonus_num']

def test_can_create_firstblood_challenge():
    """Test that firstblood challenges can be made from the API/admin panel"""
    app = create_ctfd(enable_plugins=True)
    with app.app_context():
        client = login_as_user(app, name="admin", password="password")

        challenge_data = {
            "name": "name",
            "category": "category",
            "description": "description",
            "value": 100,
            "first_blood_bonus[0]": 30,
            "first_blood_bonus[1]": 20,
            "first_blood_bonus[2]": 10,
            "state": "hidden",
            "type": "firstblood",
        }

        r = client.post("/api/v1/challenges", json=challenge_data)
        assert r.get_json().get("data")["id"] == 1

        challenges = FirstBloodChallenge.query.all()
        assert len(challenges) == 1

        challenge = challenges[0]
        assert challenge.value == 100
        assert challenge.first_blood_bonus[0] == 30
        assert challenge.first_blood_bonus[1] == 20
        assert challenge.first_blood_bonus[2] == 10
    destroy_ctfd(app)


def test_can_update_firstblood_challenge():
    app = create_ctfd(enable_plugins=True)
    with app.app_context():
        challenge_data = {
            "name": "name",
            "category": "category",
            "description": "description",
            "value": 100,
            "first_blood_bonus[0]": 30,
            "first_blood_bonus[1]": 20,
            "first_blood_bonus[2]": 10,
            "state": "hidden",
            "type": "firstblood",
        }
        req = FakeRequest(form=challenge_data)
        challenge = FirstBloodValueChallenge.create(req)

        assert challenge.value == 100
        assert challenge.first_blood_bonus[0] == 30
        assert challenge.first_blood_bonus[1] == 20
        assert challenge.first_blood_bonus[2] == 10

        challenge_data = {
            "name": "new_name",
            "category": "category",
            "description": "new_description",
            "value": "200",
            "first_blood_bonus[0]": 300,
            "first_blood_bonus[1]": 200,
            "first_blood_bonus[2]": 100,
            "max_attempts": "0",
            "state": "visible",
        }

        req = FakeRequest(form=challenge_data)
        challenge = FirstBloodValueChallenge.update(challenge, req)

        assert challenge.name == "new_name"
        assert challenge.description == "new_description"
        assert challenge.value == 200
        assert challenge.first_blood_bonus[0] == 300
        assert challenge.first_blood_bonus[1] == 200
        assert challenge.first_blood_bonus[2] == 100
        assert challenge.state == "visible"

    destroy_ctfd(app)

def test_can_delete_firstblood_challenge():
    """Test that firstblood challenges can be deleted"""
    app = create_ctfd(enable_plugins=True)
    with app.app_context():
        client = login_as_user(app, name="admin", password="password")

        challenge_data = {
            "name": "name",
            "category": "category",
            "description": "description",
            "value": 100,
            "first_blood_bonus[0]": 300,
            "first_blood_bonus[1]": 200,
            "first_blood_bonus[2]": 100,
            "state": "hidden",
            "type": "firstblood",
        }

        r = client.post("/api/v1/challenges", json=challenge_data)
        assert r.get_json().get("data")["id"] == 1

        challenges = FirstBloodChallenge.query.all()
        assert len(challenges) == 1

        challenge = challenges[0]
        FirstBloodValueChallenge.delete(challenge)

        challenges = FirstBloodChallenge.query.all()
        assert len(challenges) == 0
    destroy_ctfd(app)

def test_solve_generates_awards():
    app = create_ctfd(enable_plugins=True)
    with app.app_context():
        register_user(app, name="user1", email="user1@ctfd.io")
        register_user(app, name="user2", email="user2@ctfd.io")
        register_user(app, name="user3", email="user3@ctfd.io")
        register_user(app, name="user4", email="user4@ctfd.io")
    
        challenge_data = {
            "name": "name",
            "category": "category",
            "description": "description",
            "value": 100,
            "first_blood_bonus[0]": 30,
            "first_blood_bonus[1]": 20,
            "first_blood_bonus[2]": 10,
            "state": "visible",
            "type": "firstblood",
        }
        req = FakeRequest(form=challenge_data)
        challenge = FirstBloodValueChallenge.create(req)
        gen_flag(app.db, challenge_id=challenge.id, content="flag")

        assert challenge.value == 100
        assert challenge.first_blood_bonus[0] == 30
        assert challenge.first_blood_bonus[1] == 20
        assert challenge.first_blood_bonus[2] == 10

        for user in ["user1", "user2", "user3", "user4"]:
            client = login_as_user(app, name=user, password="password")
            with client.session_transaction():
                data = {"submission": "flag", "challenge_id": challenge.id}
                r = client.post("/api/v1/challenges/attempt", json=data)
                assert r.status_code == 200
        
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": 30, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user2", "solved": True, "bonus_points": 20, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user3", "solved": True, "bonus_points": 10, "bonus_num": 3, "bonus_name": "3rd"},
            {"user": "user4", "solved": True, "bonus_points": None},
        ]
        _check_first_blood_awards_data(challenge, expected_data)

    destroy_ctfd(app)

def test_solve_generates_no_awards_for_hidden_users():
    app = create_ctfd(enable_plugins=True)
    with app.app_context():
        register_user(app, name="user1", email="user1@ctfd.io")
        register_user(app, name="user2", email="user2@ctfd.io")
        register_user(app, name="user3", email="user3@ctfd.io")
        register_user(app, name="user4", email="user4@ctfd.io")
    
        challenge_data = {
            "name": "name",
            "category": "category",
            "description": "description",
            "value": 100,
            "first_blood_bonus[0]": 30,
            "first_blood_bonus[1]": 20,
            "first_blood_bonus[2]": 10,
            "state": "visible",
            "type": "firstblood",
        }
        req = FakeRequest(form=challenge_data)
        challenge = FirstBloodValueChallenge.create(req)
        gen_flag(app.db, challenge_id=challenge.id, content="flag")
        
        assert challenge.value == 100
        assert challenge.first_blood_bonus[0] == 30
        assert challenge.first_blood_bonus[1] == 20
        assert challenge.first_blood_bonus[2] == 10
        
        # User2 is hidden
        users = Users.query.filter(Users.name == "user2").all()
        assert len(users) == 1
        user = users[0]

        client = login_as_user(app, name="admin", password="password")
        r = client.patch("/api/v1/users/{0}".format(user.id), json={'hidden': True})
        assert r.status_code == 200

        for day, user in enumerate(["user1", "user2", "user3", "user4"], start=10):
            with freeze_time("2020-10-%02d 12:34:56" % day):
                client = login_as_user(app, name=user, password="password")
                with client.session_transaction():
                    data = {"submission": "flag", "challenge_id": challenge.id}
                    r = client.post("/api/v1/challenges/attempt", json=data)
                    assert r.status_code == 200
        
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": 30, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user2", "solved": True, "bonus_points": None},  # solved - just hidden
            {"user": "user3", "solved": True, "bonus_points": 20, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user4", "solved": True, "bonus_points": 10, "bonus_num": 3, "bonus_name": "3rd"},
        ]
        _check_first_blood_awards_data(challenge, expected_data)

    destroy_ctfd(app)

def test_awards_removed_on_challenge_removed():
    app = create_ctfd(enable_plugins=True)
    with app.app_context():
        register_user(app, name="user1", email="user1@ctfd.io")
        register_user(app, name="user2", email="user2@ctfd.io")
        register_user(app, name="user3", email="user3@ctfd.io")
        register_user(app, name="user4", email="user4@ctfd.io")
    
        challenge_data = {
            "name": "name",
            "category": "category",
            "description": "description",
            "value": 100,
            "first_blood_bonus[0]": 30,
            "first_blood_bonus[1]": 20,
            "first_blood_bonus[2]": 10,
            "state": "visible",
            "type": "firstblood",
        }
        req = FakeRequest(form=challenge_data)
        challenge = FirstBloodValueChallenge.create(req)
        gen_flag(app.db, challenge_id=challenge.id, content="flag")

        assert challenge.value == 100
        assert challenge.first_blood_bonus[0] == 30
        assert challenge.first_blood_bonus[1] == 20
        assert challenge.first_blood_bonus[2] == 10
        
        for user in ["user1", "user2", "user3", "user4"]:
            client = login_as_user(app, name=user, password="password")
            with client.session_transaction():
                data = {"submission": "flag", "challenge_id": challenge.id}
                r = client.post("/api/v1/challenges/attempt", json=data)
                assert r.status_code == 200
        
        assert Solves.query.count() == 4
        assert Awards.query.count() == 3
        
        FirstBloodValueChallenge.delete(challenge)
        
        assert Solves.query.count() == 0
        assert FirstBloodAward.query.count() == 0
        assert Awards.query.count() == 0

    destroy_ctfd(app)

def test_awards_recalculated_on_solve_removed():
    app = create_ctfd(enable_plugins=True)
    with app.app_context():
        register_user(app, name="user1", email="user1@ctfd.io")
        register_user(app, name="user2", email="user2@ctfd.io")
        register_user(app, name="user3", email="user3@ctfd.io")
        register_user(app, name="user4", email="user4@ctfd.io")
        register_user(app, name="user5", email="user5@ctfd.io")
    
        challenge_data = {
            "name": "name",
            "category": "category",
            "description": "description",
            "value": 100,
            "first_blood_bonus[0]": 30,
            "first_blood_bonus[1]": 20,
            "first_blood_bonus[2]": 10,
            "state": "visible",
            "type": "firstblood",
        }
        req = FakeRequest(form=challenge_data)
        challenge = FirstBloodValueChallenge.create(req)
        gen_flag(app.db, challenge_id=challenge.id, content="flag")

        assert challenge.value == 100
        assert challenge.first_blood_bonus[0] == 30
        assert challenge.first_blood_bonus[1] == 20
        assert challenge.first_blood_bonus[2] == 10
        
        for user in ["user1", "user2", "user3", "user4", "user5"]:
            client = login_as_user(app, name=user, password="password")
            with client.session_transaction():
                data = {"submission": "flag", "challenge_id": challenge.id}
                r = client.post("/api/v1/challenges/attempt", json=data)
                assert r.status_code == 200
        
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": 30, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user2", "solved": True, "bonus_points": 20, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user3", "solved": True, "bonus_points": 10, "bonus_num": 3, "bonus_name": "3rd"},
            {"user": "user4", "solved": True, "bonus_points": None},
            {"user": "user5", "solved": True, "bonus_points": None},
        ]
        _check_first_blood_awards_data(challenge, expected_data)
                
        # Admin deletes the solve
        solves = Solves.query.join(Users, Solves.user_id == Users.id).filter(Users.name == "user2", Solves.challenge_id == challenge.id).all()
        assert len(solves) == 1
        solve = solves[0]

        client = login_as_user(app, name="admin", password="password")
        r = client.delete("/api/v1/submissions/{0}".format(solve.id), json="")
        assert r.status_code == 200

        # First blood should have recalculated
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": 30, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user2", "solved": False},
            {"user": "user3", "solved": True, "bonus_points": 20, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user4", "solved": True, "bonus_points": 10, "bonus_num": 3, "bonus_name": "3rd"},
            {"user": "user5", "solved": True, "bonus_points": None},
        ]
        _check_first_blood_awards_data(challenge, expected_data)
        
        # There should be no leftovers in the DB
        assert Solves.query.count() == 4
        assert FirstBloodAward.query.count() == 3
        assert Awards.query.count() == 3

    destroy_ctfd(app)

def test_awards_recalculated_on_user_hidden():
    app = create_ctfd(enable_plugins=True)
    with app.app_context():
        register_user(app, name="user1", email="user1@ctfd.io")
        register_user(app, name="user2", email="user2@ctfd.io")
        register_user(app, name="user3", email="user3@ctfd.io")
        register_user(app, name="user4", email="user4@ctfd.io")
        register_user(app, name="user5", email="user5@ctfd.io")
    
        challenge_data = {
            "name": "name",
            "category": "category",
            "description": "description",
            "value": 100,
            "first_blood_bonus[0]": 30,
            "first_blood_bonus[1]": 20,
            "first_blood_bonus[2]": 10,
            "state": "visible",
            "type": "firstblood",
        }
        req = FakeRequest(form=challenge_data)
        challenge = FirstBloodValueChallenge.create(req)
        gen_flag(app.db, challenge_id=challenge.id, content="flag")

        assert challenge.value == 100
        assert challenge.first_blood_bonus[0] == 30
        assert challenge.first_blood_bonus[1] == 20
        assert challenge.first_blood_bonus[2] == 10
        
        for user in ["user1", "user2", "user3", "user4", "user5"]:
            client = login_as_user(app, name=user, password="password")
            with client.session_transaction():
                data = {"submission": "flag", "challenge_id": challenge.id}
                r = client.post("/api/v1/challenges/attempt", json=data)
                assert r.status_code == 200
        
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": 30, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user2", "solved": True, "bonus_points": 20, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user3", "solved": True, "bonus_points": 10, "bonus_num": 3, "bonus_name": "3rd"},
            {"user": "user4", "solved": True, "bonus_points": None},
            {"user": "user5", "solved": True, "bonus_points": None},
        ]
        _check_first_blood_awards_data(challenge, expected_data)
                
        # Admin hides user2
        users = Users.query.filter(Users.name == "user2").all()
        assert len(users) == 1
        user = users[0]

        client = login_as_user(app, name="admin", password="password")
        r = client.patch("/api/v1/users/{0}".format(user.id), json={'hidden': True})
        assert r.status_code == 200

        # First blood should have recalculated
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": 30, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user2", "solved": True, "bonus_points": None}, # solved, just invisible on the scoreboard
            {"user": "user3", "solved": True, "bonus_points": 20, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user4", "solved": True, "bonus_points": 10, "bonus_num": 3, "bonus_name": "3rd"},
            {"user": "user5", "solved": True, "bonus_points": None},
        ]
        _check_first_blood_awards_data(challenge, expected_data)
        
        # There should be no leftovers in the DB
        assert Solves.query.count() == 5
        assert FirstBloodAward.query.count() == 3
        assert Awards.query.count() == 3
                
        # Admin unhides user2
        users = Users.query.filter(Users.name == "user2").all()
        assert len(users) == 1
        user = users[0]

        client = login_as_user(app, name="admin", password="password")
        r = client.patch("/api/v1/users/{0}".format(user.id), json={'hidden': False})
        assert r.status_code == 200

        # First blood should have recalculated again
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": 30, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user2", "solved": True, "bonus_points": 20, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user3", "solved": True, "bonus_points": 10, "bonus_num": 3, "bonus_name": "3rd"},
            {"user": "user4", "solved": True, "bonus_points": None},
            {"user": "user5", "solved": True, "bonus_points": None},
        ]
        _check_first_blood_awards_data(challenge, expected_data)
        
        # There should be no leftovers in the DB
        assert Solves.query.count() == 5
        assert FirstBloodAward.query.count() == 3
        assert Awards.query.count() == 3

    destroy_ctfd(app)

def test_awards_recalculated_on_user_removed():
    app = create_ctfd(enable_plugins=True)
    with app.app_context():
        register_user(app, name="user1", email="user1@ctfd.io")
        register_user(app, name="user2", email="user2@ctfd.io")
        register_user(app, name="user3", email="user3@ctfd.io")
        register_user(app, name="user4", email="user4@ctfd.io")
        register_user(app, name="user5", email="user5@ctfd.io")
    
        challenge_data = {
            "name": "name",
            "category": "category",
            "description": "description",
            "value": 100,
            "first_blood_bonus[0]": 30,
            "first_blood_bonus[1]": 20,
            "first_blood_bonus[2]": 10,
            "state": "visible",
            "type": "firstblood",
        }
        req = FakeRequest(form=challenge_data)
        challenge = FirstBloodValueChallenge.create(req)
        gen_flag(app.db, challenge_id=challenge.id, content="flag")

        assert challenge.value == 100
        assert challenge.first_blood_bonus[0] == 30
        assert challenge.first_blood_bonus[1] == 20
        assert challenge.first_blood_bonus[2] == 10
        
        for user in ["user1", "user2", "user3", "user4", "user5"]:
            client = login_as_user(app, name=user, password="password")
            with client.session_transaction():
                data = {"submission": "flag", "challenge_id": challenge.id}
                r = client.post("/api/v1/challenges/attempt", json=data)
                assert r.status_code == 200
        
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": 30, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user2", "solved": True, "bonus_points": 20, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user3", "solved": True, "bonus_points": 10, "bonus_num": 3, "bonus_name": "3rd"},
            {"user": "user4", "solved": True, "bonus_points": None},
            {"user": "user5", "solved": True, "bonus_points": None},
        ]
        _check_first_blood_awards_data(challenge, expected_data)
                
        # Admin deletes user2
        users = Users.query.filter(Users.name == "user2").all()
        assert len(users) == 1
        user = users[0]

        client = login_as_user(app, name="admin", password="password")
        r = client.delete("/api/v1/users/{0}".format(user.id), json='')
        assert r.status_code == 200

        # First blood should have recalculated
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": 30, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user3", "solved": True, "bonus_points": 20, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user4", "solved": True, "bonus_points": 10, "bonus_num": 3, "bonus_name": "3rd"},
            {"user": "user5", "solved": True, "bonus_points": None},
        ]
        _check_first_blood_awards_data(challenge, expected_data)
        
        # There should be no leftovers in the DB
        assert Solves.query.count() == 4
        assert FirstBloodAward.query.count() == 3
        assert Awards.query.count() == 3
        

    destroy_ctfd(app)

def test_awards_recalculated_on_challenge_edited():
    app = create_ctfd(enable_plugins=True)
    with app.app_context():
        register_user(app, name="user1", email="user1@ctfd.io")
        register_user(app, name="user2", email="user2@ctfd.io")
        register_user(app, name="user3", email="user3@ctfd.io")
        register_user(app, name="user4", email="user4@ctfd.io")
        register_user(app, name="user5", email="user5@ctfd.io")
    
        challenge_data = {
            "name": "name",
            "category": "category",
            "description": "description",
            "value": 100,
            "first_blood_bonus[0]": 30,
            "first_blood_bonus[1]": 20,
            "first_blood_bonus[2]": 10,
            "state": "visible",
            "type": "firstblood",
        }
        req = FakeRequest(form=challenge_data)
        challenge = FirstBloodValueChallenge.create(req)
        gen_flag(app.db, challenge_id=challenge.id, content="flag")

        assert challenge.value == 100
        assert challenge.first_blood_bonus[0] == 30
        assert challenge.first_blood_bonus[1] == 20
        assert challenge.first_blood_bonus[2] == 10
        
        for user in ["user1", "user2", "user3", "user4", "user5"]:
            client = login_as_user(app, name=user, password="password")
            with client.session_transaction():
                data = {"submission": "flag", "challenge_id": challenge.id}
                r = client.post("/api/v1/challenges/attempt", json=data)
                assert r.status_code == 200
        
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": 30, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user2", "solved": True, "bonus_points": 20, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user3", "solved": True, "bonus_points": 10, "bonus_num": 3, "bonus_name": "3rd"},
            {"user": "user4", "solved": True, "bonus_points": None},
            {"user": "user5", "solved": True, "bonus_points": None},
        ]
        _check_first_blood_awards_data(challenge, expected_data)
                
        # Admin changes the values and adds one level
        challenge_data = {
            "first_blood_bonus[0]": 300,
            "first_blood_bonus[1]": 200,
            "first_blood_bonus[2]": 100,
            "first_blood_bonus[3]": 50,
        }

        client = login_as_user(app, name="admin", password="password")
        r = client.patch("/api/v1/challenges/{0}".format(challenge.id), json=challenge_data)
        assert r.status_code == 200

        # First blood should have recalculated
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": 300, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user2", "solved": True, "bonus_points": 200, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user3", "solved": True, "bonus_points": 100, "bonus_num": 3, "bonus_name": "3rd"},
            {"user": "user4", "solved": True, "bonus_points": 50,  "bonus_num": 4, "bonus_name": "4th"},
            {"user": "user5", "solved": True, "bonus_points": None},
        ]
        _check_first_blood_awards_data(challenge, expected_data)
        
        # There should be no leftovers in the DB
        assert Solves.query.count() == 5
        assert FirstBloodAward.query.count() == 4
        assert Awards.query.count() == 4
                
        # Admin removes one level
        challenge_data = {
            "first_blood_bonus[0]": 300,
            "first_blood_bonus[1]": 200,
            "first_blood_bonus[2]": 100,
        }

        client = login_as_user(app, name="admin", password="password")
        r = client.patch("/api/v1/challenges/{0}".format(challenge.id), json=challenge_data)
        assert r.status_code == 200

        # First blood should have recalculated
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": 300, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user2", "solved": True, "bonus_points": 200, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user3", "solved": True, "bonus_points": 100, "bonus_num": 3, "bonus_name": "3rd"},
            {"user": "user4", "solved": True, "bonus_points": None},
            {"user": "user5", "solved": True, "bonus_points": None},
        ]
        _check_first_blood_awards_data(challenge, expected_data)
        
        # There should be no leftovers in the DB
        assert Solves.query.count() == 5
        assert FirstBloodAward.query.count() == 3
        assert Awards.query.count() == 3
        

    destroy_ctfd(app)

def test_awards_recalculated_on_challenge_hidden():
    app = create_ctfd(enable_plugins=True)
    with app.app_context():
        register_user(app, name="user1", email="user1@ctfd.io")
        register_user(app, name="user2", email="user2@ctfd.io")
        register_user(app, name="user3", email="user3@ctfd.io")
        register_user(app, name="user4", email="user4@ctfd.io")
        register_user(app, name="user5", email="user5@ctfd.io")
    
        challenge_data = {
            "name": "name",
            "category": "category",
            "description": "description",
            "value": 100,
            "first_blood_bonus[0]": 30,
            "first_blood_bonus[1]": 20,
            "first_blood_bonus[2]": 10,
            "state": "visible",
            "type": "firstblood",
        }
        req = FakeRequest(form=challenge_data)
        challenge = FirstBloodValueChallenge.create(req)
        gen_flag(app.db, challenge_id=challenge.id, content="flag")

        assert challenge.value == 100
        assert challenge.first_blood_bonus[0] == 30
        assert challenge.first_blood_bonus[1] == 20
        assert challenge.first_blood_bonus[2] == 10
        
        for day, user in enumerate(["user1", "user2", "user3", "user4", "user5"], start=10):
            with freeze_time("2020-10-%02d 12:34:56" % day):
                client = login_as_user(app, name=user, password="password")
                with client.session_transaction():
                    data = {"submission": "flag", "challenge_id": challenge.id}
                    r = client.post("/api/v1/challenges/attempt", json=data)
                    assert r.status_code == 200
        
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": 30, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user2", "solved": True, "bonus_points": 20, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user3", "solved": True, "bonus_points": 10, "bonus_num": 3, "bonus_name": "3rd"},
            {"user": "user4", "solved": True, "bonus_points": None},
            {"user": "user5", "solved": True, "bonus_points": None},
        ]
        _check_first_blood_awards_data(challenge, expected_data)
                
        # Admin hides the challenge
        challenge_data = {
            "state": "hidden"
        }

        client = login_as_user(app, name="admin", password="password")
        r = client.patch("/api/v1/challenges/{0}".format(challenge.id), json=challenge_data)
        assert r.status_code == 200

        # First blood awards should have disappeared
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": None},
            {"user": "user2", "solved": True, "bonus_points": None},
            {"user": "user3", "solved": True, "bonus_points": None},
            {"user": "user4", "solved": True, "bonus_points": None},
            {"user": "user5", "solved": True, "bonus_points": None},
        ]
        _check_first_blood_awards_data(challenge, expected_data)
        assert Solves.query.count() == 5
        assert FirstBloodAward.query.count() == 0
        assert Awards.query.count() == 0

        # Admin shows the challenge
        challenge_data = {
            "state": "visible"
        }

        client = login_as_user(app, name="admin", password="password")
        r = client.patch("/api/v1/challenges/{0}".format(challenge.id), json=challenge_data)
        assert r.status_code == 200

        # First blood should have recalculated
        expected_data = [
            {"user": "user1", "solved": True, "bonus_points": 30, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user2", "solved": True, "bonus_points": 20, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user3", "solved": True, "bonus_points": 10, "bonus_num": 3, "bonus_name": "3rd"},
            {"user": "user4", "solved": True, "bonus_points": None},
            {"user": "user5", "solved": True, "bonus_points": None},
        ]
        _check_first_blood_awards_data(challenge, expected_data)
        assert Solves.query.count() == 5
        assert FirstBloodAward.query.count() == 3
        assert Awards.query.count() == 3
        

    destroy_ctfd(app)

# TODO: test_awards_generates_no_awards_for_hidden_teams
# TODO: test_awards_recalculated_on_team_hidden
# TODO: test_awards_recalculated_on_team_removed
