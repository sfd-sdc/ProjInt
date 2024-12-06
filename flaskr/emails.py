import resend
import os
from dotenv import load_dotenv

def sendEmail(data):

    load_dotenv()
    resend.api_key = os.getenv('RESEND_API_KEY')

    f: bytes = open(
        #Change path acording to your os. This is for linux
        os.path.join(os.path.dirname(__file__), "../files/movimentos.pdf"), "rb"
    ).read()

    attachment: resend.Attachment = {"content": list(f), "filename": "movimentos.pdf"}

    params: resend.Emails.SendParams = {
        "from": "pedro.santo@pedrosanto.pt",
        "to":data['to'],
        "subject": "SDC Bank",
        "html": "<strong>SDC Bank</strong>\n \
      <p>Aqui está o estrato das suas contas</p> \
      <p>Obrigado por usar o SDC Bank</p>",
        "attachments": [attachment],
    }

    email: resend.Email = resend.Emails.send(params)
    return email
