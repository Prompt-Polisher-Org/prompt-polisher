import asyncio
import asyncpg

async def main():
    try:
        conn = await asyncpg.connect('postgresql://user:password@localhost:5432/prompt_db')
        print("Successfully connected to the database!")
        await conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
