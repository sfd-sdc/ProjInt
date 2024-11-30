from supabase_client import supabase
from fpdf import FPDF

def generatePDF(iban, id):
    userIban = int(iban)
    f = open("files/movimentos.txt", "w")

    f.write("Movimentos\n")
    f.write("Conta Origem - Conta Destino/Entidade - Valor - Data\n")
    f.write("------------------------------------------------------------------------------------\n")

    f.close()

    data = supabase.table('payments_history') \
        .select('users(user_fullname), entitys(name), amount, date') \
        .eq('user_id', id) \
        .execute()

    f = open("files/movimentos.txt", "a")

    for i in range(len(data.data[0])):
        fDataPayments = {'name': data.data[i]['users']['user_fullname'],
             'entity': data.data[i]['entitys']['name'],
             'paymentAmount': data.data[i]['amount'],
             'paymentDate': data.data[i]['date']}
        for key, value in fDataPayments.items():
            f.write(f"{value}   ")
        f.write("\n")

    data = supabase.table('transfers_history') \
        .select('users(user_fullname), receiver_acc_id(user_id(user_fullname)), amount, date') \
        .eq('user_bank_acc(acc_iban)', userIban) \
        .execute()

    for i in range(len(data.data[0]) - 1):
        fDataTransfers = {'sender_name': data.data[i]['users']['user_fullname'],
                 'receiver_name': data.data[i]['receiver_acc_id']['user_id']['user_fullname'],
                 'transferAmount': data.data[i]['amount'],
                 'transferDate': data.data[i]['date']}
        for key, value in fDataTransfers.items():
            f.write(f"{value}   ")
        f.write("\n")


    f.close()

    #TODO: Need to change this 
    txt_file = "files/movimentos.txt"
    pdf_file = "files/movimentos.pdf"

# Criação do objeto PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

# Leitura do arquivo de texto
    with open(txt_file, 'r', encoding='utf-8') as file:
        for line in file:
            pdf.multi_cell(0, 10, line)

# Salvando o arquivo PDF
    pdf.output(pdf_file)
    return(f"Arquivo PDF '{pdf_file}' criado com sucesso.")
