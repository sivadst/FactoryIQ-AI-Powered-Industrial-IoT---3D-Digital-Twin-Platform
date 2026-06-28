import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import AsyncSessionLocal, engine
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings

async def init_db() -> None:
    async with engine.begin() as conn:
        # Create hypertable for telemetry
        await conn.execute(
            text("SELECT create_hypertable('telemetry', 'time', if_not_exists => TRUE);")
        )

    async with AsyncSessionLocal() as session:
        # Check if admin user exists
        from sqlalchemy.future import select
        result = await session.execute(select(User).filter(User.username == "admin"))
        user = result.scalars().first()
        if not user:
            user_in = User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="System Administrator",
                role="Administrator",
                is_active=True
            )
            session.add(user_in)
            await session.commit()
            print("Created default admin user.")

if __name__ == "__main__":
    from sqlalchemy import text
    asyncio.run(init_db())
