from pydantic import BaseModel
from typing import Optional

class Adduser(BaseModel):
    username:str
    password:str

class AddCustomer(BaseModel):
    customername:str
    gmail:str | None = ''

class AddVendor(BaseModel):
    vendorname:str
    gmail:str | None = ''

class CreateAccount(BaseModel):
    account_name:str
    account_type:str
    account_subtype:str
    account_subtypetwo:str

class AddInventory(BaseModel):
    inv_name:str
    ledger_name:str | None 

class PurchaseInv(BaseModel):
    inv_name:str
    qty:int
    price:int
    vendor_name:str

class AddInvoice(BaseModel):
    inv_name:str
    qty:int
    customer_name:str
    selling_price:int

class ReturnInv(BaseModel):
    return_qty:int
    
class CashReturnInv(BaseModel):
    return_qty:int
    payment_acc:str

class BadDebts(BaseModel):
    bad_debts:int

class SingleJournal(BaseModel):
    debit_account:str
    credit_account:str
    amount:int

class CustomerPayment(BaseModel):
    customer_name:str
    payment_acc:str
    inv_id:int
    amount_paid:int

class closingdata(BaseModel):
    journal_id:int

