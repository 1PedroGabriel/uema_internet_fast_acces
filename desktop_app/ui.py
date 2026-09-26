import tkinter as tk
from tkinter import messagebox
import security

def ask_credentials():
    """
    Abre uma interface gráfica simples para o usuário registrar
    suas credenciais pela primeira vez.
    """
    root = tk.Tk()
    root.title("Acesso UEMA Wi-Fi")
    root.geometry("350x250")
    root.eval('tk::PlaceWindow . center')
    root.configure(padx=20, pady=20)

    tk.Label(root, text="Configure seu acesso UEMA", font=("Arial", 12, "bold")).pack(pady=(0, 10))
    tk.Label(root, text="Suas credenciais serão salvas no\nCofre de Senhas do seu Sistema Operacional.\n(Nada é salvo em texto plano)").pack(pady=(0, 15))

    tk.Label(root, text="Usuário/Matrícula:").pack()
    user_entry = tk.Entry(root, width=30)
    user_entry.pack()

    tk.Label(root, text="Senha:").pack()
    pass_entry = tk.Entry(root, show="*", width=30)
    pass_entry.pack()

    def save():
        u = user_entry.get().strip()
        p = pass_entry.get().strip()
        if u and p:
            security.save_credentials(u, p)
            messagebox.showinfo("Sucesso", "Credenciais criptografadas e salvas com segurança no sistema!")
            root.destroy()
        else:
            messagebox.showwarning("Erro", "Por favor, preencha ambos os campos.")

    tk.Button(root, text="Salvar Credenciais", command=save, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(pady=20)
    
    # Traz a janela para frente
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    
    root.mainloop()

if __name__ == "__main__":
    ask_credentials()
