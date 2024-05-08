from flask import Flask,redirect,request,render_template,url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from datetime import datetime
import csv
import os


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///bank.db'
app.config["SQLALCHEMY_TRACK_MODIFICATION"] = False
db = SQLAlchemy(app)

class Customer(db.Model):
    
    id = db.Column(db.Integer,primary_key = True,autoincrement = True)
    name = db.Column(db.String(),nullable = True)
    account_number = db.Column(db.String(),unique = True,nullable = True)
    current_balance = db.Column(db.Float(),default=0.0)
    
class History(db.Model):
    s_no = db.Column(db.Integer,primary_key = True,autoincrement = True)
    account_number = db.Column(db.String(),nullable = True)
    amount = db.Column(db.Float(),nullable=True)
    transaction = db.Column(db.String())
    timestamp = db.Column(db.DateTime,default = datetime.utcnow)
    
@app.before_request
def create_table():
    db.create_all()
    

@app.route('/')
def home():
    return render_template("home.html")


@app.route('/add',methods=["GET","POST"])
def add_user():
    if request.method == "POST":
        name = request.form['name']
        account_number = request.form['account_number']
        current_balance = float(request.form['current_balance'])
        
        db.session.add(Customer(name=name, account_number=account_number,current_balance=current_balance))
        db.session.commit()
        return redirect(url_for('add_user',message = "Account Created Successfully"))

    return render_template('add_user.html',message = request.args.get('message'))

@app.route('/deposit',methods=["GET","POST"])
def deposit():
    if request.method == "POST":
        account_number = request.form['account_number']
        amount = float(request.form['amount'])
        
        user = Customer.query.filter_by(account_number = account_number).first()
        if not user:
            return render_template('deposit.html', error = "User not Fount")
        
        user.current_balance += amount
        db.session.add(History(account_number = account_number,amount=amount,transaction='Deposit'))
        db.session.commit()
        
        return render_template('deposit.html',message = 'Deposit Successful',current_balance = user.current_balance)
    return render_template('deposit.html')

@app.route('/withdraw',methods=["GET","POST"])
def withdraw():
    if request.method == 'POST': 
        account_number = request.form["account_number"]
        amount =float(request.form['amount'])
        
        user = Customer.query.filter_by(account_number=account_number).first()
        
        if not user:
            return render_template("withdraw.html",error="user not found")
        if user.current_balance < amount:
            return render_template("withdraw.html",error="Insufficient Balance")
        
        user.current_balance -= amount
        db.session.add(History(account_number=account_number,amount=amount ,transaction = "Withdrawl"))
        db.session.commit()
        
        
        return render_template("withdraw.html",message="Withdraw Successfully",current_balance=user.current_balance)
    
    return render_template("withdraw.html")

@app.route('/mini_statement/<int:account_number>')
def mini_statement(account_number):
    # user = Customer.query.filter_by(account_number = account_number).first()
    # if not user:
    #     return render_template('ministatement.html', error = "user not found")
    # transactions = History.query.filter_by(account_number = account_number).order_by(desc(History.timestamp)).all()

      # user = (db.session.query(Customer)
    #         .options(joinedload(Customer.transaction))
    #         .filter(Customer.account_number == account_number)
    #         .first() 
    #         )
       
    # transactions = user.transactions.order_by(desc(History.timestamp)).all()      
    

    query = (db.session.query(Customer,History)
             .join(History, Customer.account_number == History.account_number)
             .filter(Customer.account_number == account_number)
             .order_by(desc(History.timestamp)).all())
  
    user,transactions = query[0]

    csv_data = [['Amount', 'TransactionType', 'Timestamp']]
   
    csv_file_path = f'statement_{account_number}.csv'
    with open(csv_file_path, 'w', newline = '',encoding = 'utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerows(csv_data)
        csv_writer.writerow([transactions.amount, transactions.transaction, transactions.timestamp])
        

    return render_template('ministatement.html',user_account_number = user.account_number, user_balance = user.current_balance, transaction_amount = transactions.amount,transaction_type= transactions.transaction,transaction_timestamp = transactions.timestamp,csv_file_path=csv_file_path)
    
if __name__ == "__main__":
    app.run(debug=True)



