package main

import (
    "encoding/json"
    "fmt"
    "net/http"
	"os"

    "github.com/resend/resend-go/v2"
)

// Struct to hold the email request
type EmailRequest struct {
    To      string `json:"to"`
    Subject string `json:"subject"`
    Html    string `json:"html"`
}

// Function to send an email
func sendEmail(to, subject, html string) (string, error) {
	pwd, _ := os.Getwd()
	f, err := os.ReadFile(pwd + "/files/movimentos.pdf")

	if err != nil {
		panic(err)
	}

    apiKey := "re_9cJvnsx4_NYH1LWM7VW4hgdWGcpzYB5cg"

    client := resend.NewClient(apiKey)

	attachment := &resend.Attachment{
		Content: f,
		Filename: "movimentos.pdf",
	}

    params := &resend.SendEmailRequest{
        From:    "Pedro <pedro.santo@pedrosanto.pt>",
        To:      []string{to}, Html:    html,
        Subject: subject,
        ReplyTo: "replyto@example.com",
		Attachments: []*resend.Attachment{attachment},
    }

    sent, err := client.Emails.Send(params)
    if err != nil {
        return "", err
    }
    return sent.Id, nil
}

// HTTP handler to call sendEmail function
func emailHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method == http.MethodPost {
        var req EmailRequest
        if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
            http.Error(w, err.Error(), http.StatusBadRequest)
            return
        }

        id, err := sendEmail(req.To, req.Subject, req.Html)
        if err != nil {
            http.Error(w, err.Error(), http.StatusInternalServerError)
            return
        }

        response := map[string]string{"id": id}
        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(response)
    } else {
        http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
    }
}

func main() {
    http.HandleFunc("/send-email", emailHandler)
    fmt.Println("Go server is running on port 8080")
    http.ListenAndServe(":8080", nil)
}

