import mysql.connector
from sqlalchemy.orm import sessionmaker,session
from sqlalchemy import create_engine,func,distinct,text,and_
import datetime
from datetime import timedelta
from fastapi import FastAPI,Request,HTTPException,Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from jose import JWTError,jwt
from passlib.context import CryptContext
from practice_two import Users,accounts,journal_entries,inventories,customers,vendors,inv_purchases,inv_sales

app=FastAPI()
SECRET_KEY='secret123'

app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173"]
                   ,allow_methods=["*"],allow_credentials=True,
                   allow_headers=["*"])

pwd_context=CryptContext(schemes=["bcrypt"],deprecated='auto')
oauth2_scheme=OAuth2PasswordBearer(tokenUrl='login')

def get_db():
    dbase=mysql.connector.connect(
    database='react_proj',password='mishaalmalik',
    host='localhost',user='root')

    try:
        yield dbase
    finally:
        dbase.close()

def get_db_two():
      eng=create_engine('mysql+mysqlconnector://root:mishaalmalik@localhost/my_proj_two')
      Sessionlocal=sessionmaker(bind=eng)
      my_session=Sessionlocal()
      try:
            yield my_session
      finally:
            my_session.close()

def hash_password(password:str):
      return pwd_context.hash(password)

def verify_password(plain_password,hashed_password):
      return pwd_context.verify(plain_password,hashed_password)

def issue_token(user_info:dict):
      data=user_info.copy()
      data['exp']=datetime.datetime.now()+timedelta(minutes=30)
      tok=jwt.encode(data,SECRET_KEY,algorithm='HS256')
      return tok

def current_user(req:Request):
      data=req.headers.get('Authorization')
      if data is None:
            raise HTTPException(status_code=400,detail='invalid credentials')
      tok=data.split(" ")[1]
      try:
            get_dict=jwt.decode(tok,SECRET_KEY,algorithms=["HS256"])
            return get_dict["user"]
      except JWTError:
            raise HTTPException(status_code=400,detail='Token got expired')

def current_user_two(tok=Depends(oauth2_scheme)):
      try:
            get_dict=jwt.decode(tok,SECRET_KEY,algorithms=['HS256'])
            return get_dict['user']
      except JWTError:
            raise HTTPException(status_code=401,
                                detail='Expired or invalid credentials')
      
def add_journal_entry(db,debit_acc,credit_acc,amt,cur_user,journal_no=None):
      if journal_no == None:
            journal_no=db.query(func.max(journal_entries.id)).filter_by(user_id=cur_user).scalar()
      db.add(journal_entries(id=journal_no+1,account_name=debit_acc,debit_amt=amt,credit_amt=0,user_id=cur_user))
      db.add(journal_entries(id=journal_no+1,account_name=credit_acc,debit_amt=0,credit_amt=amt,user_id=cur_user))
      return journal_no

@app.get("/main")
def main_page():
    return {"Message":"LEDGER LOOPS"}

@app.post("/adduser")
async def add_user(req:Request,db=Depends(get_db_two)):
      data=await req.json()
      res=db.query(Users).filter_by(user_name=data['username']).first()
      if not res == None:
            raise HTTPException(status_code=400,detail='User already exists')
      hashed_pass=hash_password(data['password'])
      add_user=Users(user_name=data['user_name'],user_pass=hashed_pass)
      db.add(add_user)
      db.commit()
      return {"Message":"ok"}

@app.post("/login")
async def login_user(login_info:Request,db=Depends(get_db_two)):
      data=await login_info.json()
      res=db.query(Users).filter_by(user_name=data['username']).first()
      if res == None:
            raise HTTPException(status_code=400,detail='Enter a valid user id')
      ver=verify_password(data['password'],res.user_pass)
      if not ver:
            raise HTTPException(status_code=400,detail='Enter the correct password')
      tok=issue_token({"user":res.id})
      return {"access_token":tok,"token_type":"bearer"}


