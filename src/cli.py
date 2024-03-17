import click
import schedule

import time
from src.reporter.report import Reporter

def output():

    reporter = Reporter()
    numbers = reporter.scan_and_download()
    click.echo(f"{numbers}")

@click.command()

def main():

    schedule.every(12).hours.do(output)

    while True:
        schedule.run_pending()
        time.sleep(1)
if __name__ == "__main__":
    main()
