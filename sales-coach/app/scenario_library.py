from sales_coach.app.scenario_fetcher import FIXED_SCENARIOS  # noqa: F401
from sales_coach.app.scenario_loader import ScenarioLoader
from sales_coach.app.scenario_simulator import ScenarioSimulator

_loader = ScenarioLoader()
_simulator = ScenarioSimulator()


def get_scenarios_by_category(category: str):
    return _loader.get_scenarios_by_category(category)


def get_scenario_by_difficulty(difficulty: str):
    return _loader.get_scenario_by_difficulty(difficulty)


def generate_training_scenarios():
    return _simulator.generate_training_scenarios()


def append_scenarios_to_db(conn, scenarios, created_by=1):
    return _simulator.append_scenarios_to_db(conn, scenarios, created_by)
