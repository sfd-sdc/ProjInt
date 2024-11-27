from flask import request
def getPaymentData():
    paymentData = {
        'entity': request.form['entity'],
        'amount': request.form['amount']
    }
    return paymentData

def getTransferData():
    transferData = {
        'iban': request.form['iban'],
        'amount': request.form['amount']
    }
    return transferData