@app.get("/login2")
async def login_two(cur_user=Depends(current_user)):
      return {'user_id':cur_user}

@app.post("/login3")
async def login_three(cur_user=Depends(current_user_two)):
      return cur_user

@app.get("/getcustomers")
def return_customers(db=Depends(get_db_two),cur_user=Depends(current_user)):
      res=db.query(customers.customer_name).filter_by(user_id=cur_user).all()
      fil_customers=[]
      for i in res:
            cur_dict={'customer_name':i.customer_name}
            fil_customers.append(cur_dict)
      return fil_customers

@app.get("/getvendors")
def return_vendors(db=Depends(get_db_two),cur_user=Depends(current_user)):
      res=db.query(vendors).filter_by(user_id=cur_user).all()
      vendor_list=[]
      for i in res:
           vendor_list.append({'vendor_name':i.vendor_name})

      return vendor_list

@app.get("/getinventories")
def return_inv(db=Depends(get_db_two),cur_user=Depends(current_user)):
      res=db.query(inventories.inv_name).filter_by(user_id=cur_user).all()
      invs=[]
      for i in res:
            invs.append({'inv_name':i.inv_name})
      return invs

@app.get('/currentassets')
def current_assets(db=Depends(get_db_two),cur_user=Depends(current_user)):
      #cur=db.cursor(dictionary=True)
      #cur.execute("""SELECT * from accounts WHERE 
       #           account_subtype="current assets" AND
        #          user_id={} """.format(cur_user))
      res=db.query(accounts).filter_by(account_subtype='current assets',user_id=cur_user).all()
      ca=[]
      for i in res:
            cur_dict={'account_name':i.account_name,'account_nature':i.account_nature,
             'account_type':i.account_type,'account_subtype':i.account_subtype,
             'account_subtypetwo':i.account_subtypetwo,'amount':i.amount}
            ca.append(cur_dict)

      return ca

@app.get("/invpurchases")
def purchases_inv(db=Depends(get_db_two),cur_user=Depends(current_user)):
     # cur=db.cursor(dictionary=True)
   #   cur.execute("""SELECT user_id,inv_name,SUM(qty) as 'qty' from inv_purchases
    #  GROUP BY user_id,inv_name HAVING SUM(qty) > 0
     #              AND user_id={} """.format(cur_user))
      res=db.query(user_id,inv_name,func.sum(inv_purchases.qty)).filter_by(user_id=cur_user).group_by(inv_purchases.user_id,inv_purchases.inv_name)
      inv_details=[]
      for user_id,inv_name,qty in res:
            inv_details.append({'user_id':user_id,'inv_name':inv_name,'qty':qty})
      return inv_details

@app.get("/allinvoices/")
def all_invoices(db=Depends(get_db_two),invoice_id=None,cur_user=Depends(current_user)):
      #cur=db.cursor(dictionary=True)
      if invoice_id == None:
       #     cur.execute("""SELECT * from inv_sales
        #                WHERE user_id={} """.format(cur_user))
            res=db.query(inv_sales).filter_by(user_id=cur_user).all()
            all_inv=[]
            for i in res:
                  all_inv.append({'id':i.id,'date_of_sale':i.date_of_sale,
                                  'customer_name':i.customer_name,'journal_id':i.journal_id,
                                  'amount_paid':i.amount_paid,'cur_status':i.cur_status,
                                  'inv_name':i.inv_name,'qty':i.qty,'sales_price':i.sales_price,
                                  'cost_of_goods_sold':i.cost_of_goods_sold,'bad_debts_amount':i.bad_debts_amount,
                                  'return_qty':i.return_qty,'user_id':i.user_id})
            return all_inv
      else:
            #cur.execute("""SELECT * from inv_sales WHERE 
              #    id={} AND user_id={} """.format(invoice_id,cur_user))
            res=db.query(inv_sales).filter_by(user_id=cur_user,id=invoice_id).first()
            return [{'id':res.id,'date_of_sale':res.date_of_sale,
                                  'customer_name':res.customer_name,'journal_id':res.journal_id,
                                  'amount_paid':res.amount_paid,'cur_status':res.cur_status,
                                  'inv_name':res.inv_name,'qty':res.qty,'sales_price':res.sales_price,
                                  'cost_of_goods_sold':res.cost_of_goods_sold,'bad_debts_amount':res.bad_debts_amount,
                                  'return_qty':res.return_qty,'user_id':res.user_id}]
      

