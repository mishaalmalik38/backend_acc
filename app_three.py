from input_models import CreateAccount,AddCustomer,AddVendor,AddInventory,PurchaseInv,AddInvoice,ReturnInv,BadDebts,SingleJournal,CustomerPayment,CashReturnInv
from sqlalchemy.orm import sessionmaker,session,declarative_base
from sqlalchemy import create_engine,func,distinct,text,and_,or_,select
import datetime
from datetime import timedelta
from fastapi import FastAPI,Request,HTTPException,Depends,Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
from jose import JWTError,jwt
from passlib.context import CryptContext
from models_two import Users,accounts,journal_entries,inventories,customers,vendors,inv_purchases,inv_sales,closing_process
from dotenv import load_dotenv
import os

app=FastAPI()

db_url=os.getenv("DATABASE_URL")
secret_key=os.getenv("SECRET_KEY")
eng=create_engine(db_url)
Sessionlocal=sessionmaker(bind=eng)
#Base=declarative_base()

app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173"]
                   ,allow_methods=["*"],allow_credentials=True,
                   allow_headers=["*"])

pwd_context=CryptContext(schemes=["bcrypt"],deprecated='auto')
oauth2_scheme=OAuth2PasswordBearer(tokenUrl='login')

def get_db_two():
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
      tok=jwt.encode(data,secret_key,algorithm='HS256')
      return tok

def current_user(req:Request):
      data=req.headers.get('Authorization')
      if data is None:
            raise HTTPException(status_code=400,detail='invalid credentials')
      tok=data.split(" ")[1]
      try:
            get_dict=jwt.decode(tok,secret_key,algorithms=["HS256"])
            return get_dict["user"]
      except JWTError:
            raise HTTPException(status_code=400,detail='Token got expired')

def current_user_two(tok=Depends(oauth2_scheme)):
      try:
            get_dict=jwt.decode(tok,secret_key,algorithms=['HS256'])
            return get_dict['user']
      except JWTError:
            raise HTTPException(status_code=401,
                                detail='Expired or invalid credentials')
      
def add_journal_entry(db,debit_acc,credit_acc,amt,cur_user,journal_no=None):
      if journal_no == None:
            journal_no=db.query(func.max(journal_entries.id)).filter_by(user_id=cur_user).scalar()
            if journal_no == None:
                  journal_no=1
      db.add(journal_entries(id=journal_no+1,account_name=debit_acc,debit_amt=amt,credit_amt=0,user_id=cur_user))
      db.add(journal_entries(id=journal_no+1,account_name=credit_acc,debit_amt=0,credit_amt=amt,user_id=cur_user))
      return journal_no

def remaining_amount(info):
      return_amt=(info.sales_price / info.qty) * info.return_qty
      rem=info.sales_price-info.amount_paid-info.bad_debts_amount-return_amt
      return rem

@app.get("/main")
async def main_page():
    return {"Message":"LEDGER LOOPS"}

@app.post("/adduser")
async def add_user(username=Form(...),password=Form(...),db=Depends(get_db_two)):
      data={'username':username,'password':password}
      res=db.query(Users).filter_by(user_name=data['username']).first()
      if not res == None:
            raise HTTPException(status_code=400,detail='User already exists')
      hashed_pass=hash_password(data['password'])
      add_user=Users(user_name=data['username'],user_pass=hashed_pass)
      db.add(add_user)
      db.commit()
      user_info=db.query(Users).filter_by(user_name=username).first()
      cogs_acc=accounts(user_id=user_info.id,account_name='COGS',account_nature='debit',
                         account_type='income statement',account_subtype='expenses',account_subtypetwo='cost of goods sold')
      bad_debts_acc=accounts(user_id=user_info.id,account_name='bad debts',account_nature='debit',
                         account_type='income statement',account_subtype='expenses',account_subtypetwo='bad debts')
      sales_acc=accounts(user_id=user_info.id,account_name='sales',account_nature='credit',
                         account_type='income statement',account_subtype='incomes',account_subtypetwo='sales')
      cash_acc=accounts(user_id=user_info.id,account_name='cash',account_nature='debit',
                        account_type='assets',account_subtype='current assets',account_subtypetwo='cash')
      p_l_c=accounts(user_id=username,account_name='p_l_balance',account_type='liabilities',
                     account_subtype='reserves&surplus',account_subtypetwo='p_and_l_balance')
      db.add(cash_acc)
      db.add(bad_debts_acc)
      db.add(sales_acc)
      db.add(cogs_acc)
      db.add(p_l_c)
      db.commit()
      tok=issue_token({'user':username})
      return tok

