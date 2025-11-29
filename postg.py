import psycopg2
import datetime
from datetime import datetime,date
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from models_two import customers,vendors,accounts,journal_entries,inv_purchases,inv_sales,closing_process
from sqlalchemy import text,select,delete,func,and_,or_


engine=create_engine('postgresql+psycopg2://postgres:mishaalmalik@localhost:5432/postgres')
dbase=psycopg2.connect(
    database='postgres',user='postgres',host='localhost',
    password='mishaalmalik',
    port=5432
)
sessionlocal=sessionmaker(bind=engine)
my_session=sessionlocal()
#a=my_session.query(inv_purchases).filter_by(user_id=1,inv_name='pillows').all()
#b=my_session.query(inv_purchases).filter_by(user_id=1,inv_name='pillows').order_by(inv_purchases.date_of_purchase).all()
#c=my_session.execute(text("""SELECT user_id,account_name,SUM(debit_amt-credit_amt) AS balance
#from journal_entries GROUP BY user_id,account_name HAVING user_id=1;"""))


#d=my_session.execute(text("""SELECT x.user_id,x.account_name,x.account_type,x.account_subtype,
#    x.account_subtypetwo,COALESCE(balance,0) as bal
#    from accounts x LEFT JOIN 
#    (SELECT user_id,account_name,SUM(debit_amt-credit_amt) AS balance
#    FROM journal_entries GROUP BY user_id,account_name HAVING user_id=:id_user) y
#    ON x.user_id=y.user_id AND x.account_name=y.account_name;"""),{'id_user':1})

"""
res=my_session.query(journal_entries.user_id,journal_entries.account_name,journal_entries.debit_amt,journal_entries.credit_amt).filter_by(user_id=1).join(
    accounts,and_(journal_entries.user_id == accounts.user_id,
                  accounts.account_type == 'income statement')
)

statement=select(accounts.user_id,accounts.account_name,accounts.account_subtype).where(and_(accounts.user_id == 1,or_(accounts.account_subtypetwo == 'bank',accounts.account_subtypetwo == 'cash')))
ee=my_session.execute(statement).all()
print(ee)

"""

data=my_session.query(journal_entries.date_of_entry,
                      journal_entries.user_id,journal_entries.account_name,
                      journal_entries.debit_amt,journal_entries.credit_amt).filter_by(user_id=3).all()

dt='2025-01-01-00-00-00'
a=dt.split('-')
#date_ob=date(int(a[0]),int(a[1]),int(a[2]))
for i in range(len(a)):
    a[i]=int(a[i])

"""
fil_entries=[]
for date_entry,user,acc_name,debit,credit in data:
    date_ob=datetime(a[0],a[1],a[2],a[3],a[4],a[5])
    if date_entry > date_ob :
        fil_entries.append({'doe':date_entry,'user_id':user,
                            'acc_name':acc_name,'debit':debit,'credit':credit})
        
for i in fil_entries:
    print(i)
    print("-" * 20)

"""

invoices=my_session.query(inv_sales.id,inv_sales.sales_price,
                          inv_sales.amount_paid,inv_sales.bad_debts_amount,
                          inv_sales.qty,inv_sales.return_qty).filter_by(user_id=3).all()

    