@app.post("/addcustomer")
async def add_customer(req:Request,db=Depends(get_db_two),cur_user=Depends(current_user)):
      data=await req.json()
     # cur=db.cursor(dictionary=True)
      #cur.execute("""INSERT INTO customers(customer_name,gmail,user_id)
              #    VALUES("{}","{}","{}")""".format(data['customername'],data['gmail'],cur_user))
      #cur.execute("""SELECT account_name from accounts WHERE user_id={} """.format(cur_user))
      #av_customers=cur.fetchall()
      custs=db.query(customers).filter_by(user_id=cur_user).all()
      for i in custs:
            if i.customer_name == data['customername']:
                  raise HTTPException(status_code=400,detail='user exists')
      
      cust=customers(customer_name=data['customername'],gmail=data['gmail'],user_id=cur_user)
      db.add(cust)
      acc=accounts(account_name=data['customername'],account_nature='debit',account_type='assets',account_subtype='current assets',account_subtypetwo='accounts receivable',amount=0,
                         user_id=cur_user)
      db.add(acc)
      db.commit()
      return {'Message':'Added a customer'}

@app.post("/addvendor")
async def add_vendor(req:Request,db=Depends(get_db_two),cur_user=Depends(current_user)):
      data=await req.json()
     # cur=db.cursor(dictionary=True)
      #cur.execute("""INSERT INTO vendors(vendor_name,gmail,user_id)
       #           VALUES("{}","{}","{}")""".format(data['vendorname'],data['gmail'],cur_user))
      #cur.execute("""SELECT account_name from accounts 
       #           WHERE user_id={} """.format(cur_user))
      a_vendors=db.query(vendors).filter_by(user_id=cur_user).all()
      for i in a_vendors:
            if i.vendor_name == data['vendorname']:
                  raise HTTPException(status_code=400,detail='vendor exists')
      vendor=vendors(vendor_name=data['vendorname'],gmail=data['gmail'],user_id=cur_user)
      acc_name=accounts(account_name=data['vendorname'],account_nature='credit',account_type='liabilities',account_subtype='current liabilities',
               account_subtypetwo='accounts payable',amount=0,user_id=cur_user)
      db.add(acc_name)
      db.add(vendor)
      db.commit()
      return {'Message':'Added a vendor'}


@app.post("/addinventory")
async def add_inventory(req:Request,db=Depends(get_db_two),cur_user=Depends(current_user)):
      data=await req.json()
      res=db.query(inventories).filter_by(user_id=cur_user).all()
      for i in res:
            if i.inv_name == data['inv_name']:
                  raise HTTPException(status_code=400,detail='inv exists')
     
      res=db.query(accounts).filter_by(user_id=cur_user).all()
      av_accs=[i.account_name for i in res]
      if data['ledger_name'] in av_accs:
            raise HTTPException(status_code=400,detail='ledger name exists')
      if data['ledger_name'] == 'na':
            acc_name=accounts(account_name=data['inv_name'],account_nature="debit",account_type="assets",
                     account_subtype="current assets",account_subtypetwo="inventories",amount=0,
                     user_id=cur_user)
            inv=inventories(inv_name=data['inv_name'],account_name=data['inv_name'],user_id=cur_user)
            db.add(acc_name)
            db.add(inv)
      else:
             db.add(accounts(account_name=data['ledger_name'],account_nature="debit",account_type="assets",
                      account_subtype="current assets",account_subtypetwo="inventories",amount=0,
                      user_id=cur_user))
             db.add(inventories(inv_name=data['inv_name'],account_name=data['ledger_name'],user_id=cur_user))
      db.commit()
      return {'Message':'Added'}