@app.get('/tokencheck')
async def token_check(req:Request):
      get_token=req.headers.get('Authorization')
      tok=get_token.split(" ")[1]
      try:
            jwt.decode(tok,secret_key,algorithms=['HS256'])
      except Exception:
            raise HTTPException(status_code=401,detail='Invalid credentials')
      return {'msg':'ok'}

@app.post("/login")
async def login_user(username=Form(...),password=Form(...),db=Depends(get_db_two)):
      data={'username':username,'password':password}
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
async def return_customers(db=Depends(get_db_two),cur_user=Depends(current_user)):
      res=db.query(customers.customer_name).filter_by(user_id=cur_user).all()
      fil_customers=[]
      for i in res:
            cur_dict={'customer_name':i.customer_name}
            fil_customers.append(cur_dict)
      return fil_customers

@app.get("/getvendors")
async def return_vendors(db=Depends(get_db_two),cur_user=Depends(current_user)):
      res=db.query(vendors).filter_by(user_id=cur_user).all()
      vendor_list=[]
      for i in res:
           vendor_list.append({'vendor_name':i.vendor_name})

      return vendor_list

@app.get("/getinventories")
async def return_inv(db=Depends(get_db_two),cur_user=Depends(current_user)):
      res=db.query(inventories.inv_name).filter_by(user_id=cur_user).all()
      invs=[]
      for i in res:
            invs.append({'inv_name':i.inv_name})
      return invs

@app.get('/currentassets')
async def current_assets(db=Depends(get_db_two),cur_user=Depends(current_user)):
      res=db.query(accounts).filter_by(account_subtype='current assets',user_id=cur_user).all()
      ca=[]
      for i in res:
            cur_dict={'account_name':i.account_name,'account_nature':i.account_nature,
             'account_type':i.account_type,'account_subtype':i.account_subtype,
             'account_subtypetwo':i.account_subtypetwo,'amount':i.amount}
            ca.append(cur_dict)

      return ca

@app.get('/payaccounts')
async def pay_accounts(req:Request,db=Depends(get_db_two),cur_user=Depends(current_user_two)):
      stmt=select(accounts.user_id,accounts.account_name,accounts.account_subtypetwo).where(and_(accounts.user_id == cur_user),
                                     or_(accounts.account_subtypetwo == 'accounts receivable',accounts.account_subtypetwo == 'bank'))
      res=db.execute(stmt).all()
      results=[]
      for userid,acc,typ in res:
            results.append({'user_id':userid,'account_name':acc,'account_subtypetwo':typ})
      return results

@app.get("/invpurchases")
async def purchases_inv(db=Depends(get_db_two),cur_user=Depends(current_user)):
      res=db.query(inv_purchases.user_id,inv_purchases.inv_name,func.sum(inv_purchases.qty)).filter_by(user_id=cur_user).group_by(inv_purchases.user_id,inv_purchases.inv_name)
      inv_details=[]
      for user_id,inv_name,qty in res:
            inv_details.append({'user_id':user_id,'inv_name':inv_name,'qty':qty})
      return inv_details

@app.get("/allinvoices/")
async def all_invoices(db=Depends(get_db_two),invoice_id=None,cur_user=Depends(current_user)):
      if invoice_id == None:
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
            res=db.query(inv_sales).filter_by(user_id=cur_user,id=invoice_id).first()
            return {'id':res.id,'date_of_sale':res.date_of_sale,
                                  'customer_name':res.customer_name,'journal_id':res.journal_id,
                                  'amount_paid':res.amount_paid,'cur_status':res.cur_status,
                                  'inv_name':res.inv_name,'qty':res.qty,'sales_price':res.sales_price,
                                  'cost_of_goods_sold':res.cost_of_goods_sold,'bad_debts_amount':res.bad_debts_amount,
                                  'return_qty':res.return_qty,'user_id':res.user_id}
      

