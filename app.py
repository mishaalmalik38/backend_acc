import mysql.connector
import datetime
from datetime import timedelta
from fastapi import FastAPI,Request,HTTPException,Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from jose import JWTError,jwt
from passlib.context import CryptContext

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
      cur=db.cursor(dictionary=True)
      if journal_no == None:
            cur.execute("""SELECT COUNT(DISTINCT(id))+ 1 as 'cnt'
                         from journal_entries WHERE user_id={} """.format(cur_user))
            res=cur.fetchall()
            journal_no=res[0]['cnt']
      cur.execute("""INSERT INTO journal_entries(id,account_name,debit_amt,credit_amt,user_id)
                  VALUES({},"{}",{},{},{})""".format(journal_no,debit_acc,amt,0,cur_user))
      cur.execute("""INSERT INTO journal_entries(id,account_name,debit_amt,credit_amt,user_id)
                  VALUES({},"{}",{},{},{})""".format(journal_no,credit_acc,0,amt,cur_user))
      return journal_no

@app.get("/main")
def main_page():
    return {"Message":"LEDGER LOOPS"}

@app.post("/adduser")
async def add_user(req:Request,db=Depends(get_db)):
      data=await req.json()
      cur=db.cursor(dictionary=True)
      cur.execute("""SELECT * from main_users 
                  WHERE user_name="{}" """.format(data['username']))
      res=cur.fetchall()
      if len(res) == 1:
            raise HTTPException(status_code=400,detail='User already exists')
      hashed_pass=hash_password(data['password'])
      cur.execute("""INSERT INTO main_users(user_name,user_pass,main_name)
                  VALUES("{}","{}","{}") """.format(data['username'],hashed_pass,data['name']))
      db.commit()
      return {"Message":"ok"}

@app.post("/login")
def login_user(login_info:OAuth2PasswordRequestForm=Depends(),db=Depends(get_db)):
      cur=db.cursor(dictionary=True)
      cur.execute("""SELECT id,user_name,user_pass from main_users
                  WHERE user_name="{}" """.format(login_info.username))
      res=cur.fetchall()
      if len(res) == 0:
            raise HTTPException(status_code=400,detail='Enter a valid user id')
      ver=verify_password(login_info.password,res[0]['user_pass'])
      if not ver:
            raise HTTPException(status_code=400,detail='Enter the correct password')
      tok=issue_token({"user":res[0]['id']})
      return {"access_token":tok,"token_type":"bearer"}


@app.get("/login2")
async def login_two(cur_user=Depends(current_user)):
      return {'user_id':cur_user}

@app.post("/login3")
async def login_three(cur_user=Depends(current_user_two)):
      return cur_user

@app.get("/getcustomers")
def return_customers(db=Depends(get_db),cur_user=Depends(current_user)):
      cur=db.cursor(dictionary=True)
      cur.execute("""SELECT customer_name from customers
                  WHERE user_id={} """.format(cur_user))
      res=cur.fetchall()
      return res

@app.get("/getvendors")
def return_vendors(db=Depends(get_db),cur_user=Depends(current_user)):
      cur=db.cursor(dictionary=True)
      cur.execute("""SELECT vendor_name from vendors 
                  WHERE user_id={} """.format(cur_user))
      res=cur.fetchall()
      return res

@app.get("/getinventories")
def return_inv(db=Depends(get_db),cur_user=Depends(current_user)):
      cur=db.cursor(dictionary=True)
      cur.execute("""SELECT inv_name from inventories
                  WHERE user_id={} """.format(cur_user))
      res=cur.fetchall()
      return res

@app.get('/currentassets')
def current_assets(db=Depends(get_db),cur_user=Depends(current_user)):
      cur=db.cursor(dictionary=True)
      cur.execute("""SELECT * from accounts WHERE 
                  account_subtype="current assets" AND
                  user_id={} """.format(cur_user))
      res=cur.fetchall()
      return res

