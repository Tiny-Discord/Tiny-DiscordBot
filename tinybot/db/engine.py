from __future__ import annotations

import os
from typing import Awaitable, List, Self, Type

import asyncpg
from dotenv import load_dotenv
from piccolo.engine import PostgresEngine
from piccolo.engine.sqlite import SQLiteEngine
from piccolo.table import Table, create_db_tables

load_dotenv('../.env')


class DBEngine:
    """
    Main Database Engine

    Determines which driver to use (Postgres or SQLite)
    Handles cog table migrations, defaults, and creation as well
    as initial db creation.
    """

    def __init__(self: Self, path: str, cog_name: str) -> None:
        self.path = path
        self.cog_name = cog_name

    def connect(self: Self) -> SQLiteEngine | PostgresEngine:
        """
        Awaitable that returns the client's desired database engine.

        Example:
            db = DBEngine(path=os.getcwd(), cog_name='MyCog').connect()

            Then you can add the db to your Table class.

        Returns
        -------
            SQLiteEngine or PostgresEngine
        """
        if os.getenv("DB_TYPE") == 'sqlite':
            return SQLiteEngine(path=f'{self.path}/{self.cog_name}.sqlite')
        elif os.getenv("DB_TYPE") == 'postgres':
            return PostgresEngine(
                config={
                    'host': os.getenv("DB_HOST"),
                    'database': self.cog_name,
                    'user': os.getenv("DB_USER"),
                    'password': os.getenv("DB_PASSWORD")
                })

    async def postgres_create_db_and_connect(self: Self) -> Awaitable[None]:
        """
        Drops down to asyncpg to see if a postgres db matching the cog name exists.
        If it does not, then it will connect to the default db (postgres) and
        create the necessary database.

        Afterward the connection is closed.

        Returns
        -------
            None
        """
        try:
            conn = await asyncpg.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=self.cog_name)
        except asyncpg.InvalidCatalogNameError:
            # Database for cog does not exist, create it.
            conn = await asyncpg.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database='postgres')
            await conn.execute(
                f'CREATE DATABASE "{self.cog_name}" OWNER "{os.getenv("DB_USER")}"'
            )
            conn.close()
        else:
            conn.close()

    async def setup(self: Self, tables: List[Type[Table]], add_defaults: bool = False) -> Awaitable[None]:
        """

        Parameters
        ----------
        tables: List[Type[Table]]
            Required parameter that unpacks all of your table models to add them to the database.
            It will skip table creation if it's already been added.

        add_defaults: bool Default: False
            It will attempt to insert a row with all of your default values that were set on the table model.

        Returns
        -------
            None
        """
        if os.getenv('DB_TYPE') == 'postgres':
            await self.postgres_create_db_and_connect()

        await create_db_tables(*tables, if_not_exists=True)
        if add_defaults:
            for table in tables:
                if await table.count() > 0:
                    pass
                else:
                    await table.insert(table())
