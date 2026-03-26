def analyze_data(data):
    # Perform analysis on the provided data
    pass


def build_html_email(subject, body):
    # Build an HTML email
    return f"<html><body><h1>{subject}</h1><p>{body}</p></body></html>"


def send_gmail(to, subject, body):
    # Send an email via Gmail
    print(f"Sending email to {to} with subject '{subject}'")


if __name__ == '__main__':
    # Main execution starts here
    data = []
    analyze_data(data)
    email_body = build_html_email('Subject', 'This is the body of the email')
    send_gmail('test@example.com', 'Subject', email_body)