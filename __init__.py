import itertools

from flask import Blueprint
from sqlalchemy import event
from sqlalchemy.schema import DDL

from CTFd.models import Challenges, Solves, Awards, db
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.utils.modes import get_model
from CTFd.utils.humanize.numbers import ordinalize


class FirstBloodChallenge(Challenges):
    __mapper_args__ = {"polymorphic_identity": "firstblood"}
    id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )
    first_blood_bonus = db.Column(db.JSON)

    def __init__(self, *args, **kwargs):
        # This is kind of a hack because serializeJSON in CTFd does not support arrays
        first_blood_bonus = None
        for attr, value in kwargs.items():
            if attr.startswith('first_blood_bonus'):
                first_blood_bonus = []
        if first_blood_bonus is not None:
            for i in itertools.count():
                attr = 'first_blood_bonus[{0}]'.format(i)
                if attr not in kwargs:
                    break
                first_blood_bonus.append(int(kwargs[attr]) if kwargs[attr] != '' else None)
                del kwargs[attr]
            while first_blood_bonus[-1] is None:
                first_blood_bonus.pop()
            kwargs['first_blood_bonus'] = first_blood_bonus
    
        super(FirstBloodChallenge, self).__init__(**kwargs)

class FirstBloodAward(Awards):
    __mapper_args__ = {"polymorphic_identity": "firstblood"}
    id = db.Column(
        db.Integer, db.ForeignKey("awards.id", ondelete="CASCADE"), primary_key=True
    )
    solve_id = db.Column(db.Integer, db.ForeignKey("solves.id", ondelete="RESTRICT"))  # TODO: I got tired of trying to get removes to work for now
    solve_num = db.Column(db.Integer, nullable=False)

class FirstBloodValueChallenge(BaseChallenge):
    id = "firstblood"  # Unique identifier used to register challenges
    name = "firstblood"  # Name of a challenge type
    templates = {  # Handlebars templates used for each aspect of challenge editing & viewing
        "create": "/plugins/CTFd_first_blood/assets/create.html",
        "update": "/plugins/CTFd_first_blood/assets/update.html",
        "view": "/plugins/CTFd_first_blood/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/CTFd_first_blood/assets/create.js",
        "update": "/plugins/CTFd_first_blood/assets/update.js",
        "view": "/plugins/CTFd_first_blood/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/CTFd_first_blood/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "firstblood_challenges",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )
    challenge_model = FirstBloodChallenge

    @classmethod
    def update(cls, challenge, request):
        """
        This method is used to update the information associated with a challenge. This should be kept strictly to the
        Challenges table and any child tables.
        :param challenge:
        :param request:
        :return:
        """
        
        data = request.form or request.get_json()
        
        # This is kind of a hack because serializeJSON in CTFd does not support arrays
        first_blood_bonus = None
        for attr, value in data.items():
            if attr.startswith('first_blood_bonus'):
                first_blood_bonus = []
                continue
            setattr(challenge, attr, value)
        if first_blood_bonus is not None:
            for i in itertools.count():
                attr = 'first_blood_bonus[{0}]'.format(i)
                if attr not in data:
                    break
                first_blood_bonus.append(int(data[attr]) if data[attr] != '' else None)
            while first_blood_bonus[-1] is None:
                first_blood_bonus.pop()
            setattr(challenge, 'first_blood_bonus', first_blood_bonus)

        db.session.commit()
        FirstBloodValueChallenge.recalculate_awards(challenge)
        return challenge

    @classmethod
    def solve(cls, user, team, challenge, request):
        super().solve(user, team, challenge, request)
        solve = Solves.query.filter(Solves.challenge_id == challenge.id)
        if user is not None:
            solve = solve.filter(Solves.user_id == user.id)
        if team is not None:
            solve = solve.filter(Solves.team_id == team.id)
        solve = solve.first()


        Model = get_model()

        solve_count = (
            Solves.query.join(Model, Solves.account_id == Model.id)
            .filter(
                Solves.id <= solve.id,
                Solves.challenge_id == challenge.id,
                Model.hidden == False,
                Model.banned == False,
            )
            .count()
        )
        
        award_points = challenge.first_blood_bonus[solve_count - 1] if (solve_count - 1) < len(challenge.first_blood_bonus) else None
        if award_points is not None:
            award = FirstBloodAward(
                user_id=user.id if user is not None else None,
                team_id=team.id if team is not None else None,
                name='{0} blood for {1}'.format(ordinalize(solve_count), challenge.name),
                description='Bonus points for being the {0} to solve the challenge'.format(ordinalize(solve_count)),
                category='First Blood',
                value=award_points,
                solve_id=solve.id,
                solve_num=solve_count,
            )
            db.session.add(award)
            db.session.commit()

    @classmethod
    def recalculate_awards(cls, challenge):
        # TODO: The rewards should be recalculated whenever a solve is removed or points settings are changed
        pass


def load(app):
    app.db.create_all()
    app.jinja_env.filters.update(ordinalize=ordinalize)
    CHALLENGE_CLASSES["firstblood"] = FirstBloodValueChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/CTFd_first_blood/assets/"
    )