@app.get("/invpurchases")
def inv_purchases(db=Depends(get_db),cur_user=Depends(current_user)):
      cur=db.cursor(dictionary=True)
      cur.execute("""SELECT user_id,inv_name,SUM(qty) as 'qty' from inv_purchases
      GROUP BY user_id,inv_name HAVING SUM(qty) > 0
                   AND user_id={} """.format(cur_user))
      res=cur.fetchall()
      return res

@app.get("/allinvoices/")
def all_invoices(db=Depends(get_db),invoice_id=None,cur_user=Depends(current_user)):
      cur=db.cursor(dictionary=True)
      if invoice_id == None:
            cur.execute("""SELECT * from inv_sales
                        WHERE user_id={} """.format(cur_user))
      else:
            cur.execute("""SELECT * from inv_sales WHERE 
                  id={} AND user_id={} """.format(invoice_id,cur_user))
      res=cur.fetchall()
      return res
      

@app.post("/addcustomer")
async def add_customer(req:Request,db=Depends(get_db),cur_user=Depends(current_user)):
      data=await req.json()
      cur=db.cursor(dictionary=True)
      cur.execute("""INSERT INTO customers(customer_name,gmail,user_id)
                  VALUES("{}","{}","{}")""".format(data['customername'],data['gmail'],cur_user))
      cur.execute("""SELECT account_name from accounts WHERE user_id={} """.format(cur_user))
      av_customers=cur.fetchall()
      av_c_f=[i['account_name'] for i in av_customers]
      if not data['customername'] in av_c_f:
            cur.execute("""INSERT INTO accounts
                        (account_name,account_nature,
                        account_type,account_subtype
                        ,account_subtypetwo,amount,user_id)
                        VALUES("{}","debit","assets","current assets","accounts receivable",0,"{}")
                        """.format(data['customername'],cur_user))  
      db.commit()
      return {'Message':'Added a customer'}

@app.post("/addvendor")
async def add_vendor(req:Request,db=Depends(get_db),cur_user=Depends(current_user)):
      data=await req.json()
      cur=db.cursor(dictionary=True)
      cur.execute("""INSERT INTO vendors(vendor_name,gmail,user_id)
                  VALUES("{}","{}","{}")""".format(data['vendorname'],data['gmail'],cur_user))
      cur.execute("""SELECT account_name from accounts 
                  WHERE user_id={} """.format(cur_user))
      av_suppliers=cur.fetchall()
      av_s_f=[i['account_name'] for i in av_suppliers]
      if not data['vendorname'] in av_s_f:
            cur.execute("""INSERT INTO accounts
                        (account_name,account_nature,
                        account_type,account_subtype
                        ,account_subtypetwo,amount,user_id)
                        VALUES("{}","credit","liabilities","current liabilities","accounts payable",0,"{}")
                        """.format(data['vendorname'],cur_user))  
      db.commit()
      return {'Message':'Added a vendor'}


@app.post("/addinventory")
async def add_inventory(req:Request,db=Depends(get_db),cur_user=Depends(current_user)):
      data=await req.json()
      cur=db.cursor(dictionary=True)
      cur.execute("""SELECT inv_name from inventories WHERE 
                  user_id={} """.format(cur_user))
      res=cur.fetchall()
      av_invs=[i['inv_name'] for i in res]
      if data['inv_name'] in av_invs:
            return {'message':'inv'}
      cur.execute("""SELECT account_name from accounts
                  WHERE user_id={} """.format(cur_user))
      res=cur.fetchall()
      av_accs=[i['account_name'] for i in res]
      if data['ledger_name'] in av_accs:
            return {'message':'acc'}
      if data['ledger_name'] == 'na':
            cur.execute("""INSERT INTO accounts
                        (account_name,account_nature,account_type,account_subtype,account_subtypetwo,amount,user_id)
                        VALUES("{}","debit","assets","current assets","inventories",0,"{}")""".format(data['inv_name'],cur_user))
            cur.execute("""INSERT INTO inventories(inv_name,account_name,user_id)
                        VALUES("{}","{}","{}")""".format(data['inv_name'],data['inv_name'],cur_user))
      else:
             cur.execute("""INSERT INTO accounts
                        (account_name,account_nature,account_type,account_subtype,account_subtypetwo,amount,user_id)
                        VALUES("{}","debit","assets","current assets","inventories",0,"{}")""".format(data['ledger_name'],cur_user))
             cur.execute("""INSERT INTO inventories(inv_name,account_name,user_id)
                         VALUES("{}","{}")""".format(data['inv_name'],data['ledger_name'],cur_user))
      db.commit()
      return {'Message':'Added'}