@app.post('/purchaseinv')
async def purchase_inv(req:Request,db=Depends(get_db_two),cur_user=Depends(current_user)):
      data=await req.json()
      p=inv_purchases()
      p.user_id=cur_user
      p.inv_name=data['inv_name']
      p.qty=data['qty']
      p.price=data['price']
      db.add(p)
      acc_name=db.query(inventories).filter_by(user_id=cur_user,inv_name=data['inv_name']).first()
      amount=int(data['qty']) * int(data['price'])
      add_journal_entry(db,acc_name.account_name,data['vendor_name'],amount,cur_user)
      db.commit()
      return {'Message':'Successfull'}

@app.post('/addinvoice')
async def add_invoice(req:Request,db=Depends(get_db_two),cur_user=Depends(current_user)):
      data=await req.json()
      res=db.query(inv_purchases).filter_by(user_id=cur_user,inv_name=data['inv_name']).all()
     # cur=db.cursor(dictionary=True)
      #cur.execute("""SELECT * from inv_purchases
       #           WHERE inv_name="{}" AND user_id={} """.format(data['inv_name'],cur_user)) 
      #res=cur.fetchall()
      res=db.query(inv_purchases).filter_by(user_id=cur_user,inv_name=data['inv_name']).all()
      for_sale=int(data['quantity'])

      ids=[i.id for i in res]
      qty=[i.qty for i in res]
      prices=[i.price for i in res] 
      cum_qty=[]
      cum_prices=[]
      cum=0

      for i in qty:
            cum=cum+i
            cum_qty.append(cum)
      cum=0
      for i in prices:
            cum=cum+i
            cum_prices.append(cum)

      for i in range(len(cum_qty)):
                  if cum_qty[i] >= for_sale:
                        if i == 0:
                              total_price=for_sale * prices[i]
                              av_inv=cum_qty[i]-for_sale
                        else:
                              till_price=cum_qty[i-1] * cum_prices[i-1]
                              rem_qty=for_sale-cum_qty[i-1]
                              rem=rem_qty * prices[i]
                              total_price=till_price + rem
                              av_inv=cum_qty[i] - for_sale
                              for j in range(i):
                                   # cur.execute("""DELETE FROM inv_purchases
                                   to_del=db.query(inv_purchases).filter_by(id=ids[j],user_id=cur_user).first()
                                   db.delete(to_del)
                                    #        WHERE id={} AND user_id={} """.format(ids[j],cur_user))
                        if av_inv == 0:
                              #cur.execute("""DELETE from inv_purchases
                               to_del=db.query(inv_purchases).filter_by(user_id=cur_user,id=ids[i])
                               db.delete(to_del)
                               #           WHERE id={} AND user_id={} """.format(ids[i],cur_user))
                        else:
                              to_update=db.query(inv_purchases).filter_by(user_id=cur_user,id=ids[i]).first()
                              to_update.qty=av_inv
                              #cur.execute("""UPDATE inv_purchases
                               #           SET qty={} WHERE id={} AND user_id={} """.format(av_inv,ids[i],cur_user))
                        ##sales journal
                        a=add_journal_entry(db,data['customer_name'],'sales',data['selling_price'],cur_user)
                        ##cost of goods sold journal 
                        #cur.execute("""SELECT account_name from inventories WHERE 
                        #            inv_name="{}" AND user_id={}""".format(data['inv_name'],cur_user))
                        inv=db.query(inventories.account_name).filter_by(user_id=cur_user,inv_name=data['inv_name']).scalar()
                        add_journal_entry(db,"COGS",inv,total_price,cur_user,journal_no=a)
                        if data['typeOfSale'] == 'cash' or data['typeOfSale'] == 'bank':
                              paid_status='paid'
                              amt=data['selling_price']
                        else:
                              paid_status='not paid'
                              amt=0
                              sale_info=inv_sales(customer_name=data['customer_name'],
                                    journal_id=a,amount_paid=amt,cur_status=paid_status,
                                    inv_name=data['inv_name'],qty=data['quantity'],sales_price=data['selling_price'],
                                    cost_of_goods_sold=total_price,bad_debts_amount=0,return_qty=0,
                                    user_id=cur_user)
                              db.add(sale_info)
                       # cur.execute("""INSERT INTO inv_sales(customer_name,journal_id,
                       #             amount_paid,cur_status,inv_name,qty
                       #             ,sales_price,cost_of_goods_sold,user_id)
                        #            VALUES("{}",{},{},"{}","{}",{},{},{},{})""".format(
                         #                 data['customer_name'],a,amt,paid_status,data['inv_name']
                          #                ,data['quantity'],data['selling_price'],total_price,cur_user
                           #         ))
                        db.commit()
                        return {'message':'success','cogs':total_price}
                  
