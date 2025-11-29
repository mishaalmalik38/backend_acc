import mysql.connector
import datetime
from datetime import timedelta
from sqlalchemy import create_engine,func,distinct,text,and_,or_,select
from sqlalchemy.orm import sessionmaker
from practice_two import Users,accounts,journal_entries,inventories,customers,vendors,inv_purchases,inv_sales

#dt=datetime.datetime.now() + timedelta(minutes=30)
dbase=mysql.connector.connect(
    database='react_proj',password='mishaalmalik',
    host='localhost',user='root'
)
dbase_two=create_engine('mysql+mysqlconnector://root:mishaalmalik@localhost/my_proj_two')
my_sess=sessionmaker(bind=dbase_two)
my_session=my_sess()

cur=dbase.cursor(dictionary=True)
cur.execute("""SELECT * from vendors""")
res=cur.fetchall()

a=my_session.query(inv_purchases.user_id,inv_purchases.inv_name,func.sum(inv_purchases.qty).label('total')).group_by(inv_purchases.user_id,inv_purchases.inv_name).first()
b=my_session.query(accounts).filter_by(user_id=6,account_subtype='current assets').all()

#count_f=my_session.query(func.count(journal_entries.id)).filter_by(user_id=6).all()
c=my_session.query(func.count(distinct(journal_entries.id))).filter_by(user_id=6).scalar()
d=my_session.query(func.max(journal_entries.id)).filter_by(user_id=6).scalar()
e=my_session.query(inventories.account_name).filter_by(user_id=6,inv_name='stock_10').scalar()
ee=my_session.query(accounts.account_name).filter_by(user_id=6,account_name='eeeee').scalar()
a=my_session.query(inv_sales).filter_by(id=5).first()
ic=my_session.query(accounts.account_name).filter_by(account_type='income statement').all()
ic2=my_session.query(journal_entries.account_name,func.sum(journal_entries.debit_amt),
                     func.sum(journal_entries.credit_amt)).group_by(journal_entries.account_name).all()

ie_bal=my_session.execute(text("""SELECT a.account_name,SUM(debit_amt-credit_amt) as 'balance'
                   FROM journal_entries a,accounts b
                   WHERE a.account_name=b.account_name AND 
                   b.account_type='income statement' GROUP BY a.account_name"""))

bal_two=my_session.query(journal_entries.account_name,func.sum(journal_entries.debit_amt),
                         func.sum(journal_entries.credit_amt)).join(accounts,
                                               and_(journal_entries == 6,journal_entries.account_name == accounts.account_name,
                                                    accounts.account_type == 'income statement')).group_by(journal_entries.account_name)
to_close={'expenses':{},'incomes':{},'bal':0}
total_expenses=0
total_incomes=0

for a,b,c in bal_two:
    num=int(b)
    bal=int(b-c)
    if num > 0:
        to_close['expenses'][a]=bal
        #to_close['bal'] += num
    else:
        to_close['incomes'][a]=bal
        #to_close['bal'] += num
    to_close['bal'] += bal


journal_id=my_session.query(func.max(journal_entries.id)).scalar()


#closing process
for i in to_close['expenses']:
    acc_val=to_close['expenses'][i]
    entry=journal_entries(id=journal_id+1,account_name=i,debit_amt=0,credit_amt=acc_val)
    my_session.add(entry)

for i in to_close['incomes']:
    acc_value=to_close['incomes'][i] * -1
    entry=journal_entries(id=journal_id+1,account_name=i,debit_amt=acc_value,credit_amt=0)
    my_session.add(entry)

if to_close['bal'] > 0:
    entry=journal_entries(id=journal_id+1,account_name='p_l_balance',debit_amt=to_close['bal'])
    my_session.add(entry)
else:
    entry=journal_entries(id=journal_id+1,account_name='p_l_balance',debit_amt=0,credit_amt=to_close['bal']*-1)
    my_session.add(entry)

last_query=my_session.query(journal_entries.account_name,journal_entries.debit_amt,journal_entries.credit_amt).filter_by(account_name='p_l_balance').all()

accs=my_session.execute(text("""SELECT account_name,account_type from accounts"""))

cnt=journal_id+1
a=my_session.query(func.max(journal_entries.id)).filter_by(user_id=5).scalar()
cc=select(accounts).where(accounts.account_subtypetwo == 'bank' or accounts.account_subtypetwo == 'cash')
print(cc)