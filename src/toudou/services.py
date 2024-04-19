import csv
import dataclasses
import io

from datetime import datetime

from toudou.models import create_todo, get_all_todos, Todo


def export_to_csv() -> io.StringIO:
    output = io.StringIO()
    todos = get_all_todos()
    fieldnames = list(dir(todos[0]))
    csv_writer = csv.DictWriter(
        output,
        fieldnames=fieldnames
    )
    csv_writer.writeheader()
    for todo in todos:
        csv_writer.writerow(vars(todo))
    return output


def import_from_csv(csv_file: io.StringIO) -> None:
    csv_reader = csv.DictReader(
        csv_file,
        fieldnames=[f.name for f in dataclasses.fields(Todo)]
    )
    for row in csv_reader:
        create_todo(
            task=row["task"],
            due=datetime.fromisoformat(row["due"]) if row["due"] else None,
            complete=row["complete"] == "True"
        )