@app.post("/return_inv")
async def return_inventory(req:Request,db=Depends(get_db_two),inv_id=None,cur_user=Depends(current_user)):
      if inv_id == None:
            raise HTTPException(status_code=400,detail='Provide inv id')
      data=await req.json()
      #cur=db.cursor(dictionary=True)
      #cur.execute("""SELECT * from inv_sales 
       #           WHERE id={} AND user_id={}""".format(inv_id,cur_user))
      res=db.query(inv_sales).filter_by(user_id=cur_user,id=inv_id).first()
      #if len(res) == 0:
       #     raise HTTPException(status_code=400,detail='Invalid inv id')
      #inv_details=res[0]
      #cur.execute("""UPDATE inv_sales 
       #           SET return_qty=return_qty + {}
      #          WHERE id={} AND user_id={}""".format(data['return_qty'],inv_id,cur_user))
      if res == None:
            raise HTTPException(status_code=400,detail='inv_id does not exists')
      
      r=int(res.return_qty)
      r=r + int(data['return_qty'])
      res.return_qty=r

      c_p=(res.cost_of_goods_sold / res.qty) * int(data['return_qty'])
      s_p=(res.sales_price / res.qty) * int(data['return_qty'])
      acc_name=db.query(inventories.account_name).filter_by(user_id=cur_user,id=inv_id).scalar()
      j_n=add_journal_entry(db,acc_name,'COGS',c_p,cur_user)
      add_journal_entry(db,'sales return',res.customer_name,s_p,cur_user,journal_no=j_n)
      #cur.execute("""INSERT INTO inv_purchases(inv_name,qty,purchase_price,user_id)
       #          VALUES("{}",{},{},{})""".format(inv_details['inv_name'],data['return_qty'],
        #                                 c_p,cur_user))
      #db.add(inv_purchases(user_id=cur_user,inv_name=res.inv_name,qty=data['return_qty'],
       #             price=c_p))
      ret_data=inv_purchases()
      ret_data.user_id=cur_user
      ret_data.inv_name=res.inv_name
      ret_data.qty=data['return_qty']
      ret_data.price=c_p
      db.add(ret_data)
      db.commit()
      return {'Message':'sucessfull'}

@app.post("/baddebts/")
async def bad_debts(req:Request,db=Depends(get_db_two),invoice_id=None,cur_user=Depends(current_user)):
      if invoice_id == None:
            raise HTTPException(status_code=400,details='Provide an invoice id'
                                )
      data=await req.json()
      res=db.query(inv_sales).filter_by(user_id=cur_user,id=invoice_id).first()
      if res == None:
            raise HTTPException(status_code=400,detail='Enter a existing invoice')
      res.bad_debts_amount += int(data['bad_debts'])
      add_journal_entry(db,'bad debts',res.customer_name,data['bad_debts'],cur_user)
      db.commit()
      return {'Message':'Successfully added bad debts'}

