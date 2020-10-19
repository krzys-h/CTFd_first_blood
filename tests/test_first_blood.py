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
        
        expected_data = [
            {"user": "user1", "bonus_points": 30, "bonus_num": 1, "bonus_name": "1st"},
            {"user": "user2", "bonus_points": 20, "bonus_num": 2, "bonus_name": "2nd"},
            {"user": "user3", "bonus_points": 10, "bonus_num": 3, "bonus_name": "3rd"},
            {"user": "user4", "bonus_points": None},
        ]
        for expected in expected_data:
            client = login_as_user(app, name=expected['user'], password="password")
            with client.session_transaction():
                data = {"submission": "flag", "challenge_id": challenge.id}
                r = client.post("/api/v1/challenges/attempt", json=data)
                assert r.status_code == 200
            
            solves = Solves.query.join(Users, Solves.user_id == Users.id).filter(Users.name == expected['user'], Solves.challenge_id == challenge.id).all()
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

    destroy_ctfd(app)

@pytest.mark.skip(reason="TODO")
def test_awards_deleted_on_challenge_removal():
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

@pytest.mark.skip(reason="TODO")
def test_awards_recalculated_on_solve_removal():
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
        
        for expected in expected_data:
            solves = Solves.query.join(Users, Solves.user_id == Users.id).filter(Users.name == expected['user'], Solves.challenge_id == challenge.id).all()
            if not expected['solved']:
                assert len(solves) == 0
            else:
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

    destroy_ctfd(app)
