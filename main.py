import os
import pickle
import tkinter as tk
from tkinter import messagebox, simpledialog
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://mail.google.com/"]

def authenticate(root, login_button, cleaner_button):
    creds = None
    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except Exception as e:
            print(f"Error al cargar token.json: {e}")
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())

    messagebox.showinfo("Autenticación", "Autenticación completada exitosamente.")
    
    # Ocultar botón de inicio de sesión y mostrar el de limpieza
    login_button.pack_forget()
    cleaner_button.pack(pady=10)

def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        with open("token.json", "rb") as token:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        messagebox.showerror("Error", "No se encontró una sesión activa. Inicia sesión primero.")
        return None
    return build("gmail", "v1", credentials=creds)

def list_and_delete_emails(query):
    service = get_gmail_service()
    if not service:
        return
    results = service.users().messages().list(userId="me", q=query).execute()
    messages = results.get("messages", [])
    if not messages:
        messagebox.showinfo("Información", "No se encontraron correos para eliminar.")
        return
    response = messagebox.askyesno("Confirmación", f"Se encontraron {len(messages)} correos. ¿Quieres eliminarlos?")
    if response:
        for msg in messages:
            service.users().messages().delete(userId="me", id=msg["id"]).execute()
        messagebox.showinfo("Éxito", "Correos eliminados exitosamente.")

def start_gui():
    root = tk.Tk()
    root.title("Gmail Email Cleaner")
    root.geometry("400x300")
    
    login_button = tk.Button(root, text="Iniciar Sesión en Google", command=lambda: authenticate(root, login_button, cleaner_button))
    login_button.pack(pady=10)
    
    cleaner_button = tk.Button(root, text="Abrir Limpiador de Correos", command=lambda: open_email_cleaner(root))
    cleaner_button.pack_forget()  # Inicialmente oculto
    
    root.mainloop()

def open_email_cleaner(root):
    root.destroy()
    new_root = tk.Tk()
    new_root.title("Gmail Email Cleaner")
    new_root.geometry("400x300")
    
    tk.Label(new_root, text="Selecciona los filtros a aplicar:").pack(pady=5)
    filters = {
        "Promociones": "category:promotions",
        "Social": "category:social",
        "Spam": "in:spam",
        "Correos antiguos (30 días)": "older_than:30d",
        "No leídos": "is:unread",
        "De remitente específico": "from:"
    }
    
    selected_filters = []
    
    def toggle_filter(filter_key, var):
        if var.get():
            if filter_key == "De remitente específico":
                sender = simpledialog.askstring("Remitente", "Introduce el correo del remitente:")
                if sender:
                    selected_filters.append(f"from:{sender}")
            else:
                selected_filters.append(filters[filter_key])
        else:
            selected_filters.remove(filters[filter_key])
    
    vars = {}
    for text in filters.keys():
        var = tk.BooleanVar()
        vars[text] = var
        tk.Checkbutton(new_root, text=text, variable=var, command=lambda t=text, v=var: toggle_filter(t, v)).pack(anchor="w")
    
    def search_emails():
        query = " ".join(selected_filters)
        if query:
            list_and_delete_emails(query)
        else:
            messagebox.showwarning("Advertencia", "Debes seleccionar al menos un filtro.")
    
    tk.Button(new_root, text="Buscar y Eliminar", command=search_emails).pack(pady=10)
    new_root.mainloop()

if __name__ == "__main__":
    start_gui()