@app.post('/purchaseinv')
async def purchase_inv(req:Request,db=Depends(get_db),cur_user=Depends(current_user)):
      data=await req.json()
      cur=db.cursor(dictionary=True)
      cur.execute("""SELECT COUNT(DISTINCT(id)) + 1 as 'cnt' from journal_entries
      WHERE user_id={} """.format(cur_user))
      res=cur.fetchall()
      cur.execute("""INSERT INTO inv_purchases(inv_name,qty,purchase_price,user_id)
                  VALUES("{}",{},{},{})""".format(data['inv_name'],data['qty'],data['price'],cur_user))
      cur.execute("""SELECT account_name from inventories 
                  WHERE inv_name="{}" """.format(data['inv_name']))
      res_two=cur.fetchall()
      cur.execute("""INSERT INTO journal_entries(id,account_name,debit_amt,credit_amt,user_id)
                  VALUES({},"{}",{},{},{})""".format(res[0]['cnt'],res_two[0]['account_name'],int(data['price'])*int(data['qty']),0,cur_user))
      cur.execute("""INSERT INTO journal_entries(id,account_name,debit_amt,credit_amt,user_id)
                  VALUES({},"{}",{},{},{})""".format(res[0]['cnt'],data['vendor_name'],0,int(data['price'])*int(data['qty']),cur_user))
      db.commit()
      return {'Message':'Successfull'}

@app.post('/addinvoice')
async def add_invoice(req:Request,db=Depends(get_db),cur_user=Depends(current_user)):
      data=await req.json()
      cur=db.cursor(dictionary=True)
      cur.execute("""SELECT * from inv_purchases
                  WHERE inv_name="{}" AND user_id={} """.format(data['inv_name'],cur_user)) 
      res=cur.fetchall()
      for_sale=int(data['quantity'])

      ids=[i['id'] for i in res]
      qty=[i['qty'] for i in res]
      prices=[i['purchase_price'] for i in res] 
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
                                    cur.execute("""DELETE FROM inv_purchases
                                            WHERE id={} AND user_id={} """.format(ids[j],cur_user))
                        if av_inv == 0:
                              cur.execute("""DELETE from inv_purchases
                                          WHERE id={} AND user_id={} """.format(ids[i],cur_user))
                        else:
                              cur.execute("""UPDATE inv_purchases
                                          SET qty={} WHERE id={} AND user_id={} """.format(av_inv,ids[i],cur_user))
                        ##sales journal
                        a=add_journal_entry(db,data['customer_name'],'sales',data['selling_price'],cur_user)
                        ##cost of goods sold journal 
                        cur.execute("""SELECT account_name from inventories WHERE 
                                    inv_name="{}" AND user_id={}""".format(data['inv_name'],cur_user))
                        res=cur.fetchall()
                        add_journal_entry(db,"COGS",res[0]['account_name'],total_price,cur_user,journal_no=a)
                        if data['typeOfSale'] == 'cash' or data['typeOfSale'] == 'bank':
                              paid_status='paid'
                              amt=data['selling_price']
                        else:
                              paid_status='not paid'
                              amt=0
                        cur.execute("""INSERT INTO inv_sales(customer_name,journal_id,
                                    amount_paid,cur_status,inv_name,qty
                                    ,sales_price,cost_of_goods_sold,user_id)
                                    VALUES("{}",{},{},"{}","{}",{},{},{},{})""".format(
                                          data['customer_name'],a,amt,paid_status,data['inv_name']
                                          ,data['quantity'],data['selling_price'],total_price,cur_user
                                    ))
                        db.commit()
                        return {'message':'success','cogs':total_price}
                  