@app.post("/createaccount")
async def create_account(req:Request,db=Depends(get_db_two),cur_user=Depends(current_user)):
    data=await req.json()
    res=db.query(accounts.account_name).filter_by(user_id=cur_user,account_name=data['accountname']).scalar()
    if res != None:
        raise HTTPException(status_code=400,detail='Account already exists')
    db.add(accounts(account_name=data['accountname'],account_nature=data['accountnature'],
             account_type=data['accounttype'],account_subtype=data['accountsubtype'],
             account_subtypetwo=data['accountsubtypetwo'],user_id=cur_user))
    db.commit()
    return {"Message":"Added account"}

@app.get('/viewledgers')
def view_ledgers(db=Depends(get_db_two),cur_user=Depends(current_user)):
    a=db.query(accounts).filter_by(user_id=cur_user).all()
    accounts=[i.account_name for i in a]
    return accounts

@app.get("/viewbalances")
def view_balances(db=Depends(get_db_two),cur_user=Depends(current_user)):
    res=db.execute(text("""SELECT * from (
      SELECT user_id,account_name,SUM(debit_amt-credit_amt) as 'balance' from journal_entries
      GROUP BY user_id,account_name)x
      WHERE user_id=:id_user"""),{'id_user':cur_user})
    results=[]
    for i in res:
          results.append({'user_id':i.user_id,'account_name':i.account_name,
                      'balance':i.balance})
    return results

@app.post('/singlejournal')
async def add_journal_single(req:Request,db=Depends(get_db_two),typ=None,cur_user=Depends(current_user)):
    data=await req.json()
    add_journal_entry(db,data['payment_account'],data['customer_name'],data['amount_paid'],cur_user)
    #cur=db.cursor(dictionary=True)
    if typ == 'inventory':
          #cur.execute("""UPDATE inv_sales SET 
           #           amount_paid=amount_paid + {} 
            #          WHERE id={} AND user_id={} """.format(data['amount_paid'],data['inv_id'],cur_user))
          #cur.execute("""SELECT id,amount_paid,sales_price from inv_sales
           #           WHERE id={} AND user_id={} """.format(data['inv_id'],cur_user))
          a=db.query(inv_sales).filter_by(user_id=cur_user,id=data['inv_id']).first()
          a.amount_paid += data['amount_paid']
          
          if a.amount_paid == a.sales_price:
                a.cur_status='paid'
                db.update(a)
                #cur.execute("""UPDATE inv_sales SET
                 #           cur_status="paid" WHERE id={} AND user_id={} """.format(data['inv_id'],cur_user))
    db.commit()
    return {'Message':'Successfully added the journal entry'}

@app.get('/viewjournals')
def view_journals(db=Depends(get_db_two),cur_user=Depends(current_user)):
    #cursor=db.cursor(dictionary=True)
    j_e=db.execute(text("""SELECT * from (
      SELECT a.user_id,a.id,a.date_of_entry,a.account_name as 'debited',a.debit_amt as 'debit_amt',
      b.account_name as 'credited',b.credit_amt as 'credit_amt'
      from journal_entries a,journal_entries b
      WHERE a.id=b.id and a.debit_amt=b.credit_amt AND a.debit_amt != 0 AND a.user_id=b.user_id
      ORDER BY a.id)x
      WHERE user_id = :id_user """),{'id_user':cur_user})
    ret_accs=[]
    for i in j_e:
          ret_accs.append({
        'id':i.id,'date_of_entry':i.date_of_entry,'debited':i.debited,
        'debit_amt':i.debit_amt,'credited':i.credited,'credit_amt':i.credit_amt})
    return ret_accs

