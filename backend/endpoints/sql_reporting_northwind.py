import openai
import pandas as pd
from aiohttp import web
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

code_model = "code-davinci-002"

engine = create_engine("postgresql://postgres:postgres@localhost:55432/northwind")


def get_rows(engine):
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
        SELECT table_name, column_name, data_type, character_maximum_length, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_catalog = 'northwind';
    """
            )
        )
        rows = result.all()
    return rows


def create_table_definition(rows):
    prompt = "### postgres SQL tables, with their properties:\n"
    tables = {}
    for row in rows:
        if row.table_name not in tables:
            tables[row.table_name] = []
        tables[row.table_name].append(row)

    for table_name, table_rows in tables.items():
        column_defs = ", ".join(
            [
                row.column_name
                + " "
                + row.data_type
                + (
                    "(" + str(row.character_maximum_length) + ")"
                    if row.character_maximum_length is not None
                    else ""
                )
                + (" NOT NULL" if row.is_nullable == "NO" else "")
                for row in table_rows
            ]
        )
        prompt += f"# {table_name}({column_defs})\n"

    return prompt


def combine_prompts(query_prompt):
    definition = create_table_definition(get_rows(engine))
    query_init_string = f"### A query to Answer: {query_prompt}\nSELECT"
    return definition + query_init_string


def handle_response(response):
    query = response.choices[0].text

    # if query start with new line, add select

    if query.startswith("\n"):
        query = "select" + query

    if query.startswith(" "):
        query = "select" + query

    return query


async def nl_to_sql(question) -> dict:
    try:
        response = openai.Completion.create(
            model="code-davinci-002",
            prompt=combine_prompts(str(question)),
            temperature=0,
            max_tokens=1000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,  # Fixed missing value
            stop=["#", ";"],
        )
        query = handle_response(response)
        # make coulmn names lower case and inside double quotes
        # make coulmn names inside

        with engine.connect() as conn:

            result = conn.execute(text(query))
            query_response = result.all()
            query_json = pd.DataFrame(query_response).to_json(orient='records')
            return {"query": query, 'promptResponse': query_json}
    except Exception as e:
        return {"promptResponse": e}