@app.post("/return_inv")
async def return_inventory(req:Request,db=Depends(get_db),inv_id=None,cur_user=Depends(current_user)):
      if inv_id == None:
            raise HTTPException(status_code=400,detail='Provide inv id')
      data=await req.json()
      cur=db.cursor(dictionary=True)
      cur.execute("""SELECT * from inv_sales 
                  WHERE id={} AND user_id={}""".format(inv_id,cur_user))
      res=cur.fetchall()
      if len(res) == 0:
            raise HTTPException(status_code=400,detail='Invalid inv id')
      inv_details=res[0]
      cur.execute("""UPDATE inv_sales 
                  SET return_qty=return_qty + {}
                  WHERE id={} AND user_id={}""".format(data['return_qty'],inv_id,cur_user))
      c_p=(inv_details['cost_of_goods_sold'] / inv_details['qty']) * int(data['return_qty'])
      s_p=(inv_details['sales_price'] / inv_details['qty']) * int(data['return_qty'])
      j_n=add_journal_entry(db,inv_details['inv_name'],'COGS',c_p,cur_user)
      add_journal_entry(db,'sales return',inv_details['customer_name'],s_p,cur_user,journal_no=j_n)
      cur.execute("""INSERT INTO inv_purchases(inv_name,qty,purchase_price,user_id)
                  VALUES("{}",{},{},{})""".format(inv_details['inv_name'],data['return_qty'],
                                         c_p,cur_user))
      db.commit()
      return {'Message':'sucessfull'}

@app.post("/baddebts/")
async def bad_debts(req:Request,db=Depends(get_db),invoice_id=None,cur_user=Depends(current_user)):
      if invoice_id == None:
            raise HTTPException(status_code=400,details='Provide an invoice id'
                                )
      data=await req.json()
      cur=db.cursor(dictionary=True)
      cur.execute("""SELECT * from inv_sales 
                  WHERE id={} AND user_id={} """.format(invoice_id,cur_user))
      res=cur.fetchall()
      if len(res) == 0:
            raise HTTPException(status_code=400,detail='Enter a existing invoice')
      inv_details=res[0]
      cur.execute("""UPDATE inv_sales 
                  SET bad_debts_amount=bad_debts_amount + {} 
                  WHERE id={} AND user_id={} """.format(data['bad_debts'],invoice_id,cur_user))
      add_journal_entry(db,'bad debts',inv_details['customer_name'],data['bad_debts'],cur_user)
      db.commit()
      return {'Message':'Successfully added bad debts'}

@app.post("/createaccount")
async def create_account(req:Request,db=Depends(get_db),cur_user=Depends(current_user)):
    data=await req.json()
    cursor=db.cursor(dictionary=True)
    cursor.execute("""SELECT * from accounts
                   WHERE account_name="{}" AND user_id={} """.format(data['accountname'],cur_user))
    res=cursor.fetchall()
    if not len(res) == 0:
        raise HTTPException(status_code=400,detail='Account already exists')
    cursor.execute(
        """INSERT INTO accounts(account_name,account_nature,account_type,account_subtype,account_subtypetwo,amount,user_id)
        VALUES("{}","{}","{}","{}","{}",0,"{}")""".format(data['accountname'],
                                                     data['accountnature'],data['accounttype'],data['accountsubtype'],data['accountsubtypetwo'],cur_user)
    )
    db.commit()
    return {"Message":"Added account"}