@app.post("/addcustomer")
async def add_customer(req:AddCustomer,db=Depends(get_db_two),cur_user=Depends(current_user)):
      data=req.model_dump()
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
async def add_vendor(req:AddVendor,db=Depends(get_db_two),cur_user=Depends(current_user)):
      data=req.model_dump()

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
async def add_inventory(req:AddInventory,db=Depends(get_db_two),cur_user=Depends(current_user)):
      data=req.model_dump()
      res=db.query(inventories).filter_by(user_id=cur_user).all()
      for i in res:
            if i.inv_name == data['inv_name']:
                  raise HTTPException(status_code=400,detail='inv exists')
     
      res=db.query(accounts).filter_by(user_id=cur_user).all()
      av_accs=[i.account_name for i in res]
      if data['ledger_name'] in av_accs:
            raise HTTPException(status_code=400,detail='ledger name exists')
      if data['ledger_name'] == None:
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
async def purchase_inv(req:PurchaseInv,db=Depends(get_db_two),cur_user=Depends(current_user)):
      data=req.model_dump()
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
async def add_invoice(req:AddInvoice,db=Depends(get_db_two),cur_user=Depends(current_user)):
      data=req.model_dump()
      res=db.query(inv_purchases).filter_by(user_id=cur_user,inv_name=data['inv_name']).order_by(inv_purchases.date_of_purchase).all()
      for_sale=int(data['qty'])

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
                                   to_del=db.query(inv_purchases).filter_by(id=ids[j],user_id=cur_user,inv_name=data['inv_name']).first()
                                   db.delete(to_del)
                                    
                        if av_inv == 0:
                               to_del=db.query(inv_purchases).filter_by(user_id=cur_user,id=ids[i],inv_name=data['inv_name']).first()
                               db.delete(to_del)
                               
                        else:
                              to_update=db.query(inv_purchases).filter_by(user_id=cur_user,id=ids[i],inv_name=data['inv_name']).first()
                              to_update.qty=av_inv
                            
                        a=add_journal_entry(db,data['customer_name'],'sales',data['selling_price'],cur_user)
                        inv=db.query(inventories.account_name).filter_by(user_id=cur_user,inv_name=data['inv_name']).scalar()
                        add_journal_entry(db,"COGS",inv,total_price,cur_user,journal_no=a)
                       
                        paid_status='not paid'
            
                        sale_info=inv_sales(customer_name=data['customer_name'],
                                    journal_id=a,amount_paid=0,cur_status=paid_status,
                                    inv_name=data['inv_name'],qty=data['qty'],sales_price=data['selling_price'],
                                    cost_of_goods_sold=total_price,bad_debts_amount=0,return_qty=0,
                                    user_id=cur_user)
                        db.add(sale_info)
      
                        db.commit()
                        return {'message':'success','cogs':total_price}
                  
@app.post("/return_inv")
async def return_inventory(req:ReturnInv,db=Depends(get_db_two)
                           ,inv_id=None,cur_user=Depends(current_user),typ=None):
      
      if inv_id == None:
            raise HTTPException(status_code=400,detail='Provide inv id')
      data=req.model_dump()
     
      res=db.query(inv_sales).filter_by(user_id=cur_user,id=inv_id).first()
      if res == None:
            raise HTTPException(status_code=400,detail='inv_id does not exists')
    
      avgp=res.sales_price / res.qty
      return_cash_qty=res.amount_paid / avgp
      if data['return_qty'] > (res.qty - res.return_qty - return_cash_qty):
            raise HTTPException(status_code=400,detail='quantity sent by you is greater than the actual inventory available')
     
      r=int(res.return_qty)
      r=r + int(data['return_qty'])
      
      res.return_qty=r

      c_p=(res.cost_of_goods_sold / res.qty) * int(data['return_qty'])
      s_p=(res.sales_price / res.qty) * int(data['return_qty'])
      acc_name=db.query(inv_sales.inv_name).filter_by(user_id=cur_user,id=inv_id).scalar()
      j_n=add_journal_entry(db,acc_name,'COGS',c_p,cur_user)
      add_journal_entry(db,'sales',res.customer_name,s_p,cur_user,journal_no=j_n)
      
      ret_data=inv_purchases()
      ret_data.user_id=cur_user
      ret_data.inv_name=res.inv_name
      ret_data.qty=int(data['return_qty'])
      ret_data.price=int(res.cost_of_goods_sold) / int(res.qty)
      db.add(ret_data)
      db.commit()
      return {'Message':'ok'}

