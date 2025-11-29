from sqlalchemy import Column,Integer,String,ForeignKey,DateTime,func,create_engine,alias
from sqlalchemy.orm import sessionmaker,declarative_base

#mysql+mysqlconnector://root:password@localhost/testdb
engine=create_engine('mysql+mysqlconnector://root:mishaalmalik@localhost/my_proj_two')
Base=declarative_base()

my_ses=sessionmaker(bind=engine)

def get_db_two():
    my_session=my_ses()
    try:
        yield my_session
    finally:
        my_session.close()

class Users(Base):
    __tablename__='main_users'
    id=Column(Integer,primary_key=True,autoincrement=True)
    user_name=Column(String(50),primary_key=True,nullable=False)
    user_pass=Column(String(200))
    gmail=Column(String(50))

class accounts(Base):
    __tablename__='accounts'
    user_id=Column(Integer,ForeignKey('main_users.id'))
    account_name=Column(String(100),primary_key=True)
    account_nature=Column(String(20))
    account_type=Column(String(50))
    account_subtype=Column(String(50))
    account_subtypetwo=Column(String(50))
    amount=Column(Integer,default=0)

class journal_entries(Base):
    __tablename__='journal_entries'
    auto_id=Column(Integer,primary_key=True,autoincrement=True)
    id=Column(Integer)
    date_of_entry=Column(DateTime,server_default=func.now())
    user_id=Column(Integer,ForeignKey("main_users.id"))
    account_name=Column(String(50))
    debit_amt=Column(Integer)
    credit_amt=Column(Integer)

class inventories(Base):
    __tablename__='inventories'
    id=Column(Integer,primary_key=True,autoincrement=True)
    inv_name=Column(String(50))
    account_name=Column(String(50))
    user_id=Column(Integer,ForeignKey("main_users.id"))

class customers(Base):
    __tablename__='customers'
    id=Column(Integer,primary_key=True,autoincrement=True)
    customer_name=Column(String(50))
    cust_ledger=Column(String(50))
    gmail=Column(String(50))
    user_id=Column(Integer,ForeignKey('main_users.id'))

class vendors(Base):
    __tablename__='vendors'
    id=Column(Integer,primary_key=True,autoincrement=True)
    vendor_name=Column(String(50))
    cust_ledger=Column(String(50))
    gmail=Column(String(50))
    user_id=Column(Integer,ForeignKey('main_users.id'))

class inv_purchases(Base):
    __tablename__='inv_purchases'
    id=Column(Integer,primary_key=True,autoincrement=True)
    date_of_purchase=Column(DateTime,server_default=func.now())
    inv_name=Column(String(50))
    qty=Column(Integer)
    price=Column(Integer)
    user_id=Column(Integer,ForeignKey("main_users.id"))

class inv_sales(Base):
    __tablename__="inv_sales"
    id=Column(Integer,primary_key=True,autoincrement=True)
    date_of_sale=Column(DateTime,server_default=func.now())
    customer_name=Column(String(50))
    journal_id=Column(Integer)
    amount_paid=Column(Integer)
    cur_status=Column(String(50))
    inv_name=Column(String(50))
    qty=Column(Integer)
    sales_price=Column(Integer)
    cost_of_goods_sold=Column(Integer)
    bad_debts_amount=Column(Integer)
    return_qty=Column(Integer)
    user_id=Column(Integer,ForeignKey("main_users.id"))

class closing_process(Base):
    __tablename__='closing_process'
    auto_id=Column(Integer,autoincrement=True,primary_key=True)
    user_id=Column(Integer,ForeignKey('main_users.id'))
    journal_id=Column(Integer)