@app.get('/viewledgers')
def view_ledgers(db=Depends(get_db),cur_user=Depends(current_user)):
    cursor=db.cursor(dictionary=True)
    cursor.execute("""SELECT account_name from accounts
                   WHERE user_id={} """.format(cur_user))
    res=cursor.fetchall()
    return res

@app.get("/viewbalances")
def view_balances(db=Depends(get_db),cur_user=Depends(current_user)):
    cursor=db.cursor(dictionary=True)
    cursor.execute("""SELECT * from (
      SELECT user_id,account_name,SUM(debit_amt-credit_amt) as 'balance' from journal_entries
      GROUP BY user_id,account_name)x
      WHERE user_id={} """.format(cur_user))
    results=cursor.fetchall()
    return results

@app.post('/singlejournal')
async def add_journal_single(req:Request,db=Depends(get_db),typ=None,cur_user=Depends(current_user)):
    data=await req.json()
    add_journal_entry(db,data['payment_account'],data['customer_name'],data['amount_paid'],cur_user)
    cur=db.cursor(dictionary=True)
    if typ == 'inventory':
          cur.execute("""UPDATE inv_sales SET 
                      amount_paid=amount_paid + {} 
                      WHERE id={} AND user_id={} """.format(data['amount_paid'],data['inv_id'],cur_user))
          cur.execute("""SELECT id,amount_paid,sales_price from inv_sales
                      WHERE id={} AND user_id={} """.format(data['inv_id'],cur_user))
          res=cur.fetchall()
          if res[0]['amount_paid'] == res[0]['sales_price']:
                cur.execute("""UPDATE inv_sales SET
                            cur_status="paid" WHERE id={} AND user_id={} """.format(data['inv_id'],cur_user))
    db.commit()
    return {'Message':'Successfully added the journal entry'}

@app.get('/viewjournals')
def view_journals(db=Depends(get_db),cur_user=Depends(current_user)):
    cursor=db.cursor(dictionary=True)
    cursor.execute("""SELECT * from (
      SELECT a.user_id,a.id,a.date_of_entry,a.account_name as 'debited',a.debit_amt as 'debit_amt',
      b.account_name as 'credited',b.credit_amt as 'credit_amt'
      from journal_entries a,journal_entries b
      WHERE a.id=b.id and a.debit_amt=b.credit_amt AND a.debit_amt != 0 AND a.user_id=b.user_id
      ORDER BY a.id)x
      WHERE user_id={} """.format(cur_user))
    result=cursor.fetchall()
    return result

@app.get("/balancesheet")
def return_balance_sheet(db=Depends(get_db),cur_user=Depends(current_user)):
    cursor=db.cursor(dictionary=True)
    cursor.execute("""SELECT accounts.user_id,accounts.account_name,account_nature,account_type,
      account_subtype,account_subtypetwo,IFNULL(balance,0) as 'balance' from accounts LEFT JOIN (
      SELECT user_id,account_name,SUM(debit_amt-credit_amt) as 'balance' from
      journal_entries GROUP BY user_id,account_name HAVING user_id={})x
      ON accounts.user_id=x.user_id AND accounts.account_name=x.account_name;
      """.format(cur_user))
    all_results=cursor.fetchall()
    return all_results
    
@app.get("/balancesheet_two")
def al_balance_sheet(db=Depends(get_db),cur_user=Depends(current_user)):
    cursor=db.cursor(dictionary=True)
    cursor.execute("""SELECT accounts.user_id,accounts.account_name,account_nature,account_type,
      account_subtype,account_subtypetwo,IFNULL(balance,0) as 'balance' from accounts LEFT JOIN (
      SELECT user_id,account_name,SUM(debit_amt-credit_amt) as 'balance' from
      journal_entries GROUP BY user_id,account_name HAVING user_id={})x
      ON accounts.user_id=x.user_id AND accounts.account_name=x.account_name;""".format(cur_user))
    all_results=cursor.fetchall()

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