@app.post('/cashreturninv/')
async def return_cash_inventory(req:CashReturnInv,inv_id=None,db=Depends(get_db_two),cur_user=Depends(current_user_two)):
      data=req.model_dump()
      if inv_id == None:
            raise HTTPException(status_code=400,detail='Provide a invoice id')
      
      res=db.query(inv_sales).filter_by(user_id=cur_user,id=inv_id).first()
      if res == None:
            raise HTTPException(status_code=400,detail='Invoice not found')

      if res.user_id != cur_user:
            raise HTTPException(status_code=400,detail='You are not authorized')

      average_cost = res.cost_of_goods_sold / res.qty
      cp=average_cost * int(data['return_qty'])
      average_sales = res.sales_price / res.qty
      sp=average_sales * int(data['return_qty'])
      add_journal_entry(db,res.inv_name,'COGS',cp,cur_user)
      add_journal_entry(db,'sales',data['payment_acc'],sp,cur_user)
      res.return_qty += int(data['return_qty'])
      return_amt = average_sales * data['return_qty']
      res.amount_paid = res.amount_paid - return_amt
      res.return_amt_paid += return_amt

      inv_return=inv_purchases(user_id=cur_user,inv_name=res.inv_name,qty=int(data['return_qty']),price=average_cost)
      db.add(inv_return)
      db.commit()

      return {"Message":"ok","return_amount":return_amt}

@app.post("/baddebts/")
async def bad_debts(req:BadDebts,db=Depends(get_db_two),inv_id=None,cur_user=Depends(current_user)):
      if inv_id == None:
            raise HTTPException(status_code=400,details='Provide an invoice id'
                                )
      data=req.model_dump()
      res=db.query(inv_sales).filter_by(user_id=cur_user,id=inv_id).first()
      if res == None:
            raise HTTPException(status_code=400,detail='Enter a existing invoice')
      
      rem=remaining_amount(res)
      if data['bad_debts'] > rem:
            raise HTTPException(status_code=400,detail='bad debts > remaining amount')
      
      res.bad_debts_amount += int(data['bad_debts'])

      add_journal_entry(db,'bad debts',res.customer_name,data['bad_debts'],cur_user)
      db.commit()
      return {'Message':'ok'}

@app.post("/createaccount")
async def create_account(req:CreateAccount,db=Depends(get_db_two),cur_user=Depends(current_user)):
    data=req.model_dump()
    res=db.query(accounts.account_name).filter_by(user_id=cur_user,account_name=data['account_name']).scalar()
    if res != None:
        raise HTTPException(status_code=400,detail='Account already exists')
    
    acc_nature=None
    if data['account_type'] == 'assets' or data['account_subtype'] == 'expenses':
          acc_nature='debit'
    else:
          acc_nature='credit'
    db.add(accounts(account_name=data['account_name'],account_nature=acc_nature,
             account_type=data['account_type'],account_subtype=data['account_subtype'],
             account_subtypetwo=data['account_subtypetwo'],user_id=cur_user))
    db.commit()
    return {"Message":"Account created"}

@app.get('/viewledgers')
async def view_ledgers(db=Depends(get_db_two),cur_user=Depends(current_user)):
    a=db.query(accounts).filter_by(user_id=cur_user).all()
    accs=[]
    for i in a:
          accs.append({'account_name':i.account_name})
    #return accounts
    return accs

