from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from models_two import journal_entries,accounts,inv_purchases,inv_sales,customers,vendors
import asyncio
from sqlalchemy import text,select,func,and_,Subquery

db_url='postgresql+asyncpg://postgres:mishaalmalik@localhost:5432/postgres'

eng=create_async_engine(db_url)

my_session=async_sessionmaker(bind=eng,expire_on_commit=False)

async def open_conn():
    async with my_session() as session_local:
        data=await session_local.execute(text("""SELECT account_name,account_type
                                          from accounts"""))
        for a,b in data:
            print(a,b)
            print("-"*20)

async def add_vendor(vendor:str):
    async with my_session() as session_local:
        ven=vendors(vendor_name=vendor)
        session_local.add(ven)
        await session_local.commit()
        print('Added vendor:{}'.format(vendor))

async def select_stuffs():
    async with my_session() as sessionlocal:
        smt=select(journal_entries.user_id,
                   journal_entries.account_name,func.sum(journal_entries.debit_amt),
                   func.sum(journal_entries.credit_amt)).group_by(journal_entries.user_id,journal_entries.account_name).subquery()
        #data=await sessionlocal.execute(text("SELECT account_name,account_type from accounts"))
        #data=await sessionlocal.execute(smt)
        smt=select(accounts.account_name,accounts.account_type).join(smt,and_(accounts.user_id == smt.c.user_id,
                                                accounts.account_name == smt.c.account_name))
        data=await sessionlocal.execute(smt)
        for x,y in data:
            print(x,y)
            print("-"*20)
asyncio.run(select_stuffs())
            
