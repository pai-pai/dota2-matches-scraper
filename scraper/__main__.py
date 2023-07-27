import argparse
import datetime

from scraper import GQLRunner


runner = GQLRunner()
today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
date = today + datetime.timedelta(weeks=-1)

parser = argparse.ArgumentParser(
    prog="runner",
    description="Starts dota2 matches parser",
)
parser.add_argument(
    "-dt",
    "--datetime",
    type=datetime.datetime.fromisoformat,
    nargs="?",
    help="Datetime in ISOformat - YYYY-MM-DD:HH:mm:ss",
    const=date,
)
args = parser.parse_args()
if args.datetime:
    runner.get_date_starting_from_date(args.datetime)
else:
    runner.get_init_data()