@app.get("/viewbalances")
async def view_balances(db=Depends(get_db_two),cur_user=Depends(current_user)):
    res=db.execute(text("""SELECT * from (
      SELECT user_id,account_name,SUM(debit_amt-credit_amt) as balance from journal_entries
      GROUP BY user_id,account_name)x
      WHERE user_id=:id_user"""),{'id_user':cur_user})
    results=[]
    for i in res:
          results.append({'user_id':i.user_id,'account_name':i.account_name,
                      'balance':i.balance})
    return results

@app.post('/singlejournal')
async def add_journal_single(req:SingleJournal,db=Depends(get_db_two),typ=None,cur_user=Depends(current_user_two)):
    data=req.model_dump()
    accs=db.query(accounts).filter_by(user_id=cur_user).all()
    av_accs=[i.account_name for i in accs]
    if data['debit_account'] or data['credit_account'] not in av_accs:
          return HTTPException(status_code=401,detail='The provided accounts does not exists')
    add_journal_entry(db,data['debit_account'],data['credit_account'],data['amount'],cur_user)
   
@app.post('/customer_payment')
async def customer_payment(req:CustomerPayment,cur_user=Depends(current_user_two),db=Depends(get_db_two)):
      data=req.model_dump()
      
      sales=db.query(inv_sales).filter_by(user_id=cur_user,id=data['inv_id']).first()
      avg_price=sales.sales_price / sales.qty
      sales_return_amt=avg_price * sales.return_qty
      rem_amt=sales.sales_price -sales.amount_paid - sales.bad_debts_amount - sales_return_amt
      
      if sales.sales_price < data['amount_paid'] or rem_amt < data['amount_paid']:
            raise HTTPException(status_code=400,detail='amount paid is higher')
      if sales.cur_status == 'paid':
            raise HTTPException(status_code=400,detail='invoice already paid')
      
      add_journal_entry(db,data['payment_acc'],data['customer_name'],data['amount_paid'],cur_user)
      sales.amount_paid=sales.amount_paid + int(data['amount_paid'])
      sales_r=(sales.sales_price / sales.qty) * sales.return_qty
      #return {"fk":sales_r,"bd":sales.bad_debts_amount}
      
      status=None
      if (sales.amount_paid + sales.bad_debts_amount + sales_r) == sales.sales_price:
            sales.cur_status='finished'
      else:
            sales.cur_status='pending'

      db.commit()
      return {"msg":"added payment",status:sales.cur_status}

@app.get('/viewjournals')
async def view_journals(db=Depends(get_db_two),cur_user=Depends(current_user)):
    #cursor=db.cursor(dictionary=True)
    j_e=db.execute(text("""SELECT * from (
    SELECT x.id,x.date_of_entry,x.user_id,x.account_name AS debited,x.debit_amt as debit_amt,
    y.account_name as credited,y.credit_amt as credit_amt
    from journal_entries x,journal_entries y
    WHERE x.user_id=y.user_id AND x.id=y.id AND x.account_name != y.account_name
    AND x.debit_amt=y.credit_amt AND x.debit_amt != 0)z
    WHERE user_id=:id_user ;"""),{'id_user':cur_user})

    ret_accs=[]
    
    for i in j_e:
          ret_accs.append({
        'id':i.id,'date_of_entry':i.date_of_entry,'debited':i.debited,
        'debit_amt':i.debit_amt,'credited':i.credited,'credit_amt':i.credit_amt})
    
    return ret_accs

@app.get("/balancesheet")
async def return_balance_sheet(db=Depends(get_db_two),cur_user=Depends(current_user)):
    res=db.execute(text("""SELECT x.user_id,x.account_name,x.account_nature,
                        x.account_type,x.account_subtype,
                        x.account_subtypetwo,COALESCE(balance,0) as balance
                        from accounts x LEFT JOIN 
                        (SELECT user_id,account_name,SUM(debit_amt-credit_amt) AS balance
                        FROM journal_entries GROUP BY user_id,account_name HAVING user_id=:id_user) y
                        ON x.user_id=y.user_id AND x.account_name=y.account_name;
                        """),{'id_user':cur_user})
    accs=[]
    for i in res:
          accs.append({'user_id':i.user_id,'account_name':i.account_name,
                       'account_nature':i.account_nature,
                       'account_type':i.account_type,'account_subtype':i.account_subtype,
                       'account_subtypetwo':i.account_subtypetwo,'balance':i.balance})
    return accs