@app.get("/balancesheet")
def return_balance_sheet(db=Depends(get_db_two),cur_user=Depends(current_user)):
    res=db.execute(text("""SELECT accounts.user_id,accounts.account_name,account_nature,account_type,
      account_subtype,account_subtypetwo,IFNULL(balance,0) as 'balance' from accounts LEFT JOIN (
      SELECT user_id,account_name,SUM(debit_amt-credit_amt) as 'balance' from
      journal_entries GROUP BY user_id,account_name HAVING user_id=:id_user)x
      ON accounts.user_id=x.user_id AND accounts.account_name=x.account_name;
      """),{'id_user':cur_user})
    accs=[]
    for i in res:
          accs.append({'user_id':i.user_id,'account_name':i.account_name,
                       'account_nature':i.account_nature,
                       'account_type':i.account_type,'account_subtype':i.account_subtype,
                       'account_subtypetwo':i.account_subtypetwo,'balance':i.balance})
    return accs

@app.get("/balancesheet_two")
def al_balance_sheet(db=Depends(get_db_two),cur_user=Depends(current_user)):
    res=db.execute(text("""SELECT accounts.user_id,accounts.account_name,account_nature,account_type,
      account_subtype,account_subtypetwo,IFNULL(balance,0) as 'balance' from accounts LEFT JOIN (
      SELECT user_id,account_name,SUM(debit_amt-credit_amt) as 'balance' from
      journal_entries GROUP BY user_id,account_name HAVING user_id=:id_user)x
      ON accounts.user_id=x.user_id AND accounts.account_name=x.account_name;
      """),{'id_user':cur_user})
    all_results=[]
    for i in res:
          all_results.append({'user_id':i.user_id,'account_name':i.account_name,
                       'account_nature':i.account_nature,
                       'account_type':i.account_type,'account_subtype':i.account_subtype,
                       'account_subtypetwo':i.account_subtypetwo,'balance':i.balance})
    bs={}
    for i in ["assets","liabilities","income statement"]:
                bs[i]={}
                for j in all_results:
                        if i == j['account_type'] and j['account_subtype'] not in bs[i]:
                            new_key=j['account_subtype']
                            bs[i][new_key]={}
            
    for i in bs:
        for j in bs[i]:
                for z in all_results:
                        if z['account_subtype'] == j and z['account_subtype'] not in bs[i][j]:
                                bs[i][j][z['account_subtypetwo']]={}   

    for i in bs:
        for j in bs[i]:
                for z in bs[i][j]:
                        for acc in all_results:
                                if acc['account_type'] == i and acc['account_subtype']== j and acc['account_subtypetwo'] == z:
                                    bs[i][j][z][acc['account_name']]=acc['balance']
    return bs


@app.post("/closingprocess")
async def close_income_expense_accounts(request:Request,db=Depends(get_db_two),
                                  cur_user=Depends(current_user_two)):
               
      bal_two=db.query(journal_entries.account_name,func.sum(journal_entries.debit_amt),
                              func.sum(journal_entries.credit_amt)).join(accounts,
                                                and_(journal_entries.account_name == accounts.account_name,
                                                      accounts.account_type == 'income statement')).group_by(journal_entries.account_name)
      to_close={'expenses':{},'incomes':{},'bal':0}

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

      print(to_close)

      journal_id=db.query(func.max(journal_entries.id)).scalar()
      print(journal_id)
      print(type(journal_id))

      #closing process
      for i in to_close['expenses']:
            acc_val=to_close['expenses'][i]
            entry=journal_entries(id=journal_id+1,account_name=i,debit_amt=0,credit_amt=acc_val)
            db.add(entry)

      for i in to_close['incomes']:
            acc_value=to_close['incomes'][i] * -1
            entry=journal_entries(id=journal_id+1,account_name=i,debit_amt=acc_value,credit_amt=0)
            db.add(entry)

      if to_close['bal'] > 0:
            entry=journal_entries(id=journal_id+1,account_name='p_l_balance',debit_amt=to_close['bal'])
            db.add(entry)
      else:
            entry=journal_entries(id=journal_id+1,account_name='p_l_balance',debit_amt=0,credit_amt=to_close['bal']*-1)
            db.add(entry)

      last_query=db.query(journal_entries.account_name,journal_entries.debit_amt,journal_entries.credit_amt).filter_by(account_name='p_l_balance').all()

      for name,debit,credit in last_query:
            print(name,debit,credit)

