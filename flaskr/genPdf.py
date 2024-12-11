from supabase_client import supabase
from fpdf import FPDF

def generatePDF(iban):
    userIban = int(iban)
    f = open("files/movimentos.txt", "w")

    f.write("Movimentos\n")
    f.write("Origem/Destino - Valor - Data\n")
    f.write("------------------------------------------------------------------------------------\n")

    id = (supabase.table('user_bank_acc') 
          .select('id')
          .eq('acc_iban', iban)
          .execute()
          )

    data = supabase.table('payments_history') \
        .select('entitys(name), amount, date') \
        .eq('user_bank_acc_id', id.data[0]['id']) \
        .execute()

    for payment in data.data:
        payment_details = {
            "Entidade": payment['entitys']['name'],
            "Valor": payment['amount'],
            "Data": payment['date']
        }
        f.write(f"{payment_details['Entidade']}     -{payment_details['Valor']}EUR     {payment_details['Data']}\n")

    sender_data = supabase.table('transfers_history') \
        .select('receiver_acc_id(acc_iban), amount, date') \
        .eq('sender_acc_id', id.data[0]['id']) \
        .execute()

    for transfer in sender_data.data:
        transfer_details = {
            "Nome": transfer['receiver_acc_id']['acc_iban'],
            "Valor":transfer['amount'],
            "Data": transfer['date']
        }
        f.write(f"{transfer_details['Nome']}     -{transfer_details['Valor']}EUR     {transfer_details['Data']}\n")

    receiver_data = supabase.table('transfers_history') \
        .select('receiver_acc_id(acc_iban), amount, date') \
        .eq('receiver_acc_id', id.data[0]['id']) \
        .execute()

    for transfer in receiver_data.data:
        transfer_details = {
            "Nome": transfer['receiver_acc_id']['acc_iban'],
            "Valor":transfer['amount'],
            "Data": transfer['date']
        }
        f.write(f"{transfer_details['Nome']}     +{transfer_details['Valor']}EUR     {transfer_details['Data']}\n")

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