@app.get("/balancesheet_two")
async def al_balance_sheet(db=Depends(get_db_two),cur_user=Depends(current_user),fil_one=None,fil_two=None):
    res=db.execute(text("""SELECT x.user_id,x.account_name,x.account_nature,
                  x.account_type,account_subtype,account_subtypetwo,
                  z.bal as balance
                  from accounts x INNER JOIN (
                  SELECT user_id,account_name,SUM(debit_amt)-SUM(credit_amt) AS bal
                  FROM journal_entries
                  GROUP BY user_id,account_name HAVING user_id=:id_user)z
                  ON x.user_id=z.user_id AND x.account_name=z.account_name;"""),{'id_user':cur_user})

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

@app.get('/incomestatement/')
def return_income_statement(db=Depends(get_db_two),cur_user=Depends(current_user_two),begin=None,
                            end=None):
      first=None
      last=None
      if begin == None and end == None:
            first='2000-01-01'
            last='NOW()'
      else:
            if begin and end:
                  first=begin
                  last=end
            if begin:
                  first=begin
            if end:
                  last=end
                  
      statement=db.execute(text("""with table_one as (
      SELECT auto_id,id,date_of_entry,user_id,account_name,debit_amt,credit_amt
      from journal_entries
      WHERE user_id=:id_user AND (date_of_entry BETWEEN :begin AND :end )
      AND id NOT IN(
      SELECT id from journal_entries x
      WHERE x.user_id=:id_user AND account_name = 'p_l_balance'))
      
      SELECT x.user_id,x.account_name,SUM(debit_amt)-SUM(credit_amt) AS bal,
      accounts.account_type,accounts.account_subtype,accounts.account_subtypetwo
      from table_one x
      INNER JOIN accounts ON x.user_id=accounts.user_id AND 
      x.account_name=accounts.account_name and accounts.account_type='income statement'
      GROUP BY x.user_id,x.account_name,accounts.account_type,accounts.account_subtype,
      accounts.account_subtypetwo"""),{'id_user':cur_user,'begin':first,'end':last})

      accs={'incomes':{},'expenses':{}}
      for user_id,account_name,balance,account_type,account_subtype,account_subtypetwo in statement:
            if account_subtype in accs:
                  accs[account_subtype][account_subtypetwo] = balance
      return accs

@app.get("/closingprocess")
async def close_income_expense_accounts(request:Request,db=Depends(get_db_two),
                                  cur_user=Depends(current_user_two)):
                 
      bal_two=db.query(journal_entries.user_id,journal_entries.account_name,func.sum(journal_entries.debit_amt),
                              func.sum(journal_entries.credit_amt)).join(accounts,
                                                and_(journal_entries.user_id == accounts.user_id,
                                                      journal_entries.account_name == accounts.account_name,
                                                      accounts.account_type == 'income statement')).group_by(journal_entries.user_id,journal_entries.account_name).all()
      to_close={'expenses':{},'incomes':{},'bal':0}

      for u,a,b,c in bal_two:
            if u == cur_user:
                  bal=int(b-c)
                  if bal > 0:
                        to_close['expenses'][a]=bal
                  else:
                        to_close['incomes'][a]=bal
            
                  to_close['bal'] += bal

      #closing process
      for i in to_close['expenses']:
            acc_val=to_close['expenses'][i]
            add_journal_entry(db,'p_l_balance',i,acc_val,cur_user)

      for i in to_close['incomes']:
            acc_value=to_close['incomes'][i] * -1
            add_journal_entry(db,i,'p_l_balance',acc_value,cur_user)

      db.commit()
      return {"msg":"ok"}

@app.get('/bye')
async def last_route():
      return {"msg":"bye"}

