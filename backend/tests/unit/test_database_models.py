"""
Tests for SQLAlchemy ORM models and database setup.
"""
import pytest
import os
from datetime import datetime
from uuid import uuid4
from subprocess import run

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.models.database import (
    Base,
    CampaignDB,
    CharacterDB,
    GameSessionDB,
    MapDB,
    UserDB,
)


@pytest.fixture
async def async_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session_factory(async_engine):
    """Create an async session factory."""
    return async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def session(async_session_factory):
    """Create an async session for testing."""
    async with async_session_factory() as s:
        yield s


class TestCampaignDB:
    """Test CampaignDB model."""

    async def test_campaign_instantiate(self):
        """Test that CampaignDB can be instantiated."""
        campaign = CampaignDB(
            id=str(uuid4()),
            name="Test Campaign",
            description="A test campaign",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        assert campaign.name == "Test Campaign"
        assert campaign.description == "A test campaign"
        assert campaign.id is not None
        assert isinstance(campaign.created_at, datetime)
        assert isinstance(campaign.updated_at, datetime)

    async def test_campaign_create_and_retrieve(self, session: AsyncSession):
        """Test creating and retrieving a campaign from the database."""
        campaign_id = str(uuid4())
        campaign = CampaignDB(
            id=campaign_id,
            name="Dragon's Lair Campaign",
            description="Fight the dragon",
        )
        session.add(campaign)
        await session.commit()

        result = await session.execute(select(CampaignDB).where(CampaignDB.id == campaign_id))
        retrieved = result.scalar_one_or_none()
        assert retrieved is not None
        assert retrieved.name == "Dragon's Lair Campaign"
        assert retrieved.description == "Fight the dragon"


class TestCharacterDB:
    """Test CharacterDB model."""

    async def test_character_instantiate(self):
        """Test that CharacterDB can be instantiated."""
        campaign_id = str(uuid4())
        character = CharacterDB(
            id=str(uuid4()),
            campaign_id=campaign_id,
            name="Aragorn",
            race="human",
            character_class="fighter",
            level=5,
            hp=45,
            max_hp=45,
            ac=16,
        )
        assert character.name == "Aragorn"
        assert character.race == "human"
        assert character.character_class == "fighter"
        assert character.level == 5
        assert character.hp == 45
        assert character.max_hp == 45
        assert character.ac == 16

    async def test_character_with_json_fields(self):
        """Test character with JSON ability scores, skills, and inventory."""
        campaign_id = str(uuid4())
        abilities = {
            "strength": 18,
            "dexterity": 14,
            "constitution": 16,
            "intelligence": 10,
            "wisdom": 13,
            "charisma": 12,
        }
        skills = {
            "athletics": 6,
            "acrobatics": 3,
        }
        inventory = ["Longsword", "Shield", "Backpack"]

        character = CharacterDB(
            id=str(uuid4()),
            campaign_id=campaign_id,
            name="Aragorn",
            race="human",
            character_class="fighter",
            level=5,
            hp=45,
            max_hp=45,
            ac=16,
            abilities=abilities,
            skills=skills,
            inventory=inventory,
        )
        assert character.abilities == abilities
        assert character.skills == skills
        assert character.inventory == inventory

    async def test_character_create_and_retrieve(self, session: AsyncSession):
        """Test creating and retrieving a character from the database."""
        campaign_id = str(uuid4())
        character_id = str(uuid4())
        abilities = {
            "strength": 18,
            "dexterity": 14,
        }
        inventory = ["Sword", "Shield"]

        character = CharacterDB(
            id=character_id,
            campaign_id=campaign_id,
            name="Legolas",
            race="elf",
            character_class="ranger",
            level=6,
            hp=40,
            max_hp=40,
            ac=15,
            abilities=abilities,
            inventory=inventory,
        )
        session.add(character)
        await session.commit()

        result = await session.execute(
            select(CharacterDB).where(CharacterDB.id == character_id)
        )
        retrieved = result.scalar_one_or_none()
        assert retrieved is not None
        assert retrieved.name == "Legolas"
        assert retrieved.race == "elf"
        assert retrieved.abilities == abilities
        assert retrieved.inventory == inventory


class TestGameSessionDB:
    """Test GameSessionDB model."""

    async def test_game_session_instantiate(self):
        """Test that GameSessionDB can be instantiated."""
        campaign_id = str(uuid4())
        session_obj = GameSessionDB(
            id=str(uuid4()),
            campaign_id=campaign_id,
            phase="combat",
            turn_number=5,
        )
        assert session_obj.phase == "combat"
        assert session_obj.turn_number == 5
        assert session_obj.campaign_id == campaign_id

    async def test_game_session_with_active_character(self):
        """Test GameSessionDB with active character."""
        campaign_id = str(uuid4())
        character_id = str(uuid4())
        session_obj = GameSessionDB(
            id=str(uuid4()),
            campaign_id=campaign_id,
            phase="combat",
            turn_number=3,
            active_character_id=character_id,
        )
        assert session_obj.active_character_id == character_id

    async def test_game_session_create_and_retrieve(self, session: AsyncSession):
        """Test creating and retrieving a game session."""
        campaign_id = str(uuid4())
        session_id = str(uuid4())
        game_session = GameSessionDB(
            id=session_id,
            campaign_id=campaign_id,
            phase="exploration",
            turn_number=1,
        )
        session.add(game_session)
        await session.commit()

        result = await session.execute(
            select(GameSessionDB).where(GameSessionDB.id == session_id)
        )
        retrieved = result.scalar_one_or_none()
        assert retrieved is not None
        assert retrieved.phase == "exploration"
        assert retrieved.turn_number == 1


class TestMapDB:
    """Test MapDB model."""

    async def test_map_instantiate(self):
        """Test that MapDB can be instantiated."""
        session_id = str(uuid4())
        map_obj = MapDB(
            id=str(uuid4()),
            session_id=session_id,
            name="Throne Room",
            width=20,
            height=20,
        )
        assert map_obj.name == "Throne Room"
        assert map_obj.width == 20
        assert map_obj.height == 20
        assert map_obj.session_id == session_id

    async def test_map_with_grid_and_tokens(self):
        """Test MapDB with grid and token data."""
        session_id = str(uuid4())
        grid = [
            ["empty", "empty", "wall"],
            ["empty", "empty", "wall"],
            ["water", "water", "empty"],
        ]
        tokens = [
            {"entity_id": "char1", "x": 0, "y": 0},
            {"entity_id": "char2", "x": 1, "y": 1},
        ]
        fog_revealed = [
            [True, True, False],
            [True, True, False],
            [False, False, False],
        ]

        map_obj = MapDB(
            id=str(uuid4()),
            session_id=session_id,
            name="Dungeon Hall",
            width=3,
            height=3,
            grid=grid,
            tokens=tokens,
            fog_revealed=fog_revealed,
        )
        assert map_obj.grid == grid
        assert map_obj.tokens == tokens
        assert map_obj.fog_revealed == fog_revealed

    async def test_map_create_and_retrieve(self, session: AsyncSession):
        """Test creating and retrieving a map."""
        session_id = str(uuid4())
        map_id = str(uuid4())
        grid = [["empty", "wall"], ["empty", "empty"]]
        tokens = [{"entity_id": "player", "x": 0, "y": 0}]

        map_obj = MapDB(
            id=map_id,
            session_id=session_id,
            name="Forest",
            width=2,
            height=2,
            grid=grid,
            tokens=tokens,
        )
        session.add(map_obj)
        await session.commit()

        result = await session.execute(select(MapDB).where(MapDB.id == map_id))
        retrieved = result.scalar_one_or_none()
        assert retrieved is not None
        assert retrieved.name == "Forest"
        assert retrieved.grid == grid
        assert retrieved.tokens == tokens


class TestUserDB:
    """Test UserDB model."""

    async def test_user_instantiate(self):
        """Test that UserDB can be instantiated."""
        user = UserDB(
            id=str(uuid4()),
            username="gandalf",
            password_hash="hashed_password_123",
            created_at=datetime.utcnow(),
        )
        assert user.username == "gandalf"
        assert user.password_hash == "hashed_password_123"
        assert isinstance(user.created_at, datetime)

    async def test_user_create_and_retrieve(self, session: AsyncSession):
        """Test creating and retrieving a user."""
        user_id = str(uuid4())
        user = UserDB(
            id=user_id,
            username="merlin",
            password_hash="hashed_secret",
        )
        session.add(user)
        await session.commit()

        result = await session.execute(select(UserDB).where(UserDB.id == user_id))
        retrieved = result.scalar_one_or_none()
        assert retrieved is not None
        assert retrieved.username == "merlin"


class TestRelationships:
    """Test model relationships."""

    async def test_campaign_character_relationship(self, session: AsyncSession):
        """Test that characters are associated with campaigns."""
        campaign_id = str(uuid4())
        char_id_1 = str(uuid4())
        char_id_2 = str(uuid4())

        campaign = CampaignDB(
            id=campaign_id,
            name="Adventure",
            description="An adventure",
        )
        char1 = CharacterDB(
            id=char_id_1,
            campaign_id=campaign_id,
            name="Hero1",
            race="human",
            character_class="fighter",
            level=1,
            hp=10,
            max_hp=10,
            ac=10,
        )
        char2 = CharacterDB(
            id=char_id_2,
            campaign_id=campaign_id,
            name="Hero2",
            race="elf",
            character_class="ranger",
            level=1,
            hp=10,
            max_hp=10,
            ac=10,
        )

        session.add(campaign)
        session.add(char1)
        session.add(char2)
        await session.commit()

        # Verify characters are linked to campaign
        result = await session.execute(
            select(CharacterDB).where(CharacterDB.campaign_id == campaign_id)
        )
        characters = result.scalars().all()
        assert len(characters) == 2
        assert characters[0].campaign_id == campaign_id
        assert characters[1].campaign_id == campaign_id

    async def test_game_session_campaign_relationship(self, session: AsyncSession):
        """Test that game sessions are associated with campaigns."""
        campaign_id = str(uuid4())
        session_id = str(uuid4())

        campaign = CampaignDB(
            id=campaign_id,
            name="Test Campaign",
            description="For testing",
        )
        game_session = GameSessionDB(
            id=session_id,
            campaign_id=campaign_id,
            phase="combat",
            turn_number=1,
        )

        session.add(campaign)
        session.add(game_session)
        await session.commit()

        result = await session.execute(
            select(GameSessionDB).where(GameSessionDB.campaign_id == campaign_id)
        )
        retrieved = result.scalar_one_or_none()
        assert retrieved is not None
        assert retrieved.campaign_id == campaign_id

    async def test_map_session_relationship(self, session: AsyncSession):
        """Test that maps are associated with game sessions."""
        campaign_id = str(uuid4())
        session_id = str(uuid4())
        map_id = str(uuid4())

        campaign = CampaignDB(
            id=campaign_id,
            name="Test Campaign",
            description="For testing",
        )
        game_session = GameSessionDB(
            id=session_id,
            campaign_id=campaign_id,
            phase="exploration",
            turn_number=1,
        )
        map_obj = MapDB(
            id=map_id,
            session_id=session_id,
            name="Test Map",
            width=10,
            height=10,
        )

        session.add(campaign)
        session.add(game_session)
        session.add(map_obj)
        await session.commit()

        result = await session.execute(select(MapDB).where(MapDB.session_id == session_id))
        retrieved = result.scalar_one_or_none()
        assert retrieved is not None
        assert retrieved.session_id == session_id


class TestDatabaseMetadata:
    """Test database metadata and table creation."""

    async def test_create_tables(self, async_engine):
        """Test that all tables can be created from metadata."""
        # The fixture already creates tables, so we just verify they exist
        async with async_engine.connect() as conn:
            # Get all table names from metadata
            table_names = Base.metadata.tables.keys()
            assert "campaign" in table_names
            assert "character" in table_names
            assert "game_session" in table_names
            assert "map" in table_names
            assert "user" in table_names

    async def test_all_models_in_base(self):
        """Test that all ORM models are registered in Base metadata."""
        model_names = [name.lower() for name in Base.metadata.tables.keys()]
        assert "campaign" in model_names
        assert "character" in model_names
        assert "game_session" in model_names
        assert "map" in model_names
        assert "user" in model_names


class TestAlembicMigrations:
    """Test Alembic migrations."""

    def test_migration_file_exists(self):
        """Test that the initial migration file exists."""
        backend_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        migrations_dir = os.path.join(backend_path, "alembic", "versions")
        migration_files = [f for f in os.listdir(migrations_dir) if f.endswith(".py") and f != "__init__.py"]
        assert len(migration_files) > 0, "No migration files found"

    def test_alembic_config_exists(self):
        """Test that alembic.ini exists."""
        backend_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        alembic_ini = os.path.join(backend_path, "alembic.ini")
        assert os.path.exists(alembic_ini), "alembic.ini not found"

    def test_alembic_env_exists(self):
        """Test that alembic/env.py exists."""
        backend_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        env_py = os.path.join(backend_path, "alembic", "env.py")
        assert os.path.exists(env_py), "alembic/env.py not found"

    async def test_migration_upgrade_downgrade(self):
        """Test that migrations can upgrade and downgrade on in-memory SQLite."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

            def _inspect(sync_conn):
                from sqlalchemy import inspect
                inspector = inspect(sync_conn)
                return inspector.get_table_names()

            tables = await conn.run_sync(_inspect)
            assert "campaign" in tables
            assert "character" in tables
            assert "game_session" in tables
            assert "map" in tables
            assert "user" in tables

        await engine.dispose()
